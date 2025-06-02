// src/components/MainUI.tsx
import React, { useState, useRef, useEffect } from 'react';
// import { FaCog } from 'react-icons/fa';
import { Chatbot } from './Chatbot';
import '../app.css';
import '../images/menu-button.png'

type MenuOption = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export const MainUI: React.FC = () => {
  // userId is null until the user types it in the initial prompt
  const [userId, setUserId] = useState<number | null>(null);
  const [tempUserId, setTempUserId] = useState<string>('');

  const [alpha, setAlpha] = useState<number>(0.8);
  const [selectedOption, setSelectedOption] = useState<MenuOption | null>(null);

  // Dropdown state
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle the “Exit” option: reset everything
  useEffect(() => {
    if (selectedOption === 8) {
      setUserId(null);
      setTempUserId('');
      setAlpha(0.8);
      setSelectedOption(null);
    }
  }, [selectedOption]);

  // If userId is still null, render an initial prompt
  if (userId === null) {
    return (
      <div className="userid-prompt-container">
        <div className="userid-prompt-box">
          <h3 className="mb-3">Welcome to FilmBuddy</h3>
          <label htmlFor="userid-input" className="form-label">
            Please enter your User ID (1 – 1000):
          </label>
          <input
            id="userid-input"
            type="number"
            className="form-control mb-3"
            min={1}
            max={1000}
            value={tempUserId}
            onChange={(e) => setTempUserId(e.target.value)}
            placeholder="e.g. 42"
            
          />
          <button
            className="btn btn-primary"
            onClick={() => {
              const parsed = parseInt(tempUserId || '', 10);
              if (!isNaN(parsed) && parsed >= 1 && parsed <= 1000) {
                setUserId(parsed);
              } else {
                alert('Enter a valid integer between 1 and 1000.');
              }
            }}
          >
            Submit
          </button>
        </div>
      </div>
    );
  }

  // Once userId is set, show the main menu + content
  return (
    <div className="mainui-container d-flex flex-column">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center px-4 py-2 header-bar">
        <div className="dropdown" ref={dropdownRef}>
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={() => setDropdownOpen((p) => !p)}
            aria-expanded={dropdownOpen}
          >
            <img src="src/images/menu-button.png" alt="Menu" style={{ width: '24px', height: '24px' }} />
          </button>
          {dropdownOpen && (
            <ul className="dropdown-menu dropdown-menu-end show">
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setSelectedOption(1);
                    setDropdownOpen(false);
                  }}
                >
                  1. Top movie recommendation
                </button>
              </li>
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setSelectedOption(2);
                    setDropdownOpen(false);
                  }}
                >
                  2. Top-rated movies list
                </button>
              </li>
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setSelectedOption(3);
                    setDropdownOpen(false);
                  }}
                >
                  3. Talk about specific movie
                </button>
              </li>
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setSelectedOption(4);
                    setDropdownOpen(false);
                  }}
                >
                  4. Personalize (adjust alpha)
                </button>
              </li>
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setSelectedOption(5);
                    setDropdownOpen(false);
                  }}
                >
                  5. Chat with assistant
                </button>
              </li>
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setSelectedOption(6);
                    setDropdownOpen(false);
                  }}
                >
                  6. Change user ID
                </button>
              </li>
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setSelectedOption(7);
                    setDropdownOpen(false);
                  }}
                >
                  7. Manually change alpha
                </button>
              </li>
              <li><hr className="dropdown-divider" /></li>
              <li>
                <button
                  className="dropdown-item text-danger"
                  onClick={() => {
                    setSelectedOption(8);
                    setDropdownOpen(false);
                  }}
                >
                  8. Exit
                </button>
              </li>
            </ul>
          )}
        </div>
        <div>
          <span className="me-3"><strong>User ID:</strong> {userId}</span>
          <span><strong>Alpha:</strong> {alpha.toFixed(2)}</span>
        </div>
      </div>

      {/* Content area: grows to fill all remaining height */}
      <div className="flex-grow-1 overflow-auto content-area px-4 py-3">
        {!selectedOption && (
          <div className="alert alert-secondary text-center">
            Choose an option from the <strong>Menu</strong> above to begin.
          </div>
        )}

        {selectedOption === 1 && <TopMovie userId={userId} alpha={alpha} />}
        {selectedOption === 2 && <TopList userId={userId} alpha={alpha} />}
        {selectedOption === 3 && <TalkSpecificMovie />}
        {selectedOption === 4 && <AdjustEmotion alpha={alpha} setAlpha={setAlpha} />}
        {selectedOption === 5 && <Chatbot />}
        {selectedOption === 6 && <ChangeUserId setUserId={setUserId} />}
        {selectedOption === 7 && <ManualAlpha alpha={alpha} setAlpha={setAlpha} />}
        {selectedOption === 8 && (
          <div className="alert alert-warning text-center">
            All state has been reset. The app will now ask for a new User ID.
          </div>
        )}
      </div>
    </div>
  );
};




