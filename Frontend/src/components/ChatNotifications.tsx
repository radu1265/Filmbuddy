// src/components/ChatNotifications.tsx
import React, { useEffect, useState } from 'react';

type Unread = {
  message_id: number;
  from_user_id: number;
  from_username: string;
  text: string;
  ts: string;
};

type Toast = {
  id: number;
  content: string;
};

export const ChatNotifications: React.FC<{ currentUserId: number }> = ({ currentUserId }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = React.useRef(1);

  useEffect(() => {
    let stopped = false;

    const poll = async () => {
      try {
        const resp = await fetch('/api/chats/unread', {credentials: 'include'});
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data: Unread[] = await resp.json();
        if (stopped) return;

        data.forEach((msg) => {
          const id = nextId.current++;
          setToasts((prev) => [
            ...prev,
            { id, content: `${msg.from_username}: ${msg.text}` },
          ]);
          // auto-remove toast after 5s
          setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
          }, 5000);
        });
      } catch (err) {
        console.error('Error polling unread messages:', err);
      }
    };

    // initial fetch + interval
    poll();
    const iv = setInterval(poll, 5000);
    return () => {
      stopped = true;
      clearInterval(iv);
    };
  }, [currentUserId]);

  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="position-fixed top-0 end-0 p-3"
      style={{ zIndex: 1050 }}
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className="toast show mb-2"
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
        >
          <div className="toast-body">{t.content}</div>
        </div>
      ))}
    </div>
  );
};

export default ChatNotifications;