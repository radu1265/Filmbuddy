// src/components/MainUI.tsx
import React, { useState } from 'react';
import { Chatbot } from './Chatbot';
import '../app.css';
import RateMovie from './RateMovie';
import ManualAlpha from './ManualAlpha';
import ChatWindow from './ChatWindow';

type MainUIProps = {
  userId: number;
  alpha: number;
  setUserId: (id: number) => void;
  setAlpha: (a: number) => void;
  selectedOption: number | null;
  setSelectedOption: (opt: number | null) => void;
  ratingCount: number;
  onRatingCountChange: (newCount: number) => void;
};

const MainUI: React.FC<MainUIProps> = ({
  userId,
  alpha,
  setUserId,
  setAlpha,
  selectedOption,
  setSelectedOption,
  ratingCount,
  onRatingCountChange,
}) => {
  // Prevent access to recommendation screens if fewer than 5 ratings
  const requireFiveRatings = (): boolean => {
    if (ratingCount < 5) {
      alert(`You must rate at least 5 movies first.\n(You've rated ${ratingCount}.)`);
      // Force them into the “Rate a Movie” pane:
      setSelectedOption(8);
      return true;
    }
    return false;
  };

  const [peerUsernameInput, setPeerUsernameInput] = useState<string>('');
  const [peerId, setPeerId]                       = useState<number | null>(null);
  const [peerUsername, setPeerUsername]           = useState<string>('');

  // const handleStartChat = () => {
  //   const pid = parseInt(peerIdInput.trim() || '0', 10);
  //   if (!Number.isInteger(pid) || pid <= 0) {
  //     alert('Enter a valid peer user ID (positive integer).');
  //     return;
  //   }
  //   if (pid === userId) {
  //     alert("You can't chat with yourself.");
  //     return;
  //   }
  //   setPeerId(pid);
  // };

  return (
    <div className="flex-grow-1 overflow-auto content-area px-4 py-3">
      {!selectedOption && (
        <div className="alert alert-secondary text-center">
          Choose an option from the <strong>Menu</strong> above to begin.
        </div>
      )}

      {/* 1. Top movie recommendation (requires ≥ 5 ratings) */}
      {selectedOption === 1 && !requireFiveRatings() && (
        <TopMovie userId={userId} alpha={alpha} />
      )}

      {/* 2. Top-rated movies list (requires ≥ 5 ratings) */}
      {selectedOption === 2 && !requireFiveRatings() && (
        <TopList userId={userId} alpha={alpha} />
      )}

      {/* 3. Talk about a specific movie */}
      {selectedOption === 3 && <TalkSpecificMovie />}

      {/* 4. Personalize (adjust alpha) */}
      {selectedOption === 4 && (
        <AdjustEmotion userId={userId} alpha={alpha} setAlpha={setAlpha} />
      )}

      {/* 5. Chat with assistant */}
      {selectedOption === 5 && <Chatbot />}

      {/* 6. Chat with another user (polling‐based) */}
      {selectedOption === 6 && (
        <div className="pane-container">
          <h5>6. Chat with a user</h5>

          {!peerId ? (
            <>
              <p>Enter the <strong>username</strong> of the person you want to chat with:</p>
              <div className="d-flex mb-3" style={{ maxWidth: '300px' }}>
                <input
                  type="text"
                  className="form-control me-2"
                  placeholder="Peer username"
                  value={peerUsernameInput}
                  onChange={(e) => setPeerUsernameInput(e.target.value)}
                />
                <button className="btn btn-primary" onClick={async () => {
                  const name = peerUsernameInput.trim();
                  if (!name) {
                    alert('Please enter a username.');
                    return;
                  }
                  try {
                    const resp = await fetch(`/api/users/by-username/${encodeURIComponent(name)}`, {credentials: 'include'});
                    if (!resp.ok) {
                      const err = await resp.json();
                      throw new Error(err.detail || `HTTP ${resp.status}`);
                    }
                    const data = await resp.json();
                    setPeerId(data.user_id);
                    setPeerUsername(name);
                  } catch (err: any) {
                    alert(`Could not find user:\n${err.message}`);
                  }
                }}>
                  Start
                </button>
              </div>
            </>
          ) : (
            <>
              <button
                className="btn btn-secondary mb-2"
                onClick={() => {
                  setPeerId(null);
                  setPeerUsernameInput('');
                }}
              >
                Change Chat
              </button>
                  {peerId && (
                    <ChatWindow
                      currentUserId={userId}
                      peerId={peerId}
                      peerUsername={peerUsername}
                    />
                  )}
            </>
          )}
        </div>
      )}

      {/* 7. Manually change alpha (now persists to backend) */}
      {selectedOption === 7 && (
        <ManualAlpha userId={userId} alpha={alpha} setAlpha={setAlpha} />
      )}

      {/* 8. Rate a movie */}
      {selectedOption === 8 && (
        <RateMovie
          userId={userId}
          currentCount={ratingCount}
          onCountChange={onRatingCountChange}
        />
      )}

      {/* 9. Exit/reset message */}
      {selectedOption === 9 && (
        <div className="alert alert-warning text-center">
          All state has been reset. The app will now ask for a new User ID.
        </div>
      )}
    </div>
  );
};

