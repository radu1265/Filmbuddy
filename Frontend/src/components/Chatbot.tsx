// src/components/Chatbot.tsx
import React, { useState, useRef, useEffect } from 'react';
// import { FaCog } from 'react-icons/fa'; // optional: for a gear icon in the dropdown
import '../app.css';

type Message = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export const Chatbot: React.FC = () => {
  // Chat history: start with a system prompt
  const [history, setHistory] = useState<Message[]>([
    { role: 'system', content: 'You are a helpful assistant.' },
  ]);

  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  // Dropdown state
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when history changes
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  // Close dropdown if clicked outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleDropdown = () => {
    setDropdownOpen((prev) => !prev);
  };

  const handleClearChat = () => {
    setHistory([{ role: 'system', content: 'You are a helpful assistant.' }]);
    setDropdownOpen(false);
  };

  const handleHelp = () => {
    alert('Type your message and press Enter or click Send. The bot will reply.');
    setDropdownOpen(false);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    setHistory((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: [...history, userMsg] }),
      });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const data = await resp.json(); // { reply: string }
      const botMsg: Message = { role: 'assistant', content: data.reply };
      setHistory((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error('Error:', err);
      const errMsg: Message = {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
      };
      setHistory((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chatbot-container mx-auto p-3 shadow-lg rounded">
      {/* Header with dropdown */}
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h5 className="m-0">FilmBuddy Chat</h5>
        <div className="dropdown" ref={dropdownRef}>
          <button
            className="btn btn-light btn-sm"
            onClick={toggleDropdown}
            aria-expanded={dropdownOpen}
          >
            {/* <FaCog /> */}
          </button>
          {dropdownOpen && (
            <ul className="dropdown-menu dropdown-menu-end show">
              <li>
                <button className="dropdown-item" onClick={handleHelp}>
                  Help
                </button>
              </li>
              <li>
                <button className="dropdown-item" onClick={handleClearChat}>
                  Clear Chat
                </button>
              </li>
              {/* You can add more menu items here */}
            </ul>
          )}
        </div>
      </div>

      {/* Chat messages */}
      <div
        className="chat-messages mb-2 p-2 bg-white rounded"
        ref={scrollRef}
      >
        {history.map((msg, idx) => (
          <div
            key={idx}
            className={`message-bubble mb-2 ${
              msg.role === 'user' ? 'user-bubble' : msg.role === 'assistant' ? 'bot-bubble' : 'system-bubble'
            }`}
          >
            {msg.content}
          </div>
        ))}
      </div>

      {/* Input area */}
      <div className="d-flex">
        <textarea
          className="form-control me-2"
          rows={1}
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sending}
        />
        <button
          className="btn btn-primary"
          onClick={sendMessage}
          disabled={sending || !input.trim()}
        >
          {sending ? 'Sending…' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default Chatbot;