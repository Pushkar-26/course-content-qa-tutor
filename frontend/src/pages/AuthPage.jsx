
import { useState } from "react";
import { signupUser, loginUser } from "../services/authApi";
import "./AuthPage.css";

function AuthPage({ onAuthenticated }) {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (isSignup && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const cleanEmail = email.trim().toLowerCase();

      if (isSignup) {
        await signupUser(cleanEmail, password);
      }

      const data = await loginUser(cleanEmail, password);
      onAuthenticated(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function changeMode() {
    setIsSignup((current) => !current);
    setError("");
    setPassword("");
    setConfirmPassword("");
  }

  return (
    <main className="auth-page">
      <section className="auth-showcase">
        <div className="auth-brand">
          <span className="brand-icon">Q</span>
          <span>CourseQ</span>
        </div>

        <div className="showcase-content">
          <span className="showcase-label">YOUR AI STUDY COMPANION</span>
          <h1>Learn smarter.<br />Understand deeper.</h1>
          <p>
            Ask questions about your course material and get
            AI-powered answers grounded in your documents.
          </p>

          <div className="showcase-feature">
            <span>✓</span>
            Answers based on your documents
          </div>
          <div className="showcase-feature">
            <span>✓</span>
            Page references and source citations
          </div>
          <div className="showcase-feature">
            <span>✓</span>
            Your conversations, all in one place
          </div>
        </div>

        <p className="showcase-footer">
          Your learning, organised in one place.
        </p>
      </section>

      <section className="auth-form-side">
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-heading">
            <span className="form-eyebrow">
              {isSignup ? "GET STARTED" : "WELCOME BACK"}
            </span>

            <h2>
              {isSignup ? "Create your account" : "Sign in to CourseQ"}
            </h2>

            <p>
              {isSignup
                ? "Create an account to start learning."
                : "Continue where your learning left off."}
            </p>
          </div>

          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="At least 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isSignup ? "new-password" : "current-password"}
            minLength={isSignup ? 8 : 1}
            maxLength={128}
            required
          />

          {isSignup && (
            <>
              <label htmlFor="confirm-password">Confirm password</label>
              <input
                id="confirm-password"
                type="password"
                placeholder="Enter password again"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                required
              />
            </>
          )}

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading
              ? "Please wait..."
              : isSignup
                ? "Create account"
                : "Sign in"}
          </button>

          <p className="auth-switch">
            {isSignup
              ? "Already have an account?"
              : "Don't have an account?"}
            {" "}
            <button type="button" onClick={changeMode}>
              {isSignup ? "Sign in" : "Sign up"}
            </button>
          </p>

          <p className="auth-note">
            Your course documents help power your answers.
          </p>
        </form>
      </section>
    </main>
  );
}

export default AuthPage;
