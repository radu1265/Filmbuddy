# user_utils.py

import psycopg2
import bcrypt

# ────────────────────────────────────────────────────────────────────────────────
# Database connection parameters (make sure these match what you used in alg.py)
DB_NAME = "movielens"
DB_USER = "movies_user"
DB_PASS = "mypassword"   # ← your actual password
DB_HOST = "localhost"
DB_PORT = 5432
# ────────────────────────────────────────────────────────────────────────────────

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )


def add_new_user(age: int, gender: str, occupation: str, zip_code: str, raw_password: str) -> int:
    """
    Inserts a brand-new (non-dummy) user into 'users' with a bcrypt-hashed password.
    Returns the new user_id (SERIAL).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Hash the plaintext password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(raw_password.encode("utf-8"), salt)

    # 2) Insert into users(age, gender, occupation, zip_code, password_hash, is_dummy)
    cur.execute(
        """
        INSERT INTO users (age, gender, occupation, zip_code, password_hash, is_dummy)
        VALUES (%s, %s, %s, %s, %s, FALSE)
        RETURNING user_id;
        """,
        (age, gender.upper(), occupation, zip_code, hashed)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


def check_user_credentials(user_id: int, raw_password: str) -> bool:
    """
    Returns True if user_id exists and raw_password matches the stored bcrypt hash.
    Otherwise returns False.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE user_id = %s;", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return False

    stored_hash = row[0]   # bcrypt hash stored as BYTEA
    return bcrypt.checkpw(raw_password.encode("utf-8"), stored_hash)


def user_exists(user_id: int) -> bool:
    """
    Returns True if there is a row in users with this user_id; otherwise False.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id = %s;", (user_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def list_all_movies() -> list[tuple[int, str]]:
    """
    Returns a list of (movie_id, title) for every row in movies, ordered by movie_id.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT movie_id, title FROM movies ORDER BY movie_id;")
    movies = cur.fetchall()   # e.g. [(1, 'Toy Story (1995)'), (2, 'GoldenEye (1995)'), …]
    cur.close()
    conn.close()
    return movies


def add_or_update_rating(user_id: int, movie_id: int, rating: int) -> None:
    """
    Inserts or updates a rating by user_id for movie_id. 
    Rating must be 1–5. Raises ValueError if the user doesn’t exist or rating is invalid.
    """
    # Validate rating
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5.")

    if not user_exists(user_id):
        raise ValueError(f"user_id {user_id} does not exist.")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ratings (user_id, movie_id, rating)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, movie_id)
        DO UPDATE SET
          rating = EXCLUDED.rating,
          rated_at = NOW();
        """,
        (user_id, movie_id, rating)
    )
    conn.commit()
    cur.close()
    conn.close()
