// src/components/AuthPage.tsx
import React, { useState } from 'react';
import CreateAccount from './CreateAccount';

type AuthPageProps = {
  // After successful “login,” we call setUserId with a numeric ID,
  // and setUsername with the string username.
  setUserId: (id: number) => void;
  setUsername: (name: string) => void;
};

const AuthPage: React.FC<AuthPageProps> = ({ setUserId, setUsername }) => {
  const [isRegistering, setIsRegistering] = useState(false);

  // State for login form
  const [username, setUsernameInput] = useState('');
  const [password, setPassword] = useState('');

  // Handler when registration completes (we receive a newUserId)
  const handleSuccessfulRegistration = (newUserId: number) => {
    setUserId(newUserId);
    // Optionally setUsername here if CreateAccount returns the username
  };

  // Toggle between login vs registration
  const toggleMode = () => {
    setIsRegistering((prev) => !prev);
    setUsernameInput('');
    setPassword('');
  };

  // ------------ LOGIN FORM HANDLER ----------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 1) Validate that "username" is nonempty
    const trimmedUsername = username.trim();
    if (!trimmedUsername) {
      alert('Please enter your username.');
      return;
    }

    // 2) Validate password length
    if (password.length < 4) {
      alert('Password must be at least 4 characters.');
      return;
    }

    // 3) Build payload and send request
    const payload = { username: trimmedUsername, password };
    try {
      const resp = await fetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      console.log('Login request sent:', payload);
      console.log('Response status:', resp.status);

      if (!resp.ok) {
        let detail = 'Login failed. Please try again.';
        try {
          const errJson = await resp.json();
          if (errJson.detail) detail = errJson.detail;
        } catch {
          // ignore parse errors
        }
        throw new Error(detail);
      }

      const data = await resp.json();
      console.log('Login successful:', data);

      // 4) Extract numeric user_id from response and store both ID and username
      if (typeof data.user_id !== 'number') {
        throw new Error('Invalid response from server.');
      }
      setUserId(data.user_id);
      setUsername(trimmedUsername);
    } catch (err: any) {
      console.error('Login error:', err);
      alert(err.message || 'Login failed. Please try again.');
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
