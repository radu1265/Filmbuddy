import React, { useEffect, useState } from 'react';

type Movie = {
  movie_id: number;
  title: string;
};

type RateMovieProps = {
  currentCount: number;
  onCountChange: (newCount: number) => void;
};

const RateMovie: React.FC<RateMovieProps> = ({ currentCount, onCountChange }) => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [selectedMovieId, setSelectedMovieId] = useState<number | ''>('');
  const [rating, setRating] = useState<number | ''>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 1) Fetch unrated movies on mount
  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch('/api/movies/unrated', { credentials: 'include' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data: Movie[] = await resp.json();
        setMovies(data);
      } catch (err: any) {
        console.error('Error fetching movies:', err);
        setError('Could not load movies. Please try again later.');
      }
    })();
  }, []);

  // 2) Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (
      selectedMovieId === '' ||
      rating === '' ||
      !Number.isInteger(rating) ||
      rating < 1 ||
      rating > 5
    ) {
      setError('Please select a movie and a rating between 1 and 5.');
      return;
    }

    try {
      const resp = await fetch('/api/ratings', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movie_id: selectedMovieId,
          rating,
        }),
      });
      if (!resp.ok) {
        const errJson = await resp.json().catch(() => null);
        throw new Error(errJson?.detail || `HTTP ${resp.status}`);
      }
      setSuccess('Rating submitted successfully!');
      onCountChange(currentCount + 1);
      // remove the just-rated movie from the dropdown
      setMovies((m) => m.filter((mv) => mv.movie_id !== selectedMovieId));
      setSelectedMovieId('');
      setRating('');
    } catch (err: any) {
      console.error('Rating error:', err);
      setError(err.message || 'Rating failed. Please try again.');
    }
  };

  return (
    <div className="pane-container">
      <h5>Rate a Movie</h5>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit}>
        {/* Movie selector */}
        <div className="mb-3">
          <label htmlFor="movie-select" className="form-label">Movie</label>
          <select
            id="movie-select"
            className="form-select"
            value={selectedMovieId}
            onChange={(e) =>
              setSelectedMovieId(e.target.value === '' ? '' : Number(e.target.value))
            }
          >
            <option value="">— Select a movie —</option>
            {movies.map((m) => (
              <option key={m.movie_id} value={m.movie_id}>
                {m.title}
              </option>
            ))}
          </select>
        </div>

        {/* Rating selector */}
        <div className="mb-3">
          <label htmlFor="rating-select" className="form-label">Your Rating</label>
          <select
            id="rating-select"
            className="form-select"
            value={rating}
            onChange={(e) =>
              setRating(e.target.value === '' ? '' : Number(e.target.value))
            }
          >
            <option value="">— Choose 1 to 5 —</option>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n} Star{n > 1 && 's'}
              </option>
            ))}
          </select>
        </div>

        <button type="submit" className="btn btn-primary">
          Submit Rating
        </button>
      </form>
    </div>
  );
};

export default RateMovie;
