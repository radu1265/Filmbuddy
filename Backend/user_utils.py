from dotenv import load_dotenv

import os
import psycopg2
import bcrypt

load_dotenv()  # Load environment variables from .env file

# ────────────────────────────────────────────────────────────────────────────────
# Database connection parameters (make sure these match what you used in alg.py)
DB_NAME = "movielens"
DB_USER = "postgres"
DB_PASS = os.getenv("PASSWORD")
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
    Verifies whether a given user_id exists and whether the provided raw_password
    matches the stored bcrypt hash. Returns True if credentials are valid, False otherwise.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE user_id = %s;", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        print(f"[login] User ID {user_id} does not exist.")
        return False

    stored_hash = row[0]
    if stored_hash is None:
        print(f"[login] No password set for user ID {user_id}.")
        return False

    # Debug logging
    print(f"[login] raw_password (str): {raw_password!r}")
    print(f"[login] stored_hash raw type: {type(stored_hash)}, repr: {stored_hash!r}")

    # Convert memoryview (or other buffer) to bytes
    if isinstance(stored_hash, memoryview):
        print("[login] Converting stored_hash from memoryview to bytes")
        stored_hash = bytes(stored_hash)
    elif isinstance(stored_hash, str):
        # If you ever stored it as TEXT, convert that string to bytes
        print("[login] Converting stored_hash from str to bytes")
        stored_hash = stored_hash.encode("utf-8")
    # If it's already bytes, do nothing

    try:
        ok = bcrypt.checkpw(raw_password.encode("utf-8"), stored_hash)
        print(f"[login] bcrypt.checkpw returned: {ok}")
        return ok
    except Exception as ex:
        print(f"[login] Exception in bcrypt.checkpw: {ex}")
        return False




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
