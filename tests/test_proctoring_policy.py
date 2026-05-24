from proctoring_platform.models import EventSeverity
from proctoring_platform.services.audio_analyzers import PCM16AudioAnalyzer
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
