// src/components/AuthPage.tsx
import React, { useState } from 'react';
import CreateAccount from './CreateAccount';

type AuthPageProps = {
  setUserId: (id: number) => void;
  setUsername: (name: string) => void;
  setAlpha: (a: number) => void;
  onLoginComplete: (userId: number) => void;
};

const AuthPage: React.FC<AuthPageProps> = ({
  setUserId,
  setUsername,
  setAlpha,
  onLoginComplete,
}) => {
  const [isRegistering, setIsRegistering] = useState(false);
  const [usernameInput, setUsernameInput] = useState('');
  const [password, setPassword] = useState('');

  const handleSuccessfulRegistration = (newUserId: number) => {
    setUserId(newUserId);
  };

  const toggleMode = () => {
    setIsRegistering((prev) => !prev);
    setUsernameInput('');
    setPassword('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedUsername = usernameInput.trim();
    if (!trimmedUsername) {
      alert('Please enter your username.');
      return;
    }
    if (password.length < 4) {
      alert('Password must be at least 4 characters.');
      return;
    }

    const payload = { username: trimmedUsername, password };
    try {
      const resp = await fetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        let detail = 'Login failed. Please try again.';
        try {
          const errJson = await resp.json();
          if (errJson.detail) detail = errJson.detail;
        } catch {}
        throw new Error(detail);
      }

      const data = await resp.json();
      // Expecting { user_id: number, alpha: number, success: true }
      if (
        typeof data.user_id !== 'number' ||
        typeof data.alpha !== 'number'
      ) {
        throw new Error('Invalid response from server.');
      }

      setUserId(data.user_id);
      setUsername(trimmedUsername);
      setAlpha(data.alpha);
      onLoginComplete(data.user_id);
    } catch (err: any) {
      console.error('Login error:', err);
      alert(err.message || 'Login failed. Please try again.');
    }
  };

  if (isRegistering) {
    return (
      <CreateAccount
        onRegistered={handleSuccessfulRegistration}
        onCancel={toggleMode}
      />
    );
  }

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
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
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
          <button className="btn btn-link w-100" onClick={toggleMode}>
            Create a new account
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
