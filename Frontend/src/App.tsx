// src/App.tsx
import React, { useState } from 'react';
import AuthPage from './components/AuthPage';
import Header from './components/Header';
import MainUI from './components/MainUI';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';
import './app.css';

const App: React.FC = () => {
  const [userId, setUserId] = useState<number | null>(null);
  const [alpha, setAlpha] = useState<number>(0.9);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  const handleExit = () => {
    // When Exit is chosen from Header, reset everything so AuthPage re‐appears:
    setUserId(null);
    setAlpha(0.9);
    setSelectedOption(null);
  };

  if (userId === null) {
    return <AuthPage setUserId={setUserId} />;
  }

  return (
    <div className="app-root d-flex flex-column" style={{ height: '100%' }}>
      <Header
        userId={userId}
        alpha={alpha}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
        onExit={handleExit}
      />
      <MainUI
        userId={userId}
        alpha={alpha}
        setUserId={setUserId}
        setAlpha={setAlpha}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
      />
    </div>
  );
};

export default App;
