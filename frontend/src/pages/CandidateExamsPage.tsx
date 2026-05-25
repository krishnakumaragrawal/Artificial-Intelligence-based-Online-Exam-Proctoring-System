import { Clock, PlayCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ExamSummary } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function CandidateExamsPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [exams, setExams] = useState<ExamSummary[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [startingId, setStartingId] = useState<number | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    api
      .listExams(token)
      .then(setExams)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load exams"))
      .finally(() => setLoading(false));
  }, [token]);

  async function startExam(examId: number) {
    if (!token) {
      return;
    }
    setStartingId(examId);
    setError("");
    try {
      const attempt = await api.createAttempt(token, examId, navigator.userAgent);
      navigate(`/candidate/attempts/${attempt.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start exam");
    } finally {
      setStartingId(null);
    }
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <h1>Candidate exams</h1>
          <p>Start an available exam when you are ready with camera permissions enabled.</p>
        </div>
      </div>
      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p className="muted">Loading exams...</p>
      ) : (
        <div className="item-grid">
          {exams.map((exam) => (
            <article className="panel" key={exam.id}>
              <h2>{exam.title}</h2>
              <p>{exam.description || "No description provided."}</p>
              <p className="meta-line">
                <Clock size={16} /> {Math.round(exam.duration_seconds / 60)} minutes
              </p>
              <button className="primary-button" type="button" onClick={() => startExam(exam.id)}>
                <PlayCircle size={18} /> {startingId === exam.id ? "Starting..." : "Start exam"}
              </button>
            </article>
          ))}
          {!exams.length && <p className="muted">No published exams are available.</p>}
        </div>
      )}
    </section>
  );
}
