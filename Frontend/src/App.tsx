// src/App.tsx
import React, { useState } from 'react';
import AuthPage from './components/AuthPage';
import Header from './components/Header';
import MainUI from './components/MainUI';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';
import './app.css';

const App: React.FC = () => {
  const [username, setUsername] = useState<string>('');
  const [userId, setUserId] = useState<number | null>(null);
  const [alpha, setAlpha] = useState<number>(0.9);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [ratingCount, setRatingCount] = useState<number>(0);
  



  const handleExit = () => {
    // When Exit is chosen from Header, reset everything so AuthPage re‐appears:
    setUsername('');
    setUserId(null);
    setAlpha(0.9);
    setSelectedOption(null);
  };

  if (userId === null) {
    return (
      <AuthPage
        setUserId={setUserId}
        setUsername={setUsername}
        setAlpha={setAlpha}
        onLoginComplete={(newUserId: number) => {
          // After login, fetch their rating count and possibly redirect to RateMovie
          fetch(`/api/users/${newUserId}/rating_count`)
            .then((res) => res.json())
            .then((json) => {
              setRatingCount(json.count);
              if (json.count < 5) {
                setSelectedOption(8); // Force “Rate a movie” if under 5 ratings
              } else {
                setSelectedOption(1); // Or whatever default you prefer
              }
            })
            .catch((err) => console.error('Could not fetch rating count:', err));
        }}
      />
    );
  }

  return (
    <div className="app-root d-flex flex-column" style={{ height: '100%' }}>
      <Header
        username={username}
        alpha={alpha}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
        onExit={handleExit}
        ratingCount={ratingCount}
      />
      <MainUI
        userId={userId!}
        alpha={alpha}
        setUserId={setUserId}
        setAlpha={setAlpha}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
        ratingCount={ratingCount}
        onRatingCountChange={setRatingCount}
      />
    </div>
  );
};

export default App;
