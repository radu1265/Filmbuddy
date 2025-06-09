import asyncio
import traceback
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware

from ollama import Client
from server.ollama_server import OllamaServer
from recommendation import alg  # your existing recommendation.alg module
from user_utils import get_db_connection
import bcrypt

ACCESS_TOKEN_EXPIRE_MINUTES = 60

from user_utils import (
    add_new_user,
    list_all_movies,
    add_or_update_rating,
    user_exists,
    create_access_token,
    get_current_user
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
        "movie_id": int,
        "title": str,
        "comment": str
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
    movie_id = df.iloc[0]["movie_id"]
    print(f"Top recommendation for user {user_id}: {title} (ID: {movie_id})")
    movie_id = int(movie_id)
    comment = movie_response_str(client, title)

    return {
        "movie_id": movie_id,
        "title": title,
        "comment": comment
    }



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
async def register_user(data: Dict[str, Any], response: Response):
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
    
    token = create_access_token({"user_id": new_id})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

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
async def login_user(data: Dict[str, Any], response: Response):
    """
    POST /users/login
    Body JSON: { "username": str, "password": str }
    Returns:
      { "user_id": int, "alpha": float, "success": bool }
    """
    username = data.get("username", "").strip()
    raw_password = data.get("password", "")

    if not username:
        raise HTTPException(status_code=400, detail="Username required.")
    if not isinstance(raw_password, str) or not raw_password:
        raise HTTPException(status_code=400, detail="Password required.")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, is_dummy, password_hash, alpha
          FROM users
         WHERE username = %s;
        """,
        (username,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found.")

    user_id, is_dummy, stored_hash, stored_alpha = row

    # If it’s a dummy account, accept only “admin”
    if is_dummy:
        if raw_password != "admin":
            raise HTTPException(status_code=401, detail="Incorrect password for dummy.")
    else:
        # Real user — verify stored_hash
        if stored_hash is None:
            raise HTTPException(status_code=500, detail="No password set for this user.")
        if isinstance(stored_hash, memoryview):
            stored_hash = bytes(stored_hash)
        if not bcrypt.checkpw(raw_password.encode("utf-8"), stored_hash):
            raise HTTPException(status_code=401, detail="Incorrect password.")

    # At this point authentication succeeded; issue JWT cookie
    token = create_access_token({"user_id": user_id})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,       # set True in production (HTTPS)
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"user_id": user_id, "alpha": stored_alpha, "success": True}

@app.post("/users/logout")
async def logout(response: Response):
    response.delete_cookie("session_token")
    return {"success": True}

@app.put("/users/{user_id}/alpha")
async def update_user_alpha(user_id: int, data: Dict[str, Any]):
    """
    PUT /users/{user_id}/alpha
    Body JSON: { "alpha": float }
    Returns: { "alpha": float }
    """
    new_alpha = data.get("alpha")
    if not isinstance(new_alpha, (float, int)) or not (0.0 <= float(new_alpha) <= 1.0):
        raise HTTPException(status_code=400, detail="Alpha must be a number between 0.0 and 1.0.")

    # Verify user exists
    if not user_exists(user_id):
        raise HTTPException(status_code=404, detail="User not found.")

    # Update in database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET alpha = %s WHERE user_id = %s;",
        (new_alpha, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"alpha": new_alpha}

@app.get("/users/by-username/{username}")
async def get_user_by_username(username: str):
    """
    GET /api/users/by-username/{username}
    Returns { "user_id": int } or 404 if not found
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE username = %s;",
        (username,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found.")
    return {"user_id": row[0]}

from fastapi import HTTPException, Depends
from typing import Dict, Any

@app.get("/users/friends")
async def list_friends(current_user: int = Depends(get_current_user)):
    """
    List all friends of the current user.
    Returns: [ { "user_id": int, "username": str }, ... ]
    """
    conn = get_db_connection()
    cur = conn.cursor()
    print
    cur.execute(
        """
        SELECT u.user_id, u.username
          FROM friends f
          JOIN users u ON u.user_id = f.friend_id
         WHERE f.user_id = %s
         ORDER BY u.username;
        """,
        (current_user,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"user_id": r[0], "username": r[1]} for r in rows]

@app.post("/users/friends")
async def add_friend(
    data: Dict[str, Any],
    current_user: int = Depends(get_current_user),
):
    """
    POST /api/users/friends
    Body JSON: { "friend_id": int } or { "friend_username": str }
    """
    fid = data.get("friend_id")
    if fid is None:
        uname = data.get("friend_username", "").strip()
        if not uname:
            raise HTTPException(status_code=400, detail="Must provide friend_id or friend_username.")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username = %s;", (uname,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"User '{uname}' not found.")
        fid = row[0]

    if not isinstance(fid, int):
        raise HTTPException(status_code=400, detail="friend_id must be an integer.")
    if fid == current_user:
        raise HTTPException(status_code=400, detail="Cannot friend yourself.")
    if not user_exists(fid):
        raise HTTPException(status_code=404, detail=f"User {fid} not found.")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO friends (user_id, friend_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
        """,
        (current_user, fid),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"success": True}


@app.delete("/users/friends/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: int = Depends(get_current_user),
):
    """
    DELETE /api/users/friends/{friend_id}
    Removes the mutual friendship AND any friend_requests between the two users.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Remove both directions of the friendship
    cur.execute(
        """
        DELETE FROM friends
         WHERE (user_id = %s AND friend_id = %s)
            OR (user_id = %s AND friend_id = %s);
        """,
        (current_user, friend_id, friend_id, current_user),
    )

    # 2) Remove any friend_requests between them (any status)
    cur.execute(
        """
        DELETE FROM friend_requests
         WHERE (from_user_id = %s AND to_user_id = %s)
            OR (from_user_id = %s AND to_user_id = %s);
        """,
        (current_user, friend_id, friend_id, current_user),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"success": True}


# 1️⃣ Send a friend request
@app.post("/users/friend_requests")
async def send_friend_request(
    data: Dict[str, Any],
    current_user: int = Depends(get_current_user),
):
    """
    POST /api/users/friend_requests
    Body JSON: { "friend_username": str } (or "friend_id": int)
    """
    fid = data.get("friend_id")
    if fid is None:
        uname = (data.get("friend_username") or "").strip()
        if not uname:
            raise HTTPException(400, "Must provide friend_username or friend_id")
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username = %s;", (uname,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            raise HTTPException(404, f"User '{uname}' not found.")
        fid = row[0]

    if not isinstance(fid, int):
        raise HTTPException(400, "friend_id must be an integer")
    if fid == current_user:
        raise HTTPException(400, "Cannot friend yourself")
    if not user_exists(fid):
        raise HTTPException(404, f"User {fid} not found")

    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO friend_requests (from_user_id, to_user_id)
            VALUES (%s, %s)
            ON CONFLICT (from_user_id,to_user_id) DO NOTHING;
            """,
            (current_user, fid),
        )
        conn.commit()
    finally:
        cur.close(); conn.close()

    return {"success": True}


# 2️⃣ List incoming requests
@app.get("/users/friend_requests")
async def list_friend_requests(current_user: int = Depends(get_current_user)):
    """
    GET /api/users/friend_requests
    Returns a list of pending requests TO me:
      [ { request_id, from_user_id, from_username, created_at }, … ]
    """
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute(
        """
        SELECT fr.request_id,
               fr.from_user_id,
               u.username AS from_username,
               fr.created_at
          FROM friend_requests fr
          JOIN users u ON u.user_id = fr.from_user_id
         WHERE fr.to_user_id = %s
           AND fr.status = 'pending'
         ORDER BY fr.created_at ASC;
        """,
        (current_user,),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()

    return [
        {
          "request_id":    r[0],
          "from_user_id":  r[1],
          "from_username": r[2],
          "created_at":    r[3].isoformat(),
        }
        for r in rows
    ]


# 3️⃣ Respond to a request
@app.post("/users/friend_requests/{request_id}/respond")
async def respond_friend_request(
    request_id: int,
    data: Dict[str, Any],
    current_user: int = Depends(get_current_user),
):
    """
    POST /api/users/friend_requests/{request_id}/respond
    Body JSON: { "accept": boolean }
    """
    accept = data.get("accept")
    if not isinstance(accept, bool):
        raise HTTPException(status_code=400, detail="Missing 'accept' boolean")

    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Verify there is a pending request to this user
    cur.execute(
        """
        SELECT from_user_id, to_user_id
          FROM friend_requests
         WHERE request_id = %s
           AND status = 'pending';
        """,
        (request_id,),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found or already handled")

    fid, tid = row
    if tid != current_user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Not your request to respond to")

    # 2) If accepted, insert mutual friendship
    if accept:
        cur.execute(
            """
            INSERT INTO friends (user_id, friend_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
            INSERT INTO friends (user_id, friend_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (current_user, fid, fid, current_user),
        )

    # 3) Delete the request row regardless of accept/reject
    cur.execute(
        "DELETE FROM friend_requests WHERE request_id = %s;",
        (request_id,),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"success": True}

@app.get("/users/friend_requests/outgoing")
async def list_outgoing_requests(current_user: int = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT fr.request_id,
               fr.to_user_id,
               u.username AS to_username
          FROM friend_requests fr
          JOIN users u ON u.user_id = fr.to_user_id
         WHERE fr.from_user_id = %s
           AND fr.status = 'pending'
         ORDER BY fr.created_at;
        """,
        (current_user,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
      {"request_id": r[0], "to_user_id": r[1], "to_username": r[2]}
      for r in rows
    ]

@app.post("/chats/send")
async def send_message(
    data: Dict[str, Any],
    from_user_id: int = Depends(get_current_user)   # now derived from the session cookie
):
    """
    POST /api/chats/send
    Body JSON: { "to_user_id": int, "text": str }
    Returns { "success": True } or HTTPException
    """
    to_user_id = data.get("to_user_id")
    text       = (data.get("text") or "").strip()

    # 1) Basic type checks
    if not isinstance(to_user_id, int):
        raise HTTPException(status_code=400, detail="to_user_id must be an integer.")
    if to_user_id == from_user_id:
        raise HTTPException(status_code=400, detail="Cannot send a message to yourself.")
    if not text:
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")

    # 2) Existence check for recipient
    if not user_exists(to_user_id):
        raise HTTPException(status_code=404, detail=f"Recipient user {to_user_id} not found.")

    # 3) Insert into DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO messages (from_user_id, to_user_id, text)
        VALUES (%s, %s, %s);
        """,
        (from_user_id, to_user_id, text),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"success": True}




@app.get("/chats/history")
async def get_history(
    peer_id: int,
    current_user: int = Depends(get_current_user),
):
    """
    GET /api/chats/history?user1=<int>&user2=<int>
    Returns JSON: { "messages": [ { "from": int, "to": int, "text": str, "ts": str }, … ] }
    Only returns messages where (from = user1 AND to = user2) OR (from = user2 AND to = user1), ordered by timestamp ascending.
    """
    user1 = current_user
    user2 = peer_id

    if not isinstance(user1, int) or not isinstance(user2, int):
        raise HTTPException(status_code=400, detail="user1 and user2 must be integers.")
    # In a production app, confirm that the caller is either user1 or user2, to prevent snooping.
    # For now, we assume the front-end won’t lie.
    if not user_exists(user1) or not user_exists(user2):
        raise HTTPException(status_code=404, detail="One or both users not found.")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT from_user_id, to_user_id, text, created_at
          FROM messages
         WHERE (from_user_id = %s AND to_user_id = %s)
            OR (from_user_id = %s AND to_user_id = %s)
         ORDER BY created_at ASC;
        """,
        (user1, user2, user2, user1),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "messages": [
            {
                "from": r[0],
                "to": r[1],
                "text": r[2],
                "ts": r[3].isoformat(),
            }
            for r in rows
        ]
    }

@app.get("/chats/unread")
async def get_unread_messages(current_user: int = Depends(get_current_user)):
    """
    GET /api/chats/unread
    Returns all messages sent *to* current_user that have not yet been marked seen,
    along with the sender's username. Then marks them seen.
    """
    user_id = current_user

    conn = get_db_connection()
    cur = conn.cursor()
    # 1) Select unread messages + sender username
    cur.execute(
        """
        SELECT m.message_id, m.from_user_id, u.username AS from_username, m.text, m.created_at
          FROM messages m
          JOIN users u ON u.user_id = m.from_user_id
         WHERE m.to_user_id = %s
           AND m.seen = FALSE
         ORDER BY m.created_at ASC;
        """,
        (user_id,),
    )
    rows = cur.fetchall()

    # 2) Mark them seen
    cur.execute(
        "UPDATE messages SET seen = TRUE WHERE to_user_id = %s AND seen = FALSE;",
        (user_id,),
    )
    conn.commit()
    cur.close()
    conn.close()

    return [
        {
            "message_id":   row[0],
            "from_user_id": row[1],
            "from_username": row[2],
            "text":         row[3],
            "ts":           row[4].isoformat(),
        }
        for row in rows
    ]


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

@app.get("/movies/unrated")
async def list_unrated_movies(current_user: int = Depends(get_current_user)):
    """
    GET /api/movies/unrated
    Returns all movies that the current user has not yet rated.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT m.movie_id, m.title
          FROM movies m
     LEFT JOIN ratings r
            ON r.movie_id = m.movie_id
           AND r.user_id = %s
         WHERE r.user_id IS NULL
         ORDER BY m.title
        """,
        (current_user,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"movie_id": mid, "title": t} for mid, t in rows]

@app.post("/ratings")
async def rate_movie(
    data: Dict[str, Any],
    current_user: int = Depends(get_current_user),
):
    """
    POST /api/ratings
    Body JSON: { "movie_id": int, "rating": int }
    Uses session cookie to identify user.
    """
    movie_id = data.get("movie_id")
    rating   = data.get("rating")

    # Basic validation
    if not isinstance(movie_id, int) or movie_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid movie_id.")
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be 1–5.")

    try:
        # Reuse your helper, but pass current_user instead of body’s user_id
        add_or_update_rating(current_user, movie_id, rating)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save rating: {e}")

    return {"success": True}
