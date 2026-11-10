import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { fieldErrorsFromDetail, formatDetail } from "../api/client";

function validatePassword(password) {
  if (password.length < 8) return "Password must be at least 8 characters";
  if (!/[A-Z]/.test(password)) return "Password must contain an uppercase letter";
  if (!/[a-z]/.test(password)) return "Password must contain a lowercase letter";
  if (!/\d/.test(password)) return "Password must contain a digit";
  return "";
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    const nextErrors = {};
    if (name.trim().length < 2) nextErrors.name = "Name must be at least 2 characters";
    if (!email.trim()) nextErrors.email = "Email is required";

    const passwordError = validatePassword(password);
    if (passwordError) nextErrors.password = passwordError;

    setErrors(nextErrors);
    setFormError("");

    if (Object.keys(nextErrors).length) return;

    setSubmitting(true);

    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password
      });
      navigate("/", { replace: true });
    } catch (error) {
      setErrors(fieldErrorsFromDetail(error.detail));
      setFormError(formatDetail(error.detail) || "Could not create account");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <p className="eyebrow">TaskFlow</p>
        <h1>Create your account</h1>
        <p className="muted">
          Use a valid email and a password with 8+ characters, mixed case, and a number.
        </p>

        <form onSubmit={handleSubmit} className="stack">
          {formError && <div className="alert">{formError}</div>}

          <label>
            Name
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              autoComplete="name"
            />
            {errors.name && <span className="field-error">{errors.name}</span>}
          </label>

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
              autoComplete="new-password"
            />
            {errors.password && <span className="field-error">{errors.password}</span>}
          </label>

          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Creating account…" : "Sign up"}
          </button>
        </form>

        <p className="muted">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
