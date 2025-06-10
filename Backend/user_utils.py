from dotenv import load_dotenv

import os
import psycopg2
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from typing import Optional

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


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


def add_new_user(
    username: str,
    age: int,
    gender: str,
    occupation: str,
    zip_code: str,
    raw_password: str
) -> int:
    """
    Inserts a brand-new (non-dummy) user into 'users' with:
      - a UNIQUE username
      - bcrypt-hashed password in password_hash
      - is_dummy = FALSE
    Returns the newly assigned user_id.
    """
    # 1. Hash the plaintext password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(raw_password.encode("utf-8"), salt)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (username, age, gender, occupation, zip_code, password_hash, is_dummy)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
            RETURNING user_id;
            """,
            (username, age, gender.upper(), occupation, zip_code, hashed)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise ValueError("Username already taken")
    finally:
        cur.close()
        conn.close()

    return new_id




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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    if user_id is None or not user_exists(user_id):
        raise HTTPException(status_code=401, detail="User not found")
    # you can fetch and return a full user object here if needed
    return user_id