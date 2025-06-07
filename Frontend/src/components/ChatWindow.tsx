// src/components/ChatWindow.tsx
import React, { useEffect, useState, useRef } from 'react';

type Message = {
  from: number;
  to: number;
  text: string;
  ts: string; // ISO timestamp
};

type ChatWindowProps = {
  currentUserId: number;
  peerId: number;
  peerUsername: string;
};

const ChatWindow: React.FC<ChatWindowProps> = ({
  currentUserId,
  peerId,
  peerUsername,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const historyRef = useRef<HTMLDivElement | null>(null);
  const lastTsRef = useRef<string | null>(null);

  // Fetch only if there’s newer content
  const fetchHistory = async () => {
    try {
      const resp = await fetch(`/api/chats/history?peer_id=${peerId}`, {
        credentials: 'include',
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const msgs: Message[] = data.messages;

      const newest = msgs.length ? msgs[msgs.length - 1].ts : null;
      if (newest && newest === lastTsRef.current) {
        return; // no change
      }

      lastTsRef.current = newest;
      setMessages(msgs);

      // scroll to bottom
      setTimeout(() => {
        historyRef.current?.scrollTo({
          top: historyRef.current.scrollHeight,
          behavior: 'smooth',
        });
      }, 50);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  // poll every 3s
  useEffect(() => {
    fetchHistory();
    const id = setInterval(fetchHistory, 3000);
    return () => clearInterval(id);
  }, [currentUserId, peerId]);

  // send message
  const handleSend = async () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setSending(true);
    try {
      const resp = await fetch('/api/chats/send', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_user_id: peerId,
          text: trimmed,
        }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      setText('');
      await fetchHistory();
    } catch (err: any) {
      console.error('Failed to send message:', err);
      alert(`Could not send message:\n${err.message}`);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="pane-container d-flex flex-column" style={{ height: '100%' }}>
      <h5>Chat with {peerUsername}</h5>

      <div
        ref={historyRef}
        className="chat-history border rounded p-2 mb-2 flex-grow-1"
        style={{ overflowY: 'auto', backgroundColor: '#f9f9f9' }}
      >
        {messages.length === 0 ? (
          <div className="text-center text-muted">No messages yet.</div>
        ) : (
          messages.map((m, i) => (
            <div
              key={i}
              className={`d-flex mb-1 ${
                m.from === currentUserId ? 'justify-content-end' : 'justify-content-start'
              }`}
            >
              <div
                className={`p-2 rounded ${
                  m.from === currentUserId ? 'bg-primary text-white' : 'bg-light text-dark'
                }`}
                style={{ maxWidth: '70%' }}
              >
                {m.text}
                <div className="text-end" style={{ fontSize: '0.75rem' }}>
                  {new Date(m.ts).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="chat-input d-flex">
        <input
          type="text"
          className="form-control me-2"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={sending}
          placeholder="Type a message…"
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={sending || !text.trim()}
        >
          {sending ? 'Sending…' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
