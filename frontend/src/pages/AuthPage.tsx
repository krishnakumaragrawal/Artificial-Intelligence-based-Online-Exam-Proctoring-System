import { ShieldCheck } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { token, login, signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (token) {
    return <Navigate to="/candidate/exams" replace />;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "signup") {
        await signup(email, username, password);
      } else {
        await login(email, password);
      }
      navigate("/candidate/exams");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="brand auth-brand">
          <ShieldCheck size={34} />
          <div>
            <strong>ExamGuard</strong>
            <span>Fair online examination</span>
          </div>
        </div>
        <h1>{mode === "signup" ? "Create candidate account" : "Sign in"}</h1>
        <p className="muted">Use the production FastAPI backend to manage attempts, proctoring, and review.</p>
        <form onSubmit={onSubmit} className="form-stack">
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          {mode === "signup" && (
            <label>
              Username
              <input value={username} onChange={(event) => setUsername(event.target.value)} required />
            </label>
          )}
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>
          {error && <p className="error-text">{error}</p>}
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Working..." : mode === "signup" ? "Create account" : "Sign in"}
          </button>
        </form>
        <p className="muted">
          {mode === "signup" ? "Already have an account?" : "Need a candidate account?"}{" "}
          <Link to={mode === "signup" ? "/login" : "/signup"}>
            {mode === "signup" ? "Sign in" : "Sign up"}
          </Link>
        </p>
      </section>
    </main>
  );
}
