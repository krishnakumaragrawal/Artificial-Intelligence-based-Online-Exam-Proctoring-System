from dataclasses import dataclass
from typing import Dict

from proctoring_platform.models import EventSeverity


CANONICAL_EVENT_TYPES = {
    "NO_FACE",
    "MULTIPLE_FACES",
    "GAZE_AWAY",
    "HEAD_AWAY",
    "MOUTH_OPEN",
    "PHONE_DETECTED",
    "UNAUTHORIZED_OBJECT",
    "AUDIO_SPIKE",
    "TAB_SWITCH",
    "FULLSCREEN_EXIT",
    "CAMERA_INTERRUPTED",
    "MICROPHONE_INTERRUPTED",
    "NETWORK_INTERRUPTED",
}


SEVERITY_BY_EVENT_TYPE: Dict[str, EventSeverity] = {
    "NO_FACE": EventSeverity.medium,
    "MULTIPLE_FACES": EventSeverity.high,
    "GAZE_AWAY": EventSeverity.low,
    "HEAD_AWAY": EventSeverity.low,
    "MOUTH_OPEN": EventSeverity.low,
    "PHONE_DETECTED": EventSeverity.high,
    "UNAUTHORIZED_OBJECT": EventSeverity.high,
    "AUDIO_SPIKE": EventSeverity.medium,
    "TAB_SWITCH": EventSeverity.high,
    "FULLSCREEN_EXIT": EventSeverity.high,
    "CAMERA_INTERRUPTED": EventSeverity.high,
    "MICROPHONE_INTERRUPTED": EventSeverity.medium,
    "NETWORK_INTERRUPTED": EventSeverity.medium,
}


@dataclass(frozen=True)
class ProctoringPolicy:
    default_severity: EventSeverity = EventSeverity.info

    def normalize_event_type(self, event_type: str) -> str:
        normalized = event_type.strip().upper().replace("-", "_").replace(" ", "_")
        return normalized or "UNKNOWN"

    def severity_for(self, event_type: str) -> EventSeverity:
        normalized = self.normalize_event_type(event_type)
        return SEVERITY_BY_EVENT_TYPE.get(normalized, self.default_severity)

    def should_attach_evidence(self, event_type: str, confidence: float = 0.0) -> bool:
        severity = self.severity_for(event_type)
        if severity in {EventSeverity.high, EventSeverity.critical}:
            return True
        return confidence >= 0.85


policy = ProctoringPolicy()
