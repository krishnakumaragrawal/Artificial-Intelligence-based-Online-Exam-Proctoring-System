import { FileCheck2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, AttemptTimeline, ReviewOutcome } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { StatusBadge } from "../components/StatusBadge";

const outcomes: { value: ReviewOutcome; label: string }[] = [
  { value: "clear", label: "Clear" },
  { value: "needs_follow_up", label: "Needs follow-up" },
  { value: "violation_confirmed", label: "Violation confirmed" },
  { value: "void_attempt", label: "Void attempt" }
];

export function ReviewTimelinePage() {
  const { attemptId } = useParams();
  const { token } = useAuth();
  const [timeline, setTimeline] = useState<AttemptTimeline | null>(null);
  const [outcome, setOutcome] = useState<ReviewOutcome>("clear");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || !attemptId) {
      return;
    }
    api
      .getTimeline(token, Number(attemptId))
      .then(setTimeline)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load timeline"));
  }, [attemptId, token]);

  async function saveDecision(event: FormEvent) {
    event.preventDefault();
    if (!token || !attemptId) {
      return;
    }
    try {
      const decision = await api.createReviewDecision(token, Number(attemptId), outcome, notes);
      setTimeline((current) =>
        current ? { ...current, review_decisions: [decision, ...current.review_decisions] } : current
      );
      setNotes("");
      setMessage("Review decision saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save decision");
    }
  }

  return (
    <section className="page-section wide">
      <div className="page-heading">
        <div>
          <h1>Attempt timeline</h1>
          <p>Review proctoring events, evidence metadata, and final decisions.</p>
        </div>
      </div>
      {error && <p className="error-text">{error}</p>}
      {message && <p className="success-text">{message}</p>}
      {timeline && (
        <div className="review-grid">
          <section className="panel">
            <h2>Attempt</h2>
            <dl className="detail-list">
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge value={timeline.attempt.status} />
                </dd>
              </div>
              <div>
                <dt>Score</dt>
                <dd>{timeline.attempt.score ?? "-"}</dd>
              </div>
              <div>
                <dt>Started</dt>
                <dd>{new Date(timeline.attempt.started_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt>Due</dt>
                <dd>{new Date(timeline.attempt.due_at).toLocaleString()}</dd>
              </div>
            </dl>
          </section>

          <section className="panel">
            <h2>Review decision</h2>
            <form className="form-stack" onSubmit={saveDecision}>
              <label>
                Outcome
                <select value={outcome} onChange={(event) => setOutcome(event.target.value as ReviewOutcome)}>
                  {outcomes.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Notes
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} />
              </label>
              <button className="primary-button" type="submit">
                <FileCheck2 size={18} /> Save decision
              </button>
            </form>
          </section>

          <section className="panel span-two">
            <h2>Proctoring events</h2>
            <div className="timeline-list">
              {timeline.events.map((event) => (
                <div className="timeline-row" key={event.id}>
                  <StatusBadge value={event.severity} />
                  <strong>{event.event_type}</strong>
                  <span>{new Date(event.received_at).toLocaleString()}</span>
                  <code>{JSON.stringify(event.payload)}</code>
                </div>
              ))}
              {!timeline.events.length && <p className="muted">No events recorded.</p>}
            </div>
          </section>

          <section className="panel span-two">
            <h2>Prior decisions</h2>
            <div className="timeline-list compact">
              {timeline.review_decisions.map((decision) => (
                <div className="timeline-row" key={decision.id}>
                  <StatusBadge value={decision.outcome} />
                  <span>{decision.notes || "No notes"}</span>
                  <small>{new Date(decision.created_at).toLocaleString()}</small>
                </div>
              ))}
              {!timeline.review_decisions.length && <p className="muted">No review decisions yet.</p>}
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
