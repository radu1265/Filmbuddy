// src/components/FriendList.tsx
import React, { useEffect, useState, useRef } from 'react';

type Friend = { user_id: number; username: string };
type IncomingRequest = { request_id: number; from_user_id: number; from_username: string };
type OutgoingRequest = { request_id: number; to_user_id: number; to_username: string };

interface FriendListProps {
  onChatWith: (friendId: number, friendUsername: string) => void;
}

const FriendList: React.FC<FriendListProps> = ({ onChatWith }) => {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [incoming, setIncoming] = useState<IncomingRequest[]>([]);
  const [outgoing, setOutgoing] = useState<OutgoingRequest[]>([]);
  const [loading, setLoading] = useState(false);

  // previous friends snapshot for diff
  const prevFriendsRef = useRef<Friend[]>([]);

  // modal state for add
  const [showModal, setShowModal] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [modalError, setModalError] = useState('');

  // reload data
  const reloadAll = () => {
    // fetch friends and diff
    fetch('/api/users/friends', { credentials: 'include' })
      .then((r) => r.json())
      .then((newFriends: Friend[]) => {
        const old = prevFriendsRef.current;
        // detect additions
        const added = newFriends.filter(
          (f) => !old.some((o) => o.user_id === f.user_id)
        );
        // detect removals
        const removed = old.filter(
          (o) => !newFriends.some((f) => f.user_id === o.user_id)
        );
        if (added.length > 0 || removed.length > 0) {
          setFriends(newFriends);
          prevFriendsRef.current = newFriends;
          added.forEach((f) => alert(`Friend added: ${f.username}`));
          removed.forEach((f) => alert(`Friend removed: ${f.username}`));
        }
      })
      .catch(console.error);

    // incoming requests
    fetch('/api/users/friend_requests', { credentials: 'include' })
      .then((r) => r.json())
      .then(setIncoming)
      .catch(console.error);

    // outgoing requests
    fetch('/api/users/friend_requests/outgoing', { credentials: 'include' })
      .then((r) => r.json())
      .then(setOutgoing)
      .catch(console.error);
  };

  useEffect(() => {
    setLoading(true);
    // initial load: set friends without alerts
    fetch('/api/users/friends', { credentials: 'include' })
      .then((r) => r.json())
      .then((initial: Friend[]) => {
        setFriends(initial);
        prevFriendsRef.current = initial;
      })
      .catch(console.error)
      .finally(() => setLoading(false));
    // load requests
    reloadAll();
    const iv = setInterval(reloadAll, 5000);
    return () => clearInterval(iv);
  }, []);

  const sendRequest = () => {
    setModalError('');
    fetch('/api/users/friend_requests', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ friend_username: newUsername.trim() }),
    })
      .then((r) => (r.ok ? reloadAll() : r.json().then((j) => Promise.reject(j.detail))))
      .then(() => {
        setShowModal(false);
        setNewUsername('');
      })
      .catch((err) => setModalError(String(err)));
  };

  const respond = (reqId: number, accept: boolean) => {
    fetch(`/api/users/friend_requests/${reqId}/respond`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accept }),
    })
      .then((r) => (r.ok ? reloadAll() : r.json().then((j) => Promise.reject(j.detail))))
      .catch(console.error);
  };

  const deleteFriend = (fid: number, fun: string) => {
    if (!window.confirm(`Do you want to delete user: ${fun}?`)) return;
    fetch(`/api/users/friends/${fid}`, {
      method: 'DELETE',
      credentials: 'include',
    })
      .then((r) => (r.ok ? reloadAll() : Promise.reject('Failed to delete')))
      .catch((err) => console.error('Could not delete friend:', err));
  };

  if (loading) return <div>Loading friends…</div>;

  return (
    <div className="card h-100 m-2">
      <div className="card-header d-flex justify-content-between align-items-center">
        <strong>Friends</strong>
        <button
          className="btn btn-sm btn-outline-primary"
          onClick={() => setShowModal(true)}
        >
          + Add
        </button>
      </div>

      <ul className="list-group list-group-flush flex-grow-1 overflow-auto">
        {friends.map((f) => (
          <li
            key={f.user_id}
            className="d-flex justify-content-between align-items-center list-group-item"
          >
            <span
              className="list-group-item-action"
              style={{ cursor: 'pointer' }}
              onClick={() => onChatWith(f.user_id, f.username)}
            >
              {f.username}
            </span>
            <button
              className="btn btn-sm btn-outline-danger"
              onClick={() => deleteFriend(f.user_id, f.username)}
            >
              🗑
            </button>
          </li>
        ))}
      </ul>

      {outgoing.length > 0 && (
        <div className="card-footer bg-light">
          <strong>Requests Sent:</strong>
          {outgoing.map((rq) => (
            <div key={rq.request_id} className="mt-2">
              {rq.to_username} (pending)
            </div>
          ))}
        </div>
      )}

      {incoming.length > 0 && (
        <div className="card-footer bg-light">
          <strong>Requests Received:</strong>
          {incoming.map((rq) => (
            <div
              key={rq.request_id}
              className="d-flex justify-content-between align-items-center mt-2"
            >
              <span>{rq.from_username}</span>
              <div>
                <button
                  className="btn btn-sm btn-success me-1"
                  onClick={() => respond(rq.request_id, true)}
                >
                  ✓
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => respond(rq.request_id, false)}
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal d-block" tabIndex={-1} role="dialog">
          <div className="modal-dialog" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Add a Friend</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowModal(false)}
                />
              </div>
              <div className="modal-body">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Enter username"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                />
                {modalError && <div className="text-danger mt-2">{modalError}</div>}
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={sendRequest}>
                  Send Request
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FriendList;
