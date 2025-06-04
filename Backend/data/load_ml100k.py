"""
load_ml100k.py

This script:
  1. Connects to the local PostgreSQL movielens database as movies_user.
  2. Populates genres, users, movies, movie_genres, and ratings from the raw ML-100k files.
"""

import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# ────────────────────────────────────────────────────────────────────────────────
# Adjust these two variables if your ML-100k folder is somewhere else:
ML100K_DIR = os.path.expanduser("~/Downloads/ml-100k")
DB_NAME    = "movielens"
DB_USER    = "movies_user"
DB_PASS    = os.getenv("PASSWORD")       # ← replace with whatever password you chose
DB_HOST    = "localhost"
DB_PORT    = 5432
# ────────────────────────────────────────────────────────────────────────────────

def connect_db():
    """Return a psycopg2 connection to our movielens DB."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = False
    return conn

def load_genres(cur):
    """
    Read u.genre (format: genre_name|genre_id) and insert into genres(name).
    We only care about the name; the genre_id in u.genre is not strictly needed
    (PostgreSQL will assign its own genre_id SERIAL). We'll ignore lines without a pipe.
    """
    filepath = os.path.join(ML100K_DIR, "u.genre")
    print(f"Loading genres from {filepath} ...")
    with open(filepath, "r", encoding="latin-1") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            genre_name, _ = line.split("|", 1)
            if genre_name:
                cur.execute(
                    "INSERT INTO genres (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;",
                    (genre_name,)
                )

def load_users(cur):
    """
    Read u.user (format: user_id|age|gender|occupation|zip_code).
    Since our users table has user_id SERIAL, we override it by specifying the column list.
    After inserting all 943 users, we must set the SERIAL sequence to start at 944.
    """
    filepath = os.path.join(ML100K_DIR, "u.user")
    print(f"Loading users from {filepath} ...")
    with open(filepath, "r", encoding="latin-1") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            user_id, age, gender, occupation, zip_code = line.split("|")
            cur.execute(
                """
                INSERT INTO users (user_id, age, gender, occupation, zip_code)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (int(user_id), int(age), gender, occupation, zip_code)
            )

    # Reset the users_user_id_seq so that future new users start at 944:
    cur.execute("SELECT MAX(user_id) FROM users;")
    max_uid = cur.fetchone()[0] or 0
    next_seq = max_uid + 1
    cur.execute(
        f"ALTER SEQUENCE users_user_id_seq RESTART WITH {next_seq};"
    )

def load_movies_and_movie_genres(cur):
    """
    Read u.item (format:
       movie_id|title|release_date|video_release_date|IMDb_URL|19 genre_flags...
    )
    We:
      (a) Insert into movies (movie_id, title, release_date)
      (b) For each of the 19 genre_flags that =1, we look up the genre_id by
          matching the column index to the genre name read earlier. Then insert
          (movie_id, genre_id) into movie_genres.
    """
    # 1. Build a list of (genre_id, genre_name) in order of their appearance in u.genre.
    cur.execute("SELECT genre_id, name FROM genres ORDER BY genre_id;")
    genre_rows = cur.fetchall()
    # We assume genre_rows are in the same "order" as u.genre's lines.
    # (MovieLens u.genre lists 19 lines; if you inserted in that order, this holds.)
    ordered_genre_ids = [row[0] for row in genre_rows]  # [1,2,...19]
    print("Genre IDs in the order they appear:", ordered_genre_ids)

    filepath = os.path.join(ML100K_DIR, "u.item")
    print(f"Loading movies + movie_genres from {filepath} ...")
    with open(filepath, "r", encoding="latin-1") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) < 24:
                continue
            movie_id = int(parts[0])
            title = parts[1]
            release_date_str = parts[2]  # e.g. "01-Jan-1995"
            # Convert to YYYY-MM-DD for PostgreSQL:
            try:
                release_date = datetime.strptime(release_date_str, "%d-%b-%Y").date()
            except Exception:
                release_date = None

            # 1) Insert into movies
            cur.execute(
                "INSERT INTO movies (movie_id, title, release_date) VALUES (%s, %s, %s) "
                "ON CONFLICT (movie_id) DO NOTHING;",
                (movie_id, title, release_date)
            )

            # 2) The next 19 columns (indices 5..23) are genre flags:
            genre_flags = parts[5:5+len(ordered_genre_ids)]
            for idx, flag in enumerate(genre_flags):
                if flag == "1":
                    genre_id = ordered_genre_ids[idx]
                    cur.execute(
                        "INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s) "
                        "ON CONFLICT (movie_id, genre_id) DO NOTHING;",
                        (movie_id, genre_id)
                    )

def load_ratings(cur):
    """
    Read u.data (format: user_id \t movie_id \t rating \t timestamp).
    We'll insert into ratings(user_id, movie_id, rating, rated_at).
    The timestamp in u.data is a UNIX epoch in seconds; we'll convert it to a proper TIMESTAMP.
    """
    filepath = os.path.join(ML100K_DIR, "u.data")
    print(f"Loading ratings from {filepath} ...")
    with open(filepath, "r", encoding="latin-1") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            user_id, movie_id, rating, ts = line.split("\t")
            ts = int(ts)
            rated_at = datetime.fromtimestamp(ts)
            cur.execute(
                """
                INSERT INTO ratings (user_id, movie_id, rating, rated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, movie_id) DO NOTHING;
                """,
                (int(user_id), int(movie_id), int(rating), rated_at)
            )

def main():
    conn = connect_db()
    cur = conn.cursor()

    try:
        load_genres(cur)
        print("→ genres loaded.")
        load_users(cur)
        print("→ users loaded.")
        load_movies_and_movie_genres(cur)
        print("→ movies & movie_genres loaded.")
        load_ratings(cur)
        print("→ ratings loaded.")

        conn.commit()
        print("All data committed successfully.")
    except Exception as e:
        conn.rollback()
        print("Error occurred:", e)
        print("Rolled back any partial changes.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # main()
    print(DB_PASS)
