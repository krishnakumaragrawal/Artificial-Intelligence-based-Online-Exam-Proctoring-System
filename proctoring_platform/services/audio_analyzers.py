from array import array
from typing import Dict, List

from proctoring_platform.services.detectors import DetectorEvent


class PCM16AudioAnalyzer:
    """Detect audio spikes from raw little-endian PCM16 microphone chunks."""

    def __init__(self, threshold: int = 2000) -> None:
        self.threshold = threshold

    def analyze(self, chunk: bytes, sample_rate: int) -> List[DetectorEvent]:
        signals = self.signals(chunk, sample_rate)
        if signals["peak_amplitude"] > self.threshold:
            return [
                DetectorEvent(
                    event_type="AUDIO_SPIKE",
                    confidence=min(1.0, signals["peak_amplitude"] / 32767),
                    payload=signals,
                )
            ]
        return []

    def signals(self, chunk: bytes, sample_rate: int) -> Dict[str, int]:
        if len(chunk) < 2:
            return {"sample_rate": sample_rate, "sample_count": 0, "peak_amplitude": 0}

        samples = array("h")
        samples.frombytes(chunk[: len(chunk) - (len(chunk) % 2)])
        peak = max((abs(sample) for sample in samples), default=0)
        return {
            "sample_rate": sample_rate,
            "sample_count": len(samples),
            "peak_amplitude": int(peak),
        }
