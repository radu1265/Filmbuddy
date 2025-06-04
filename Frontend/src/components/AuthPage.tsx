// src/components/AuthPage.tsx
import React, { useState } from 'react';
import CreateAccount from './CreateAccount';

type AuthPageProps = {
  // After successful “login,” we call setUserId with a numeric ID.
  setUserId: (id: number) => void;
};

const AuthPage: React.FC<AuthPageProps> = ({ setUserId }) => {
  const [isRegistering, setIsRegistering] = useState(false);

  // State for login form
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Handler when registration completes (we receive a newUserId)
  const handleSuccessfulRegistration = (newUserId: number) => {
    // You might want to auto-login them here, or just switch back to login screen.
    // For now, let’s just pass the ID upward and stay on login:
    setUserId(newUserId);
  };

  // Toggle between login vs registration
  const toggleMode = () => {
    setIsRegistering((prev) => !prev);
    // Clear login fields when switching
    setUsername('');
    setPassword('');
  };

  // ------------ LOGIN FORM HANDLER ----------------
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: replace this placeholder logic with real authentication (e.g. fetch to /users/login).
    if (username.trim() && password.trim()) {
      // For now, we simply assign a dummy user ID (e.g. 1).
      setUserId(1);
    } else {
      alert('Please enter both username and password.');
    }
  };

  // ------------ RENDER ----------------
  if (isRegistering) {
    return (
      <CreateAccount
        onRegistered={handleSuccessfulRegistration}
        onCancel={toggleMode}
      />
    );
  }

  // Otherwise, render LOGIN form
  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="card shadow-sm" style={{ width: '100%', maxWidth: '600px' }}>
        <div className="card-body">
          <h4 className="card-title text-center mb-4">FilmBuddy Login</h4>
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="username-input" className="form-label">
                Username
              </label>
              <input
                id="username-input"
                type="text"
                className="form-control"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="password-input" className="form-label">
                Password
              </label>
              <input
                id="password-input"
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
              />
            </div>
            <button type="submit" className="btn btn-primary w-100 mb-2">
              Login
            </button>
          </form>
          <hr />
          <button
            className="btn btn-link w-100"
            onClick={toggleMode}
          >
            Create a new account
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
