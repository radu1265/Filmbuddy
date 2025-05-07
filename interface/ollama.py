import requests
import json
from recommendation.alg import alg

def query_ollama(prompt, model="llama3.1"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        return response.json()["response"]
    except Exception as e:
        return f"Error: {e}"


def chat_loop():
    print("🤖 Ollama Chat – Type 'exit' to quit.")
    prompt_ollama = f"""

    You are an assistant that interprets movie preferences from natural language input.

    Please respond only in strict JSON with:
    - "intent": always "movie_recommendation"
    - "preferences": inferred genres, tones, or features
    - "confidence": a number between 0-100 representing how confident you are in the interpretation
    - "raw_response": a natural sentence recommending a placeholder movie (don't worry, the actual movie will be inserted later)

    """
    # get movie recommendation model
    model, rmse_value = alg.apply_svd()

    # trebuie adaugat logica pt json trb adaugat si alg de predictie

    while True:
        querry_ollama = prompt_ollama + "\n" + "User: " + user_input + "\n" + "Assistant: "

        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        reply = query_ollama(user_input)
        print(f"Ollama: {reply.strip()}\n")