/* Sub-components below: */

const TopMovie: React.FC<{
  userId: number;
  alpha: number;
}> = ({ userId, alpha }) => {
  const [result, setResult] = useState<{ title: string; comment: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchTop = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/recommend/top', {
        method: 'POST',
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
      <button
        className="btn btn-primary mb-3"
        onClick={fetchTop}
        disabled={loading}
      >
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
  const [n, setN] = useState(5);
  const [results, setResults] = useState<Array<{ title: string; hybrid_score: number }>>([]);
  const [loading, setLoading] = useState(false);

  const fetchList = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/recommend/top_list', {
        method: 'POST',
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
      <button
        className="btn btn-primary mb-3"
        onClick={fetchList}
        disabled={loading}
      >
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
  const [movieName, setMovieName] = useState('');
  const [history, setHistory] = useState<Array<{ role: string; content: string }>>([]);
  const [chatting, setChatting] = useState(false);

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
  const [text, setText] = useState('');
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

const AdjustEmotion: React.FC<{ alpha: number; setAlpha: (a: number) => void }> = ({
  alpha,
  setAlpha,
}) => {
  const [feedback, setFeedback] = useState('');
  const [result, setResult] = useState<{ interpreted: number; adjusted: number } | null>(null);
  const [loading, setLoading] = useState(false);

  const submitEmotion = async () => {
    if (!feedback.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch('/api/emotion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_text: feedback, alpha }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setResult({ interpreted: data.alpha_interpreted, adjusted: data.alpha_adjusted });
      setAlpha(data.alpha_adjusted);
    } catch {
      // ignore
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
      <button className="btn btn-primary mb-3" onClick={submitEmotion} disabled={loading}>
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

const ChangeUserId: React.FC<{ setUserId: (id: number) => void }> = ({ setUserId }) => {
  const [temp, setTemp] = useState('');
  return (
    <div className="pane-container">
      <h5>6. Change user ID</h5>
      <div className="mb-3">
        <label className="form-label">New User ID (1–1000):</label>
        <input
          type="number"
          className="form-control"
          min={1}
          max={1000}
          value={temp}
          onChange={(e) => setTemp(e.target.value)}
        />
      </div>
      <button
        className="btn btn-primary"
        onClick={() => {
          const parsed = parseInt(temp || '0', 10);
          if (parsed >= 1 && parsed <= 1000) {
            setUserId(parsed);
            setTemp('');
          } else {
            alert('Enter a valid ID between 1 and 1000.');
          }
        }}
      >
        Update User ID
      </button>
    </div>
  );
};

const ManualAlpha: React.FC<{ alpha: number; setAlpha: (a: number) => void }> = ({
  alpha,
  setAlpha,
}) => {
  const [temp, setTemp] = useState(alpha.toString());
  return (
    <div className="pane-container">
      <h5>7. Manually change similarity threshold (alpha)</h5>
      <div className="mb-3">
        <label className="form-label">New alpha (0.0–1.0):</label>
        <input
          type="number"
          step="0.01"
          min={0}
          max={1}
          className="form-control"
          value={temp}
          onChange={(e) => setTemp(e.target.value)}
        />
      </div>
      <button
        className="btn btn-primary"
        onClick={() => {
          const parsed = parseFloat(temp);
          if (!isNaN(parsed) && parsed >= 0.0 && parsed <= 1.0) {
            setAlpha(parsed);
          } else {
            alert('Enter a valid number between 0.0 and 1.0.');
          }
        }}
      >
        Update Alpha
      </button>
      <p className="mt-2">Current alpha: {alpha.toFixed(2)}</p>
    </div>
  );
};

export default MainUI;