export default MainUI;

/* ————————————————
   Sub‐components (same as before, just copied in)
   ———————————————— */

const TopMovie: React.FC<{
  userId: number;
  alpha: number;
}> = ({ userId, alpha }) => {
  const [result, setResult] = React.useState<{ title: string; comment: string } | null>(null);
  const [loading, setLoading] = React.useState(false);

  const fetchTop = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/recommend/top', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, alpha }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json(); // { title, comment }
      setResult({ title: data.title, comment: data.comment });
    } catch {
      setResult({ title: 'Error', comment: 'Could not fetch recommendation.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pane-container">
      <h5>1. Get top movie recommendation</h5>
      <p>
        <strong>User ID:</strong> {userId} | <strong>Alpha:</strong> {alpha.toFixed(2)}
      </p>
      <button className="btn btn-primary mb-3" onClick={fetchTop} disabled={loading}>
        {loading ? 'Loading…' : 'Get Recommendation'}
      </button>
      {result && (
        <div className="mt-3">
          <h6>Title: {result.title}</h6>
          <p>{result.comment}</p>
        </div>
      )}
    </div>
  );
};

const TopList: React.FC<{
  userId: number;
  alpha: number;
}> = ({ userId, alpha }) => {
  const [n, setN] = React.useState(5);
  const [results, setResults] = React.useState<Array<{ title: string; hybrid_score: number }>>([]);
  const [loading, setLoading] = React.useState(false);

  const fetchList = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/recommend/top_list', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, alpha, n }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json(); // { movies: [...] }
      setResults(data.movies.slice(0, n));
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pane-container">
      <h5>2. Get list of top-rated movies</h5>
      <p>
        <strong>User ID:</strong> {userId} | <strong>Alpha:</strong> {alpha.toFixed(2)}
      </p>
      <div className="mb-3">
        <label className="form-label">Number of movies:</label>
        <input
          type="number"
          className="form-control"
          style={{ width: '5rem' }}
          min={1}
          max={20}
          value={n}
          onChange={(e) => setN(parseInt(e.target.value || '5', 10))}
        />
      </div>
      <button className="btn btn-primary mb-3" onClick={fetchList} disabled={loading}>
        {loading ? 'Loading…' : `Get Top ${n}`}
      </button>
      {results.length > 0 && (
        <ul className="list-group">
          {results.map((row, idx) => (
            <li key={idx} className="list-group-item">
              {idx + 1}. <strong>{row.title}</strong> (Score: {row.hybrid_score.toFixed(2)})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

const TalkSpecificMovie: React.FC = () => {
  const [movieName, setMovieName] = React.useState('');
  const [history, setHistory] = React.useState<Array<{ role: string; content: string }>>([]);
  const [chatting, setChatting] = React.useState(false);

  const startDiscussion = () => {
    if (!movieName.trim()) return;
    const initial: Array<{ role: string; content: string }> = [
      { role: 'system', content: 'You are a movie expert assistant.' },
      { role: 'user', content: `Let's talk about ${movieName}.` },
    ];
    setHistory(initial);
    setChatting(true);
  };

  const sendMsg = async (msg: string) => {
    const newHistory = [...history, { role: 'user', content: msg }];
    setHistory(newHistory);
    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: newHistory }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setHistory((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch {
      setHistory((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: could not get response.' },
      ]);
    }
  };

  return (
    <div className="pane-container">
      <h5>3. Talk about a specific movie</h5>
      {!chatting ? (
        <>
          <div className="mb-3">
            <label className="form-label">Movie name:</label>
            <input
              type="text"
              className="form-control"
              value={movieName}
              onChange={(e) => setMovieName(e.target.value)}
              placeholder="e.g. The Godfather"
            />
          </div>
          <button className="btn btn-primary" onClick={startDiscussion}>
            Start Discussion
          </button>
        </>
      ) : (
        <div className="chat-section">
          <div className="chat-messages mb-2">
            {history.map((msg, idx) => (
              <div
                key={idx}
                className={`message-bubble mb-2 ${
                  msg.role === 'user'
                    ? 'user-bubble'
                    : msg.role === 'assistant'
                    ? 'bot-bubble'
                    : 'system-bubble'
                }`}
              >
                {msg.content}
              </div>
            ))}
          </div>
          <MovieChatInput onSend={sendMsg} />
        </div>
      )}
    </div>
  );
};

const MovieChatInput: React.FC<{ onSend: (msg: string) => void }> = ({ onSend }) => {
  const [text, setText] = React.useState('');
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (text.trim()) {
        onSend(text.trim());
        setText('');
      }
    }
  };
  return (
    <div className="d-flex">
      <textarea
        className="form-control me-2"
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about this movie…"
      />
      <button
        className="btn btn-secondary"
        onClick={() => {
          if (text.trim()) {
            onSend(text.trim());
            setText('');
          }
        }}
      >
        Send
      </button>
    </div>
  );
};

const AdjustEmotion: React.FC<{
  userId: number;
  alpha: number;
  setAlpha: (a: number) => void;
}> = ({ userId, alpha, setAlpha }) => {
  const [feedback, setFeedback] = React.useState('');
  const [result, setResult] = React.useState<{
    interpreted: number;
    adjusted: number;
  } | null>(null);
  const [loading, setLoading] = React.useState(false);

  const submitEmotion = async () => {
    if (!feedback.trim()) return;
    setLoading(true);
    try {
      // 1) Call your emotion‐interpretation endpoint
      const resp = await fetch('/api/emotion', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_text: feedback, alpha }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const newAlpha = data.alpha_adjusted;
      setResult({
        interpreted: data.alpha_interpreted,
        adjusted: newAlpha,
      });
      setAlpha(newAlpha);

      // 2) Persist newAlpha to your /users/{userId}/alpha endpoint
      const resp2 = await fetch(`/api/users/${userId}/alpha`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alpha: newAlpha }),
      });
      if (!resp2.ok) {
        console.error('Failed to persist alpha:', await resp2.text());
      }
    } catch (err) {
      console.error('Error adjusting emotion:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pane-container">
      <h5>4. Personalize (adjust alpha)</h5>
      <p>Current alpha: {alpha.toFixed(2)}</p>
      <div className="mb-3">
        <label className="form-label">How do you feel about these recs?</label>
        <textarea
          className="form-control"
          rows={2}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="e.g. I loved that last movie!"
        />
      </div>
      <button
        className="btn btn-primary mb-3"
        onClick={submitEmotion}
        disabled={loading}
      >
        {loading ? 'Interpreting…' : 'Submit Feedback'}
      </button>
      {result && (
        <div>
          <p>
            Interpreted: {result.interpreted.toFixed(2)} | Adjusted alpha:{' '}
            {result.adjusted.toFixed(2)}
          </p>
        </div>
      )}
    </div>
  );
};

