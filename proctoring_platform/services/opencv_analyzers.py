from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

from proctoring_platform.services.detectors import DetectorEvent, DetectorUnavailable, FrameAnalysis


SUSPICIOUS_OBJECTS = {
    "book",
    "cell phone",
    "keyboard",
    "laptop",
    "mouse",
    "remote",
    "tvmonitor",
}


@dataclass(frozen=True)
class LegacyDetectorFunctions:
    detect_face: Callable[[Any], Tuple[int, Sequence[Any]]]
    detect_blink: Callable[[Sequence[Any], Any], Tuple[Any, ...]]
    detect_gaze: Callable[[Sequence[Any], Any], str]
    detect_mouth: Callable[[Sequence[Any], Any], str]
    detect_head_pose: Callable[[Sequence[Any], Any], Any]
    detect_object: Callable[[Any], Sequence[Tuple[str, float]]]


def load_legacy_detector_functions() -> LegacyDetectorFunctions:
    try:
        from blink_detection import isBlinking
        from eye_tracker import gazeDetection
        from facial_detections import detectFace
        from head_pose_estimation import head_pose_detection
        from mouth_tracking import mouthTrack
        from object_detection import detectObject
    except Exception as exc:
        raise DetectorUnavailable(f"OpenCV/Dlib detector dependencies are unavailable: {exc}") from exc

    return LegacyDetectorFunctions(
        detect_face=detectFace,
        detect_blink=isBlinking,
        detect_gaze=gazeDetection,
        detect_mouth=mouthTrack,
        detect_head_pose=head_pose_detection,
        detect_object=detectObject,
    )


class LegacyOpenCVFrameAnalyzer:
    def __init__(self, detector_functions: Optional[LegacyDetectorFunctions] = None) -> None:
        self.detectors = detector_functions or load_legacy_detector_functions()

    def analyze_image_bytes(self, image_bytes: bytes, frame_id: Optional[str] = None) -> FrameAnalysis:
        try:
            import cv2
            import numpy as np
        except Exception as exc:
            raise DetectorUnavailable(f"OpenCV image decoding dependencies are unavailable: {exc}") from exc

        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Uploaded file is not a valid image frame")
        return self.analyze(frame, frame_id or uuid4().hex)

    def analyze(self, frame: Any, frame_id: str) -> FrameAnalysis:
        working_frame = frame.copy()
        events: List[DetectorEvent] = []
        signals: Dict[str, Any] = {}

        face_count, faces = self.detectors.detect_face(working_frame)
        signals["face_count"] = face_count

        if face_count == 0:
            events.append(DetectorEvent(event_type="NO_FACE", confidence=1.0, payload={"face_count": 0}))
            return FrameAnalysis(frame_id=frame_id, events=events, payload=signals)

        if face_count > 1:
            events.append(DetectorEvent(event_type="MULTIPLE_FACES", confidence=1.0, payload={"face_count": face_count}))
            return FrameAnalysis(frame_id=frame_id, events=events, payload=signals)

        self._append_single_face_signals(working_frame, faces, signals, events)
        return FrameAnalysis(frame_id=frame_id, events=events, payload=signals)

    def _append_single_face_signals(
        self,
        frame: Any,
        faces: Sequence[Any],
        signals: Dict[str, Any],
        events: List[DetectorEvent],
    ) -> None:
        blink_status = self._safe_call("blink", signals, self.detectors.detect_blink, faces, frame)
        if blink_status:
            signals["blink"] = {
                "left_ratio": blink_status[0] if len(blink_status) > 0 else None,
                "right_ratio": blink_status[1] if len(blink_status) > 1 else None,
                "status": blink_status[2] if len(blink_status) > 2 else None,
            }

        gaze = self._safe_call("gaze", signals, self.detectors.detect_gaze, faces, frame)
        if gaze:
            signals["gaze"] = gaze
            if gaze in {"left", "right"}:
                events.append(
                    DetectorEvent(
                        event_type="GAZE_AWAY",
                        confidence=0.82,
                        payload={"direction": gaze},
                    )
                )

        mouth = self._safe_call("mouth", signals, self.detectors.detect_mouth, faces, frame)
        if mouth:
            signals["mouth"] = mouth
            if mouth == "Mouth Open":
                events.append(DetectorEvent(event_type="MOUTH_OPEN", confidence=0.78, payload={"status": mouth}))

        head_pose = self._safe_call("head_pose", signals, self.detectors.detect_head_pose, faces, frame)
        if head_pose is not None:
            signals["head_pose"] = head_pose
            if isinstance(head_pose, str) and head_pose.startswith("Head "):
                events.append(DetectorEvent(event_type="HEAD_AWAY", confidence=0.82, payload={"pose": head_pose}))

        objects = self._safe_call("objects", signals, self.detectors.detect_object, frame)
        if objects is not None:
            normalized_objects = [
                {"label": label, "confidence": float(confidence)}
                for label, confidence in objects
            ]
            signals["objects"] = normalized_objects
            self._append_object_events(normalized_objects, events)

    def _append_object_events(self, objects: List[Dict[str, Any]], events: List[DetectorEvent]) -> None:
        for detected in objects:
            label = detected["label"]
            confidence = detected["confidence"]
            if label == "cell phone":
                events.append(DetectorEvent(event_type="PHONE_DETECTED", confidence=confidence, payload=detected))
            elif label in SUSPICIOUS_OBJECTS:
                events.append(DetectorEvent(event_type="UNAUTHORIZED_OBJECT", confidence=confidence, payload=detected))

    def _safe_call(self, name: str, signals: Dict[str, Any], func: Callable[..., Any], *args: Any) -> Any:
        try:
            return func(*args)
        except Exception as exc:
            signals.setdefault("detector_errors", {})[name] = str(exc)
            return None
