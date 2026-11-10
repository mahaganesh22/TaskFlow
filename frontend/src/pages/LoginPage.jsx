import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { fieldErrorsFromDetail, formatDetail } from "../api/client";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    const nextErrors = {};
    if (!email.trim()) nextErrors.email = "Email is required";
    if (!password) nextErrors.password = "Password is required";

    setErrors(nextErrors);
    setFormError("");

    if (Object.keys(nextErrors).length) return;

    setSubmitting(true);

    try {
      await login({ email: email.trim(), password });
      const next = location.state?.from?.pathname || "/";
      navigate(next, { replace: true });
    } catch (error) {
      setErrors(fieldErrorsFromDetail(error.detail));
      setFormError(formatDetail(error.detail) || "Could not log in");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <p className="eyebrow">TaskFlow</p>
        <h1>Welcome back</h1>
        <p className="muted">Log in to your boards, assignments, and live updates.</p>

        <form onSubmit={handleSubmit} className="stack">
          {formError && <div className="alert">{formError}</div>}

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
            />
            {errors.email && <span className="field-error">{errors.email}</span>}
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
            {errors.password && <span className="field-error">{errors.password}</span>}
          </label>

          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Log in"}
          </button>
        </form>

        <p className="muted">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
