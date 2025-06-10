// src/components/AddMovie.tsx
import React, { useEffect, useState } from 'react';

type Genre = { genre_id: number; name: string };

export default function AddMovie() {
  const [title, setTitle] = useState('');
  const [releaseDate, setReleaseDate] = useState('');
  const [imdbUrl, setImdbUrl] = useState('');
  const [genres, setGenres] = useState<Genre[]>([]);
  const [selectedGenres, setSelectedGenres] = useState<number[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  // Load genres on mount
  useEffect(() => {
    fetch('/api/genres', { credentials: 'include' })
      .then((r) => r.json())
      .then(setGenres)
      .catch(console.error);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    try {
      const resp = await fetch('/api/admin/movies', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          release_date: releaseDate,
          genres: selectedGenres
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => null);
        throw new Error(err?.detail || `HTTP ${resp.status}`);
      }
      const { movie_id } = await resp.json();
      console.log(resp);
      setMsg(`Movie #${movie_id} added!`);
      // clear form
      setTitle('');
      setReleaseDate('');
      setSelectedGenres([]);
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    }
  };

  return (
    <div className="pane-container">
      <h5>Add a New Movie</h5>
      {msg && <div className="alert alert-info">{msg}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-2">
          <label>Title</label>
          <input
            className="form-control"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div className="mb-2">
          <label>Release Date</label>
          <input
            type="text"
            className="form-control"
            placeholder="01-Jan-2000"
            value={releaseDate}
            onChange={(e) => setReleaseDate(e.target.value)}
            required
          />
        </div>
        <div className="mb-3">
          <label>Genres</label>
        <div className="mb-3">
        <div className="border rounded p-2" style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {genres.map((g) => (
            <div key={g.genre_id} className="form-check">
                <input
                className="form-check-input"
                type="checkbox"
                id={`genre-${g.genre_id}`}
                checked={selectedGenres.includes(g.genre_id)}
                onChange={(e) => {
                    if (e.target.checked) {
                    setSelectedGenres((prev) => [...prev, g.genre_id]);
                    } else {
                    setSelectedGenres((prev) =>
                        prev.filter((id) => id !== g.genre_id)
                    );
                    }
                }}
                />
                <label className="form-check-label" htmlFor={`genre-${g.genre_id}`}>
                {g.name}
                </label>
            </div>
            ))}
        </div>
        </div>
        </div>
        <button type="submit" className="btn btn-primary">
          Add Movie
        </button>
      </form>
    </div>
  );
}
