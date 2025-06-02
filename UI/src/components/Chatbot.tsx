import React, { useState,type KeyboardEvent,type ChangeEvent, useRef, useEffect } from 'react';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState<string>('');
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownOpen &&
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now(),
      text: inputValue,
      sender: 'user',
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // Simulate bot response (replace with real API call as needed)
    setTimeout(() => {
      const botMessage: Message = {
        id: Date.now() + 1,
        text: `You said: ${userMessage.text}`,
        sender: 'bot',
      };
      setMessages(prev => [...prev, botMessage]);
    }, 1000);
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const toggleDropdown = () => {
    setDropdownOpen(prev => !prev);
  };

  return (
    <div className="container-fluid mt-5 d-flex justify-content-center">
      <div className="card shadow-lg rounded" style={{ width: '95%' }}>
        <div className="card-header bg-primary text-white d-flex justify-content-between align-items-center position-relative">
          <h5 className="mb-0">Chatbot</h5>
          <div ref={dropdownRef}>
            <button
              className="btn btn-outline-light"
              type="button"
              onClick={toggleDropdown}
            >
              <i className="bi bi-gear-fill"></i>
            </button>
            <ul
              className="dropdown-menu dropdown-menu-end"
              style={{ display: dropdownOpen ? 'block' : 'none', top: '100%', right: 0, position: 'absolute' }}
            >
              <li><button className="dropdown-item" type="button">Settings</button></li>
              <li><button className="dropdown-item" type="button" onClick={() => setMessages([])}>Clear Chat</button></li>
              <li><button className="dropdown-item" type="button">Help</button></li>
            </ul>
          </div>
        </div>
        <div className="card-body bg-light" style={{ height: '60vh', overflowY: 'auto' }}>
          {messages.length === 0 && (
            <div className="text-center text-muted mt-5">Start the conversation...</div>
          )}
          {messages.map(message => (
            <div
              key={message.id}
              className={`d-flex mb-3 ${message.sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
            >
              <div
                className={`p-3 rounded ${message.sender === 'user' ? 'bg-primary text-white' : 'bg-white text-dark'}`}
                style={{ maxWidth: '75%' }}
              >
                {message.text}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="card-footer bg-white">
          <div className="input-group">
            <input
              type="text"
              className="form-control border-end-0"
              placeholder="Type a message..."
              value={inputValue}
              onChange={handleChange}
              onKeyPress={handleKeyPress}
            />
            <button className="btn btn-primary border-start-0" onClick={handleSend}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;

// Integration in App.tsx:
// import React from 'react';
// import Chatbot from './components/Chatbot';
//
// const App: React.FC = () => {
//   return (
//     <div>
//       <Chatbot />
//     </div>
//   );
// };
//
// export default App;
