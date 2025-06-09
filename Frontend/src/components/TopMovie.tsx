import React, { useState } from 'react';

type TopMovieProps = {
  userId: number;
  alpha: number;
};

const TopMovie: React.FC<TopMovieProps> = ({ userId, alpha }) => {
  const [result, setResult] = useState<{
    movie_id?: number;
    title: string;
    comment: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [selectedRating, setSelectedRating] = useState(1);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

    // dump raw text so we can see what the server actually sent
    const raw = await resp.text();
    console.log('[TopMovie] raw response text:', raw);

    // try to parse it
    let data: any;
    try {
      data = JSON.parse(raw);
    } catch (e) {
      console.error('[TopMovie] JSON.parse error:', e);
      throw new Error('Invalid JSON from server');
    }
    console.log('[TopMovie] parsed JSON:', data);

    // handle both snake_case or camelCase
    const movie_id = data.movie_id ?? data.movieId;
    if (typeof movie_id !== 'number') {
      throw new Error(`Missing or invalid movie_id: ${movie_id}`);
    }

    setResult({
      movie_id,
      title: String(data.title),
      comment: String(data.comment),
    });
  } catch (err: any) {
    console.error('[TopMovie] fetchTop error:', err);
    setResult({ 
      movie_id: undefined, 
      title: 'Error', 
      comment: 'Could not fetch recommendation.' 
    });
  } finally {
    setLoading(false);
  }
};

  const sendRating = async () => {
    console.log('sendRating called with:', selectedRating);
    if (!result?.movie_id) return;
    console.log('Sending rating', selectedRating, 'for', result.movie_id);
    setSending(true);
    setError(null);
    try {
      const resp = await fetch('/api/ratings', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          movie_id: result.movie_id,
          rating: selectedRating
        }),
      });
      console.log('sendRating response:', resp);
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || `HTTP ${resp.status}`);
      }
      setShowModal(false);
      alert('Rating submitted!');
    } catch (err: any) {
      console.error('sendRating error:', err);
      setError(err.message || 'Failed to submit rating');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="pane-container">
      <h5>Top Movie Recommendation</h5>
      <button
        className="btn btn-primary mb-3"
        onClick={fetchTop}
        disabled={loading}
      >
        {loading ? 'Loading…' : 'Get Recommendation'}
      </button>

      {result && (
        <div>
          <h6>{result.title}</h6>
          <p>{result.comment}</p>
          <button
            className="btn btn-outline-secondary"
            onClick={() => setShowModal(true)}
          >
            Rate this movie
          </button>
        </div>
      )}

      {showModal && result && (
        <div className="modal d-block" tabIndex={-1} role="dialog">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Rate “{result.title}”</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowModal(false)}
                />
              </div>
              <div className="modal-body">
                <label className="form-label">Select Rating:</label>
                <select
                  className="form-select"
                  value={selectedRating}
                  onChange={(e) => setSelectedRating(+e.target.value)}
                >
                  {[1,2,3,4,5].map((n) => (
                    <option key={n} value={n}>
                      {n} Star{n>1 && 's'}
                    </option>
                  ))}
                </select>
                {error && <div className="text-danger mt-2">{error}</div>}
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                  disabled={sending}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  onClick={sendRating}
                  disabled={sending}
                >
                  {sending ? 'Sending…' : 'Send Rating'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopMovie;
