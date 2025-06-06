import React from 'react';

type ManualAlphaProps = {
  userId: number;
  alpha: number;
  setAlpha: (a: number) => void;
};

const ManualAlpha: React.FC<ManualAlphaProps> = ({ userId, alpha, setAlpha }) => {
  const [temp, setTemp] = React.useState(alpha.toString());
  const [saving, setSaving] = React.useState(false);

  const handleUpdate = async () => {
    const parsed = parseFloat(temp);
    if (isNaN(parsed) || parsed < 0.0 || parsed > 1.0) {
      alert('Enter a valid number between 0.0 and 1.0.');
      return;
    }

    setSaving(true);
    try {
      // 1) Update local state immediately
      setAlpha(parsed);

      // 2) Persist to backend
      const resp = await fetch(`/api/users/${userId}/alpha`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alpha: parsed }),
      });

      if (!resp.ok) {
        // If backend rejects, revert local state to previous alpha
        setAlpha(alpha);
        const text = await resp.text();
        alert(`Failed to save alpha: ${text}`);
      }
    } catch (err) {
      // On network or other error, revert local state
      setAlpha(alpha);
      console.error('Error while saving alpha:', err);
      alert('Error updating alpha. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pane-container">
      <h5>7. Manually change similarity threshold (alpha)</h5>
      <div className="mb-3">
        <label className="form-label">New alpha (0.0 – 1.0):</label>
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
        onClick={handleUpdate}
        disabled={saving}
      >
        {saving ? 'Saving…' : 'Update Alpha'}
      </button>
      <p className="mt-2">Current alpha: {alpha.toFixed(2)}</p>
    </div>
  );
};

export default ManualAlpha;
