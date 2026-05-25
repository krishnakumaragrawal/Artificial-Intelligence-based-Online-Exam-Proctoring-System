from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from proctoring_platform.api.routes.proctoring import get_frame_analyzer
from proctoring_platform.app import create_app
from proctoring_platform.core.config import Settings
from proctoring_platform.services.detectors import DetectorEvent, FrameAnalysis


class FakeFrameAnalyzer:
    def analyze_image_bytes(self, image_bytes: bytes) -> FrameAnalysis:
        return FrameAnalysis(
            frame_id="fake-frame",
            events=[
                DetectorEvent(event_type="MOUTH_OPEN", confidence=0.78, payload={"status": "Mouth Open"}),
                DetectorEvent(event_type="PHONE_DETECTED", confidence=0.91, payload={"label": "cell phone"}),
            ],
            payload={
                "face_count": 1,
                "gaze": "center",
                "mouth": "Mouth Open",
                "head_pose": -1,
                "objects": [{"label": "cell phone", "confidence": 0.91}],
            },
        )


def _client(tmp_path: Path, **settings_overrides) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        jwt_secret="test-secret-with-at-least-thirty-two-bytes",
        evidence_dir=tmp_path / "evidence",
        seed_sample_data=True,
        bootstrap_admin_email="admin@example.com",
        bootstrap_admin_password="AdminPass123",
        **settings_overrides,
    )
    app = create_app(settings)
    app.dependency_overrides[get_frame_analyzer] = lambda: FakeFrameAnalyzer()
    return TestClient(app)


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_production_rejects_default_jwt_secret(tmp_path):
    settings = Settings(
        environment="production",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        bootstrap_admin_email="admin@example.com",
        bootstrap_admin_password="AdminPass123",
    )

    with pytest.raises(ValueError, match="JWT_SECRET"):
        create_app(settings)


def test_frame_upload_rejects_oversized_payload(tmp_path):
    with _client(tmp_path, max_frame_upload_bytes=8) as client:
        signup = client.post(
            "/auth/signup",
            json={"email": "student@example.com", "username": "student", "password": "Password123"},
        )
        student_token = signup.json()["access_token"]
        exam_id = client.get("/exams", headers=_auth_header(student_token)).json()[0]["id"]
        attempt = client.post(
            "/attempts",
            headers=_auth_header(student_token),
            json={"exam_id": exam_id, "client_fingerprint": "browser-test"},
        )
        session_id = attempt.json()["proctoring_session_id"]

        frame_analysis = client.post(
            f"/proctoring/sessions/{session_id}/analyze-frame",
            headers=_auth_header(student_token),
            files={"file": ("frame.jpg", b"too-large", "image/jpeg")},
        )

        assert frame_analysis.status_code == 413


def test_student_attempt_flow_records_answer_event_and_submission(tmp_path):
    with _client(tmp_path) as client:
        signup = client.post(
            "/auth/signup",
            json={"email": "student@example.com", "username": "student", "password": "Password123"},
        )
        assert signup.status_code == 201
        student_token = signup.json()["access_token"]

        exams = client.get("/exams", headers=_auth_header(student_token))
        assert exams.status_code == 200
        exam_id = exams.json()[0]["id"]

        attempt = client.post(
            "/attempts",
            headers=_auth_header(student_token),
            json={"exam_id": exam_id, "client_fingerprint": "browser-test"},
        )
        assert attempt.status_code == 200
        attempt_body = attempt.json()
        attempt_id = attempt_body["id"]
        session_id = attempt_body["proctoring_session_id"]

        questions = client.get(f"/attempts/{attempt_id}/questions", headers=_auth_header(student_token))
        assert questions.status_code == 200
        first_question = questions.json()["questions"][0]
        correct_option = next(option for option in first_question["options"] if option["body"] == "Unlimited length")

        answer = client.post(
            f"/attempts/{attempt_id}/answers",
            headers=_auth_header(student_token),
            json={"question_id": first_question["id"], "selected_option_id": correct_option["id"]},
        )
        assert answer.status_code == 200

        event = client.post(
            f"/proctoring/sessions/{session_id}/events",
            headers=_auth_header(student_token),
            json={"event_type": "tab switch", "confidence": 0.93, "payload": {"visible": False}},
        )
        assert event.status_code == 200
        assert event.json()["event_type"] == "TAB_SWITCH"
        assert event.json()["severity"] == "high"

        frame_analysis = client.post(
            f"/proctoring/sessions/{session_id}/analyze-frame",
            headers=_auth_header(student_token),
            files={"file": ("frame.jpg", b"fake-image-bytes", "image/jpeg")},
        )
        assert frame_analysis.status_code == 200
        assert frame_analysis.json()["frame_id"] == "fake-frame"
        assert frame_analysis.json()["signals"]["mouth"] == "Mouth Open"
        assert frame_analysis.json()["evidence_asset"] is not None
        assert {item["event_type"] for item in frame_analysis.json()["events"]} == {
            "MOUTH_OPEN",
            "PHONE_DETECTED",
        }

        loud_audio = (3000).to_bytes(2, byteorder="little", signed=True) * 4
        audio_analysis = client.post(
            f"/proctoring/sessions/{session_id}/analyze-audio",
            headers=_auth_header(student_token),
            data={"sample_rate": "44100"},
            files={"file": ("chunk.pcm", loud_audio, "application/octet-stream")},
        )
        assert audio_analysis.status_code == 200
        assert audio_analysis.json()["events"][0]["event_type"] == "AUDIO_SPIKE"

        submitted = client.post(f"/attempts/{attempt_id}/submit", headers=_auth_header(student_token))
        assert submitted.status_code == 200
        assert submitted.json()["status"] == "submitted"
        assert submitted.json()["score"] == 1.0

        login = client.post("/auth/login", json={"email": "admin@example.com", "password": "AdminPass123"})
        assert login.status_code == 200
        admin_token = login.json()["access_token"]

        timeline = client.get(f"/review/attempts/{attempt_id}/timeline", headers=_auth_header(admin_token))
        assert timeline.status_code == 200
        event_types = {item["event_type"] for item in timeline.json()["events"]}
        assert {"TAB_SWITCH", "MOUTH_OPEN", "PHONE_DETECTED", "AUDIO_SPIKE"}.issubset(event_types)

        review_attempts = client.get("/review/attempts", headers=_auth_header(admin_token))
        assert review_attempts.status_code == 200
        assert review_attempts.json()[0]["attempt_id"] == attempt_id
        assert review_attempts.json()[0]["candidate_email"] == "student@example.com"
        assert review_attempts.json()[0]["event_count"] == 4
