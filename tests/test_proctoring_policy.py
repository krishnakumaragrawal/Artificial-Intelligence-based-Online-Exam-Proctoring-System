from proctoring_platform.models import EventSeverity
from proctoring_platform.services.audio_analyzers import PCM16AudioAnalyzer
from proctoring_platform.services.opencv_analyzers import LegacyDetectorFunctions, LegacyOpenCVFrameAnalyzer
from proctoring_platform.services.proctoring_policy import ProctoringPolicy


def test_policy_normalizes_event_names_and_assigns_severity():
    policy = ProctoringPolicy()

    assert policy.normalize_event_type("tab switch") == "TAB_SWITCH"
    assert policy.normalize_event_type("camera-interrupted") == "CAMERA_INTERRUPTED"
    assert policy.severity_for("tab switch") == EventSeverity.high
    assert policy.severity_for("unknown-event") == EventSeverity.info


def test_policy_requests_evidence_for_high_severity_or_high_confidence():
    policy = ProctoringPolicy()

    assert policy.should_attach_evidence("PHONE_DETECTED", confidence=0.55)
    assert policy.should_attach_evidence("GAZE_AWAY", confidence=0.91)
    assert not policy.should_attach_evidence("GAZE_AWAY", confidence=0.60)


def test_pcm16_audio_analyzer_emits_audio_spike_for_loud_chunk():
    analyzer = PCM16AudioAnalyzer(threshold=2000)
    loud_chunk = (3000).to_bytes(2, byteorder="little", signed=True) * 4

    events = analyzer.analyze(loud_chunk, sample_rate=44100)

    assert events[0].event_type == "AUDIO_SPIKE"
    assert events[0].payload["peak_amplitude"] == 3000


def test_legacy_opencv_analyzer_maps_detector_outputs_to_events():
    class FakeFrame:
        def copy(self):
            return self

    analyzer = LegacyOpenCVFrameAnalyzer(
        LegacyDetectorFunctions(
            detect_face=lambda frame: (1, ["face"]),
            detect_blink=lambda faces, frame: (2.0, 2.2, "No Blink"),
            detect_gaze=lambda faces, frame: "left",
            detect_mouth=lambda faces, frame: "Mouth Open",
            detect_head_pose=lambda faces, frame: "Head Right",
            detect_object=lambda frame: [("cell phone", 0.92), ("book", 0.86)],
        )
    )

    analysis = analyzer.analyze(FakeFrame(), "frame-1")

    assert analysis.payload["face_count"] == 1
    assert {event.event_type for event in analysis.events} == {
        "GAZE_AWAY",
        "MOUTH_OPEN",
        "HEAD_AWAY",
        "PHONE_DETECTED",
        "UNAUTHORIZED_OBJECT",
    }


def test_legacy_opencv_analyzer_keeps_object_detection_when_no_face_is_found():
    class FakeFrame:
        def copy(self):
            return self

    analyzer = LegacyOpenCVFrameAnalyzer(
        LegacyDetectorFunctions(
            detect_face=lambda frame: (0, []),
            detect_blink=lambda faces, frame: (),
            detect_gaze=lambda faces, frame: "center",
            detect_mouth=lambda faces, frame: "Mouth Close",
            detect_head_pose=lambda faces, frame: -1,
            detect_object=lambda frame: [("cell phone", 0.91)],
        )
    )

    analysis = analyzer.analyze(FakeFrame(), "frame-2")

    assert analysis.payload["face_count"] == 0
    assert analysis.payload["objects"] == [{"label": "cell phone", "confidence": 0.91}]
    assert {event.event_type for event in analysis.events} == {"NO_FACE", "PHONE_DETECTED"}
