import { CheckCircle2, Send } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ExamDetail, ProctoringEventPublic } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ProctoringPanel } from "../components/ProctoringPanel";
import { StatusBadge } from "../components/StatusBadge";

export function ExamAttemptPage() {
  const { attemptId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const numericAttemptId = Number(attemptId);
  const [exam, setExam] = useState<ExamDetail | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [events, setEvents] = useState<ProctoringEventPublic[]>([]);
  const [error, setError] = useState("");
  const [submittedScore, setSubmittedScore] = useState<number | null>(null);
  const [savingQuestion, setSavingQuestion] = useState<number | null>(null);

  useEffect(() => {
    if (!token || Number.isNaN(numericAttemptId)) {
      return;
    }
    Promise.all([api.getAttemptQuestions(token, numericAttemptId), api.getAttempt(token, numericAttemptId)])
      .then(([examDetail, attempt]) => {
        setExam(examDetail);
        if (!attempt.proctoring_session_id) {
          throw new Error("Attempt does not have a proctoring session");
        }
        setSessionId(attempt.proctoring_session_id);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load attempt"));
  }, [numericAttemptId, token]);

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);

  const onEvent = useCallback((event: ProctoringEventPublic) => {
    setEvents((current) => [event, ...current].slice(0, 8));
  }, []);

  async function chooseAnswer(questionId: number, optionId: number) {
    if (!token) {
      return;
    }
    setAnswers((current) => ({ ...current, [questionId]: optionId }));
    setSavingQuestion(questionId);
    setError("");
    try {
      await api.saveAnswer(token, numericAttemptId, questionId, optionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save answer");
    } finally {
      setSavingQuestion(null);
    }
  }

  async function submitAttempt() {
    if (!token) {
      return;
    }
    try {
      const result = await api.submitAttempt(token, numericAttemptId);
      setSubmittedScore(result.score);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit attempt");
    }
  }

  if (submittedScore !== null) {
    return (
      <section className="completion-state">
        <CheckCircle2 size={52} />
        <h1>Exam submitted</h1>
        <p>Your score is {submittedScore}. The proctoring timeline is available to reviewers.</p>
        <button className="primary-button" type="button" onClick={() => navigate("/candidate/exams")}>
          Back to exams
        </button>
      </section>
    );
  }

  return (
    <section className="exam-layout">
      <div className="exam-main">
        <div className="page-heading">
          <div>
            <h1>{exam?.title ?? "Loading exam"}</h1>
            <p>
              {answeredCount} of {exam?.questions.length ?? 0} questions answered
            </p>
          </div>
          <button className="primary-button" type="button" onClick={submitAttempt} disabled={!exam}>
            <Send size={18} /> Submit
          </button>
        </div>
        {error && <p className="error-text">{error}</p>}
        <div className="question-list">
          {exam?.questions.map((question) => (
            <article className="panel question-panel" key={question.id}>
              <div className="question-header">
                <h2>
                  {question.order_index}. {question.prompt}
                </h2>
                {savingQuestion === question.id && <span className="muted">Saving...</span>}
              </div>
              <div className="option-stack">
                {question.options.map((option) => (
                  <label className="option-row" key={option.id}>
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      checked={answers[question.id] === option.id}
                      onChange={() => chooseAnswer(question.id, option.id)}
                    />
                    <span>{option.body}</span>
                  </label>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
      <aside className="exam-side">
        {token && sessionId && <ProctoringPanel token={token} sessionId={sessionId} active onEvent={onEvent} />}
        <section className="panel">
          <h2>Recent events</h2>
          <div className="timeline-list compact">
            {events.map((event) => (
              <div className="timeline-row" key={event.id}>
                <StatusBadge value={event.severity} />
                <span>{event.event_type}</span>
              </div>
            ))}
            {!events.length && <p className="muted">No proctoring events recorded in this browser session.</p>}
          </div>
        </section>
      </aside>
    </section>
  );
}
