// src/components/CreateAccount.tsx
import React, { useState } from 'react';

type CreateAccountProps = {
  onRegistered: (newUserId: number) => void;
  onCancel: () => void;
};

const CreateAccount: React.FC<CreateAccountProps> = ({ onRegistered, onCancel }) => {
  const [age, setAge] = useState<number | ''>('');
  const [gender, setGender] = useState<'M' | 'F' | ''>('');
  const [occupation, setOccupation] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    // Basic validation
    if (
      age === '' ||
      gender === '' ||
      !occupation.trim() ||
      !zipCode.trim() ||
      password.length < 4
    ) {
      setError("Please fill in all fields (password ≥ 4 chars).");
      return;
    }

    // TODO: Replace with real fetch to your /users/register endpoint
    // For example:
    //
    // try {
    //   const resp = await fetch("http://localhost:8000/users/register", {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({ age, gender, occupation, zip_code: zipCode, password }),
    //   });
    //   if (!resp.ok) throw new Error("Registration failed");
    //   const data = await resp.json();
    //   const newId = data.user_id; 
    //   onRegistered(newId);
    // } catch (err: any) {
    //   setError(err.message || "Registration error");
    // }

    // For now, just simulate success with a dummy ID:
    const newId = Math.floor(Math.random() * 10000) + 1000;
    onRegistered(newId);
  };

  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="card shadow-sm" style={{ width: '100%', maxWidth: '600px' }}>
        <div className="card-body">
          <h4 className="card-title text-center mb-4">Create New Account</h4>
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}
          <form onSubmit={handleRegister}>
            <div className="mb-3">
              <label htmlFor="age-input" className="form-label">Age</label>
              <input
                id="age-input"
                type="number"
                className="form-control"
                value={age}
                onChange={(e) => setAge(e.target.value === '' ? '' : Number(e.target.value))}
                placeholder="Enter your age"
              />
            </div>
            <div className="mb-3">
              <label htmlFor="gender-select" className="form-label">Gender</label>
              <select
                id="gender-select"
                className="form-select"
                value={gender}
                onChange={(e) => setGender(e.target.value as 'M' | 'F' | '')}
              >
                <option value="">Choose gender</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </div>
            <div className="mb-3">
              <label htmlFor="occupation-input" className="form-label">Occupation</label>
              <input
                id="occupation-input"
                type="text"
                className="form-control"
                value={occupation}
                onChange={(e) => setOccupation(e.target.value)}
                placeholder="Enter your occupation"
              />
            </div>
            <div className="mb-3">
              <label htmlFor="zip-input" className="form-label">Zip Code</label>
              <input
                id="zip-input"
                type="text"
                className="form-control"
                value={zipCode}
                onChange={(e) => setZipCode(e.target.value)}
                placeholder="Enter your zip code"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="password-input" className="form-label">Password</label>
              <input
                id="password-input"
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Choose a password"
              />
            </div>
            <button type="submit" className="btn btn-success w-100">
              Create Account
            </button>
          </form>
          <hr />
          <button
            className="btn btn-link w-100"
            onClick={onCancel}
          >
            ← Back to Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateAccount;
