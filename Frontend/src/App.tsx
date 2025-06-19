// src/App.tsx
import React, { useState } from 'react';
import AuthPage from './components/AuthPage';
import Header from './components/Header';
import MainUI from './components/MainUI';
import FriendList from './components/FriendList';
import ChatNotifications from './components/ChatNotifications';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';
import './app.css';

const App: React.FC = () => {
  const [username, setUsername] = useState<string>('');
  const [userId, setUserId] = useState<number | null>(null);
  const [alpha, setAlpha] = useState<number>(0.9);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [ratingCount, setRatingCount] = useState<number>(0);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);

  // for FriendList → ChatWindow
  const [peerId, setPeerId] = useState<number | null>(null);
  const [peerUsername, setPeerUsername] = useState<string>('');

  const handleExit = async () => {
    try {
      await fetch('/api/users/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (e) {
      console.error('Logout failed:', e);
    } finally {
      setUserId(null);
      setUsername('');
      setAlpha(0.9);
      setRatingCount(0);
      setSelectedOption(null);
      setPeerId(null);
      setPeerUsername('');
    }
  };

  // when clicking a friend in the sidebar
  const handleChatWith = (fid: number, fun: string) => {
    console.log('handleChatWith:', { fid, fun });
    setPeerId(fid);
    setPeerUsername(fun);
    setSelectedOption(6);
  };

  if (userId === null) {
    return (
      <AuthPage
        setUserId={setUserId}
        setUsername={setUsername}
        setAlpha={setAlpha}
        setIsAdmin={setIsAdmin}

        onLoginComplete={(newUserId: number) => {
          fetch(`/api/users/${newUserId}/rating_count`, {
            credentials: 'include',
          })
            .then((res) => res.json())
            .then((json) => {
              setRatingCount(json.count);
              setSelectedOption(json.count < 5 ? 8 : 1);
            })
            .catch((err) => console.error('Could not fetch rating count:', err));
        }}
      />
    );
  }

  return (
      <div className="row col-12 h-100">
        {/* Main content */}
        <div className="col-9 d-flex flex-column p-0">
          <Header
            username={username}
            isAdmin={isAdmin}
            alpha={alpha}
            selectedOption={selectedOption}
            setSelectedOption={setSelectedOption}
            onExit={handleExit}
            ratingCount={ratingCount}
          />
          <ChatNotifications currentUserId={userId} />
          <MainUI
            userId={userId}
            isAdmin={isAdmin}
            alpha={alpha}
            setAlpha={setAlpha}
            selectedOption={selectedOption}
            setSelectedOption={setSelectedOption}
            ratingCount={ratingCount}
            onRatingCountChange={setRatingCount}
            peerId={peerId}
            peerUsername={peerUsername}
            setPeerId={setPeerId}
            setPeerUsername={setPeerUsername}
          />
        </div>

        {/* Friend list sidebar */}
        <div className="col-3 border-start">
          <FriendList onChatWith={handleChatWith} />
        </div>
      </div>
  );
};

export default App;
