import asyncio
import traceback
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ollama import Client
from server.ollama_server import OllamaServer
from recommendation import alg  # your existing recommendation.alg module
from user_utils import get_db_connection
import bcrypt

from user_utils import (
    add_new_user,
    list_all_movies,
    add_or_update_rating,
    user_exists
)

# Globals to hold the Ollama server context and client
ollama_server: OllamaServer = None
client: Client = None


def check_user_id(user_id: int) -> bool:
    return isinstance(user_id, int) and 1 <= user_id <= 1000000
    # (adjust upper bound as you wish)


async def interpret_emotion(
    client: Client, user_text: str, alpha: float
) -> float:
    """
    Calls Ollama to interpret the user's emotion (0.0–1.0) and returns a float.
    """
    prompt = (
        "You are an analysis assistant.\n"
        "ALWAYS RESPOND ONLY WITH A SINGLE FLOAT NUMBER BETWEEN 0.0 AND 1.0 FOR EMOTIONS, POSITIVE IS BIGGER.\n"
        f"User input: \"{user_text}\""
    )
    response = client.generate(model="llama3.1", prompt=prompt)
    try:
        raw = response.get("response", "0.5").strip()
        alpha_out = float(raw)
    except (ValueError, AttributeError):
        alpha_out = 0.5

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, alpha_out))


def movie_response_str(client: Client, movie: str) -> str:
    """
    Uses Ollama chat (streaming) to get a short recommendation/fun fact about `movie`.
    Returns the full concatenated string.
    """
    messages = [
        {"role": "system", "content": "You are a movie expert assistant."},
        {
            "role": "user",
            "content": (
                f"Based on my algorithm, the predicted movie is '{movie}'. "
                "Provide a concise recommendation or fun fact about this movie."
            ),
        },
    ]

    # stream=True returns an iterator of chunks; concatenate them
    full = ""
    for chunk in client.chat(model="llama3.1", messages=messages, stream=True):
        full += chunk["message"]["content"]
    return full.strip()


