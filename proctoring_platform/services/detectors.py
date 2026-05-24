from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from proctoring_platform.core.time import now_utc


@dataclass(frozen=True)
class DetectorEvent:
    event_type: str
    confidence: Optional[float] = None
    occurred_at: datetime = field(default_factory=now_utc)
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FrameAnalysis:
    frame_id: str
    events: List[DetectorEvent]
    payload: Dict[str, Any] = field(default_factory=dict)


class FrameAnalyzer(Protocol):
    def analyze(self, frame: Any, frame_id: str) -> FrameAnalysis:
        """Analyze one frame and return structured detector events."""


class AudioAnalyzer(Protocol):
    def analyze(self, chunk: bytes, sample_rate: int) -> List[DetectorEvent]:
        """Analyze one audio chunk and return structured detector events."""


class DetectorUnavailable(RuntimeError):
    """Raised when optional detector runtime dependencies are not installed."""
