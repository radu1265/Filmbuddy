import React from 'react';

type AdjustEmotionProps = {
  userId: number;
  alpha: number;
  setAlpha: (a: number) => void;
};

const AdjustEmotion: React.FC<AdjustEmotionProps> = ({ userId, alpha, setAlpha }) => {
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

      // 2) Persist newAlpha to your /users/{user_id}/alpha endpoint
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

export default AdjustEmotion;
