import { Camera, Eye, MicVocal, ShieldAlert, WifiOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, FrameAnalysisResponse, ProctoringEventPublic } from "../api/client";

interface ProctoringPanelProps {
  token: string;
  sessionId: number;
  active: boolean;
  onEvent: (event: ProctoringEventPublic) => void;
}

export function ProctoringPanel({ token, sessionId, active, onEvent }: ProctoringPanelProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzingRef = useRef(false);
  const [streamReady, setStreamReady] = useState(false);
  const [status, setStatus] = useState("Waiting for camera");
  const [lastAnalysis, setLastAnalysis] = useState<FrameAnalysisResponse | null>(null);

  function beepAlert() {
    try {
      const audioContext = audioContextRef.current ?? new AudioContext();
      audioContextRef.current = audioContext;
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();

      oscillator.type = "square";
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.08, audioContext.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.18);

      oscillator.connect(gain);
      gain.connect(audioContext.destination);
      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch {
      // Ignore audio playback failures caused by browser autoplay restrictions.
    }
  }

  function pushFlaggedEvent(event: ProctoringEventPublic) {
    beepAlert();
    onEvent(event);
  }

  useEffect(() => {
    if (!active) {
      return;
    }

    let stream: MediaStream | null = null;
    let cancelled = false;

    async function startCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setStreamReady(true);
        setStatus("Camera active");
      } catch (error) {
        setStatus("Camera unavailable");
        const event = await api.sendProctoringEvent(token, sessionId, {
          event_type: "CAMERA_INTERRUPTED",
          confidence: 1,
          payload: { reason: error instanceof Error ? error.message : "camera permission denied" }
        });
        pushFlaggedEvent(event);
      }
    }

    startCamera();

    return () => {
      cancelled = true;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [active, sessionId, token]);

  useEffect(() => {
    if (!active || !streamReady) {
      return;
    }

    const interval = window.setInterval(async () => {
      if (analyzingRef.current) {
        return;
      }

      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || video.videoWidth === 0 || video.videoHeight === 0) {
        return;
      }

      analyzingRef.current = true;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext("2d")?.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(async (blob: Blob | null) => {
        if (!blob) {
          analyzingRef.current = false;
          return;
        }
        try {
          setStatus("Analyzing live frame");
          const analysis = await api.analyzeFrame(token, sessionId, blob);
          setLastAnalysis(analysis);
          analysis.events.forEach(pushFlaggedEvent);
          setStatus(analysis.events.length ? "Attention event detected" : "Live monitoring active");
        } catch (error) {
          setStatus(error instanceof Error ? error.message : "Frame analysis failed");
        } finally {
          analyzingRef.current = false;
        }
      }, "image/jpeg", 0.75);
    }, 2500);

    return () => window.clearInterval(interval);
  }, [active, sessionId, streamReady, token]);

  useEffect(() => {
    if (!active) {
      return;
    }

    const onVisibility = () => {
      if (document.hidden) {
        api
          .sendProctoringEvent(token, sessionId, {
            event_type: "TAB_SWITCH",
            confidence: 1,
            payload: { hidden: true }
          })
          .then(pushFlaggedEvent)
          .catch(() => undefined);
      }
    };
    const onOffline = () => {
      api
        .sendProctoringEvent(token, sessionId, {
            event_type: "NETWORK_INTERRUPTED",
            confidence: 1,
            payload: { online: false }
          })
          .then(pushFlaggedEvent)
          .catch(() => undefined);
    };
    const onFullscreen = () => {
      if (!document.fullscreenElement) {
        api
          .sendProctoringEvent(token, sessionId, {
              event_type: "FULLSCREEN_EXIT",
              confidence: 1,
              payload: { fullscreen: false }
            })
          .then(pushFlaggedEvent)
          .catch(() => undefined);
      }
    };

    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("offline", onOffline);
    document.addEventListener("fullscreenchange", onFullscreen);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("offline", onOffline);
      document.removeEventListener("fullscreenchange", onFullscreen);
    };
  }, [active, sessionId, token]);

  useEffect(() => {
    return () => {
      audioContextRef.current?.close().catch(() => undefined);
      audioContextRef.current = null;
    };
  }, []);

  return (
    <section className="panel proctoring-panel">
      <div className="panel-heading">
        <div>
          <h2>Proctoring</h2>
          <p>Live snapshots are analyzed every 2.5 seconds for gaze, mouth, head pose, face count, and flagged objects.</p>
        </div>
        <span className="status status-active">{status}</span>
      </div>
      <video ref={videoRef} className="camera-preview" muted playsInline />
      <canvas ref={canvasRef} hidden />
      <div className="signal-grid">
        <span>
          <Camera size={16} /> {streamReady ? "Camera ready" : "Camera pending"}
        </span>
        <span>
          <Eye size={16} /> {String(lastAnalysis?.signals.gaze ?? "unknown")}
        </span>
        <span>
          <ShieldAlert size={16} /> {lastAnalysis?.events.length ?? 0} latest events
        </span>
        <span>
          <MicVocal size={16} /> {String(lastAnalysis?.signals.mouth ?? "unknown")}
        </span>
        <span>
          <WifiOff size={16} /> {String(lastAnalysis?.signals.head_pose ?? "browser events tracked")}
        </span>
      </div>
    </section>
  );
}
