import requests
import json
from recommendation import alg

# def query_ollama(prompt, model="llama3.1"):
#     url = "http://localhost:11434/api/generate"
#     payload = {
#         "model": model,
#         "prompt": prompt,
#         "stream": True
#     }

#     try:
#         response = requests.post(url, json=payload)
#         return response.json()["response"]
#     except Exception as e:
#         return f"Error: {e}"
def query_ollama(prompt, model="llama3.1", stream=True):
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "num_predict": 512,  # adjust as needed
        }
    }

    try:
        if stream:
            # Handle streamed responses
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()
                full_reply = ""
                for line in response.iter_lines():
                    if line:
                        # Each line is a JSON object
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            print(data["response"], end="", flush=True)
                            full_reply += data["response"]
                        if data.get("done"):
                            break
                print()  # newline after streaming output
                return full_reply
        else:
            # Non-streamed (standard) response
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()["response"]

    except Exception as e:
        return f"Error communicating with Ollama: {e}"

def chat_loop():
    print("🤖 Ollama Chat – Type 'exit' to quit.")
    prompt_init_ollama = f"""

    You are an assistant that interprets movie preferences from natural language input.

    Please respond only in strict JSON with:
    - "intent": always "movie_recommendation"
    - "preferences": inferred genres, tones, or features
    - "confidence": a number between 0-100 representing how confident you are in the interpretation
    - "sentiment": a number between -1 and 1 representing the sentiment of the input

    """

    prompt_output_ollama = f"""

    Please create a short sentance that describes this movie recommendation

    """

    # get movie recommendation model
    # model, rmse_value = alg.apply_svd()

    # trebuie adaugat logica pt json trb adaugat si alg de predictie
    query_ollama(prompt_init_ollama)

    while True:
        # querry_ollama = prompt_init_ollama + "\n" + "User: " + user_input + "\n" + "Assistant: "
        


        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        reply = query_ollama(user_input)
        print(f"Assistant: {reply}")

