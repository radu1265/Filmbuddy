import asyncio
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ollama import Client
from server.ollama_server import OllamaServer
from recommendation import alg  # your existing recommendation.alg module

# Globals to hold the Ollama server context and client
ollama_server: OllamaServer = None
client: Client = None


def check_user_id(user_id: int) -> bool:
    return isinstance(user_id, int) and 1 <= user_id <= 1000


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
    "http://localhost:3000",  # if you ever run a different dev port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        raise HTTPException(status_code=400, detail="Invalid user_id (must be 1-1000).")

    try:
        alpha = float(alpha)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alpha value.")

    # Recommendation algorithm (returns a pandas DataFrame)
    df = alg.recommend_top_n_movies(user_id, 1, alpha)
    if df.empty:
        raise HTTPException(status_code=404, detail="No recommendation found.")
    title = df.iloc[0]["title"]

    # Get Ollama comment
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
        raise HTTPException(status_code=400, detail="Invalid user_id (must be 1-1000).")
    try:
        alpha = float(alpha)
        n = int(n)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alpha or n value.")

    df = alg.recommend_top_n_movies(user_id, n, alpha)
    # Convert DataFrame to list of dicts
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