async def chat_response(client: Client, history: List[Dict[str, str]]) -> str:
    """
    Uses Ollama chat (streaming) to reply given a Slack‐style `history` of messages.
    Returns the full concatenated assistant reply.
    """
    full = ""
    for chunk in client.chat(model="llama3.1", messages=history, stream=True):
        full += chunk["message"]["content"]
    return full.strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler to start and stop the Ollama server.
    """
    global ollama_server, client

    # Startup logic
    ollama_server = OllamaServer(host="127.0.0.1:11435")
    ollama_server.__enter__()  # Start OllamaServer
    client = Client(host="http://127.0.0.1:11435")
    client.pull("llama3.1")  # Preload the model

    yield  # Hand over control to FastAPI

    # Shutdown logic
    if ollama_server:
        ollama_server.__exit__(None, None, None)


app = FastAPI(lifespan=lifespan)

# 1. Allow CORS from your Vite/React frontend (e.g. http://localhost:5173)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────────────────────────────────────────────────────────────────
# Recommendation endpoints (unchanged)
# ────────────────────────────────────────────────────────────────────────────────

@app.post("/recommend/top")
async def get_top_recommendation(data: Dict[str, Any]):
    """
    POST /recommend/top
    Body JSON: { "user_id": int, "alpha": float }
    Returns:
      {
        "title": "<movie title>",
        "comment": "<Ollama-generated comment>"
      }
    """
    user_id = data.get("user_id")
    alpha = data.get("alpha")

    if not check_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user_id (must be ≥1).")

    try:
        alpha = float(alpha)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alpha value.")

    df = alg.recommend_top_n_movies(user_id, 1, alpha)
    if df.empty:
        raise HTTPException(status_code=404, detail="No recommendation found.")
    title = df.iloc[0]["title"]

    comment = movie_response_str(client, title)

    return {"title": title, "comment": comment}


@app.post("/recommend/top_list")
async def get_top_list(data: Dict[str, Any]):
    """
    POST /recommend/top_list
    Body JSON: { "user_id": int, "alpha": float, "n": int (optional, default=5) }
    Returns:
      {
        "movies": [
          { "title": str, "hybrid_score": float, ... },
          ...
        ]
      }
    """
    user_id = data.get("user_id")
    alpha = data.get("alpha")
    n = data.get("n", 5)

    if not check_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user_id (must be ≥1).")
    try:
        alpha = float(alpha)
        n = int(n)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alpha or n value.")

    df = alg.recommend_top_n_movies(user_id, n, alpha)
    records = df.to_dict(orient="records")
    return {"movies": records}


@app.post("/emotion")
async def adjust_alpha(data: Dict[str, Any]):
    """
    POST /emotion
    Body JSON: { "user_text": str, "alpha": float }
    Returns:
      {
        "alpha_interpreted": float,
        "alpha_adjusted": float
      }
    """
    user_text = data.get("user_text", "")
    alpha = data.get("alpha")

    try:
        alpha = float(alpha)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alpha value.")

    interpreted = await interpret_emotion(client, user_text, alpha)
    adjusted = (interpreted + alpha) / 2.0

    return {"alpha_interpreted": interpreted, "alpha_adjusted": adjusted}


@app.post("/chat")
async def chat_endpoint(data: Dict[str, Any]):
    """
    POST /chat
    Body JSON: { "history": [ { "role": "user"|"assistant"|"system", "content": str }, ... ] }
    Returns:
      { "reply": "<assistant-generated text>" }
    """
    history = data.get("history")
    if not isinstance(history, list):
        raise HTTPException(status_code=400, detail="`history` must be a list of messages.")

    reply = await chat_response(client, history)
    return {"reply": reply}


# ────────────────────────────────────────────────────────────────────────────────
# New endpoints for user‐management, movie‐listing, and rating
# ────────────────────────────────────────────────────────────────────────────────

@app.post("/users/register")
async def register_user(data: Dict[str, Any]):
    """
    POST /users/register
    Body JSON:
      {
        "username": str,       # must be unique, nonempty
        "age": int,
        "gender": "M"|"F",
        "occupation": str,
        "zip_code": str,
        "password": str
      }
    Returns:
      { "user_id": int }
    """
    username = data.get("username", "").strip()
    age = data.get("age")
    gender = data.get("gender", "").upper()
    occupation = data.get("occupation", "")
    zip_code = data.get("zip_code", "")
    raw_password = data.get("password", "")

    # Validate username
    if not isinstance(username, str) or len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be ≥3 characters.")

    # The rest of your existing validation:
    if not isinstance(age, int) or age <= 0:
        raise HTTPException(status_code=400, detail="Invalid age.")
    if gender not in ("M", "F"):
        raise HTTPException(status_code=400, detail="Gender must be 'M' or 'F'.")
    if not isinstance(occupation, str) or not occupation:
        raise HTTPException(status_code=400, detail="Invalid occupation.")
    if not isinstance(zip_code, str) or not zip_code:
        raise HTTPException(status_code=400, detail="Invalid zip_code.")
    if not isinstance(raw_password, str) or len(raw_password) < 4:
        raise HTTPException(status_code=400, detail="Password must be ≥4 characters.")

    try:
        new_id = add_new_user(username, age, gender, occupation, zip_code, raw_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create user: {e}")

    return {"user_id": new_id}

@app.get("/users/{user_id}/rating_count")
async def get_rating_count(user_id: int):
    """
    Returns how many ratings this user has submitted so far.
    Response: { "count": <integer> }
    """
    # 1) Verify user exists
    if not user_exists(user_id):
        raise HTTPException(status_code=404, detail="User not found.")

    # 2) Query the ratings table
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM ratings WHERE user_id = %s;",
        (user_id,)
    )
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    return {"count": count}



@app.post("/users/login")
async def login_user(data: Dict[str, Any]):
    """
    POST /users/login
    Body JSON: { "username": str, "password": str }
    Returns:
      { "user_id": int, "success": bool }
    """
    username = data.get("username", "").strip()
    raw_password = data.get("password", "")

    if not username:
        raise HTTPException(status_code=400, detail="Username required.")
    if not isinstance(raw_password, str) or not raw_password:
        raise HTTPException(status_code=400, detail="Password required.")
    
    # debug
    print(f"Login attempt for user: {username}")

    # 1) Look up the row by username, retrieve user_id, is_dummy, and password_hash
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, is_dummy, password_hash FROM users WHERE username = %s;",
        (username,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found.")

    user_id, is_dummy, stored_hash = row

    # 2) If dummy account, accept only "admin"
    if is_dummy:
        if raw_password == "admin":
            return {"user_id": user_id, "success": True}
        else:
            raise HTTPException(status_code=401, detail="Incorrect password for dummy.")

    # 3) Real user → check that stored_hash is not None, then bcrypt
    if stored_hash is None:
        raise HTTPException(status_code=500, detail="No password set for this user.")

    # Convert memoryview to bytes if necessary
    if isinstance(stored_hash, memoryview):
        stored_hash = bytes(stored_hash)

    if not bcrypt.checkpw(raw_password.encode("utf-8"), stored_hash):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    return {"user_id": user_id, "success": True}


@app.get("/movies")
async def get_movies():
    """
    GET /movies
    Returns:
      {
        "movies": [
          { "movie_id": int, "title": str },
          ...
        ]
      }
    """
    try:
        movies = list_all_movies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list movies: {e}")

    return {
        "movies": [
            {"movie_id": mid, "title": title}
            for mid, title in movies
        ]
    }


@app.post("/ratings")
async def rate_movie(data: Dict[str, Any]):
    """
    POST /ratings
    Body JSON: { "user_id": int, "movie_id": int, "rating": int }
    Returns:
      { "success": bool }
    """
    user_id = data.get("user_id")
    movie_id = data.get("movie_id")
    rating = data.get("rating")

    # Basic validation
    if not isinstance(user_id, int) or user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user_id.")
    if not isinstance(movie_id, int) or movie_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid movie_id.")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1–5.")

    try:
        add_or_update_rating(user_id, movie_id, rating)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save rating: {e}")

    return {"success": True}
