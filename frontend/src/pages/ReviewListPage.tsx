import { ClipboardList, RefreshCcw, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ReviewAttemptSummary } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { StatusBadge } from "../components/StatusBadge";

export function ReviewListPage() {
  const { token } = useAuth();
  const [attempts, setAttempts] = useState<ReviewAttemptSummary[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  async function loadAttempts(currentToken: string, silent = false) {
    if (!silent) {
      setLoading(true);
    }
    setError("");
    try {
      const data = await api.listReviewAttempts(currentToken);
      setAttempts(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load attempts");
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    if (!token) {
      return;
    }

    void loadAttempts(token);

    const intervalId = window.setInterval(() => {
      void loadAttempts(token, true);
    }, 10000);

    return () => window.clearInterval(intervalId);
  }, [token]);

  const filtered = useMemo(() => {
    const needle = query.toLowerCase();
    return attempts.filter(
      (attempt) =>
        attempt.exam_title.toLowerCase().includes(needle) ||
        attempt.candidate_email.toLowerCase().includes(needle) ||
        attempt.candidate_username.toLowerCase().includes(needle)
    );
  }, [attempts, query]);

  return (
    <section className="page-section wide">
      <div className="page-heading">
        <div>
          <h1>Review attempts</h1>
          <p>Inspect submitted and active attempts with captured proctoring events.</p>
          <p className="muted">
            {lastUpdated ? `Last updated at ${lastUpdated}.` : "Waiting for review data."} New attempts refresh automatically every 10
            seconds.
          </p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => token && void loadAttempts(token)}
          disabled={!token || loading}
        >
          <RefreshCcw size={16} /> {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>
      <label className="search-box">
        <Search size={18} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search exam or candidate" />
      </label>
      {error && <p className="error-text">{error}</p>}
      <div className="table-panel">
        <table>
          <thead>
            <tr>
              <th>Exam</th>
              <th>Candidate</th>
              <th>Status</th>
              <th>Submitted</th>
              <th>Score</th>
              <th>Events</th>
              <th>Latest event</th>
              <th>Review</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((attempt) => (
              <tr key={attempt.attempt_id}>
                <td>{attempt.exam_title}</td>
                <td>
                  {attempt.candidate_username}
                  <small>{attempt.candidate_email}</small>
                </td>
                <td>
                  <StatusBadge value={attempt.status} />
                </td>
                <td>{attempt.submitted_at ? new Date(attempt.submitted_at).toLocaleString() : "-"}</td>
                <td>{attempt.score ?? "-"}</td>
                <td>{attempt.event_count}</td>
                <td>{attempt.latest_event_type ?? "-"}</td>
                <td>
                  <Link className="inline-link" to={`/admin/review/${attempt.attempt_id}`}>
                    <ClipboardList size={16} /> Open
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && (
          <p className="muted table-empty">
            {attempts.length ? "No attempts match the current search." : "No candidate attempts have been recorded yet."}
          </p>
        )}
      </div>
    </section>
  );
}
