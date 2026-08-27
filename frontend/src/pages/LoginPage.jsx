import { useState } from "react";
import { api } from "../api.js";
import { saveSession } from "../auth.js";
import Typewriter from "../components/Typewriter.jsx";

const PHASES = [
  "Tracking where training leads.",
  "Finding where skills are missing.",
  "Measuring what actually works.",
];

const DEMO = [
  { role: "Government", email: "admin@sih.gov.in" },
  { role: "Provider", email: "provider@sih.gov.in" },
  { role: "Trainee", email: "trainee@sih.gov.in" },
];

export default function LoginPage({ onAuthChange }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const data = await api.login(email.trim(), password);
      saveSession(data);
      // Land straight on this role's own view instead of "#" ("/"), which
      // is the admin dashboard and would trip the unavailable-page guard.
      const ROLE_HOME = { admin: "/", provider: "/overview", trainee: "/my-profile" };
      window.location.hash = ROLE_HOME[data.role] || "/";
      if (onAuthChange) onAuthChange();
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="brand-col">
          <div className="brand mark-lg">SA</div>
          <div className="login-banner">
            <h1>StatAvishkar</h1>
            <p className="login-tag">A Skilling Intelligence Platform</p>
          </div>
        </div>
      </div>

      <div className="login-card-wrap">
        <div className="login-card">
          <div className="login-head">
            <span className="login-kicker">Secure government access</span>
            <h2>Sign in</h2>
            <Typewriter phrases={PHASES} />
          </div>

          {error && <div className="form-error">{error}</div>}

          <form onSubmit={submit} className="form">
            <label className="field">
              <span>Email</span>
              <input
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@section.gov.in"
                required
              />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </label>
            <button className="btn btn-primary btn-block" disabled={busy} type="submit">
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="demo-row">
            <span className="demo-label">Demo accounts</span>
            <div className="demo-buttons">
              {DEMO.map((d) => (
                <button
                  key={d.role}
                  type="button"
                  className="demo-pill"
                  onClick={() => {
                    setEmail(d.email);
                    setPassword("demo123");
                  }}
                >
                  {d.role} · {d.email}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}