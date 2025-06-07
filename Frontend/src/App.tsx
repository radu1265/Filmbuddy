// src/App.tsx
import React, { useState } from 'react';
import AuthPage from './components/AuthPage';
import Header from './components/Header';
import MainUI from './components/MainUI';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';
import './app.css';
import ChatNotifications from './components/ChatNotifications';

const App: React.FC = () => {
  const [username, setUsername] = useState<string>('');
  const [userId, setUserId] = useState<number | null>(null);
  const [alpha, setAlpha] = useState<number>(0.9);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [ratingCount, setRatingCount] = useState<number>(0);
  



  const handleExit = async () => {
      try {
        // 1) hit your logout endpoint to delete the cookie
        await fetch('/api/users/logout', {
          method: 'POST',
          credentials: 'include',
        });
      } catch (e) {
        console.error('Logout failed:', e);
      } finally {
        // 2) clear all local state
        setUserId(null);
        setUsername('');
        setAlpha(0.9);
        setRatingCount(0);
        setSelectedOption(null);
      }
    };
  if (userId === null) {
    return (
      <AuthPage
        setUserId={setUserId}
        setUsername={setUsername}
        setAlpha={setAlpha}
        onLoginComplete={(newUserId: number) => {
          // After login, fetch their rating count and possibly redirect to RateMovie
          fetch(`/api/users/${newUserId}/rating_count`, {credentials: 'include'})
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
      <ChatNotifications currentUserId={userId} />
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
