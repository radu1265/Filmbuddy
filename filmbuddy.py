import asyncio
import os
from ollama import Client
from interface.ollama_server import OllamaServer
from recommendation import alg

# Task 1: Emotional interpretation to adjust alpha
# Returns a float between 0.0 and 1.0
async def interpret_emotion(client: Client, user_text: str) -> float:
    prompt = (
        "You are an analysis assistant.\n"
        "Interpret the emotion in the following user input and respond with a single number \n"
        "between 0.0 (user wants simething new) and 1.0 (user wants things similar to what they allreay saw).\n"
        f"User input: \"{user_text}\""
    )
    response = client.generate(
        model="llama3.1",
        prompt=prompt
    )
    try:
        alpha = float(response.get("completion", "0.5").strip())
    except ValueError:
        alpha = 0.5
    return max(0.0, min(1.0, alpha))

# Task 2: Generate output based on a predicted movie
def movie_response(client: Client, movie: str) -> None:
    messages = [
        {"role": "system", "content": "You are a movie expert assistant."},
        {"role": "user", "content": (
            f"Based on my algorithm, the predicted movie is '{movie}'. "
            "Provide a concise recommendation or fun fact about this movie."
        )}
    ]
    print("Movie output:", end=" ", flush=True)
    for chunk in client.chat(
        model="llama3.1",
        messages=messages,
        stream=True
    ):
        # each chunk looks like {'message': {'role': 'assistant', 'content': '...'}}
        print(chunk["message"]["content"], end="", flush=True)
    print("\n")

# Task 3: Standard chat interaction (streaming)
async def chat_interaction(client: Client, history: list[dict]) -> None:
    print("Assistant:", end=" ", flush=True)
    for chunk in client.chat(model="llama3.1", messages=history, stream=True):
        print(chunk["message"]["content"], end="", flush=True)
    print("\n")

# Utility: Validate user ID
def check_user_id(user_id: int) -> bool:
    return isinstance(user_id, int) and 1 <= user_id <= 1000

# Main application loop
def main():
    # Step 1: Ask for user ID
    print("Welcome to FilmBuddy! Your personal movie recommendation assistant.")
    try:
        user_id_input = input("Please enter your user ID (1-1000): ")
        user_id = int(user_id_input)
    except ValueError:
        print("Invalid user ID. Exiting.")
        return
    if not check_user_id(user_id):
        print("User ID out of range. Exiting.")
        return

    # Initial alpha for hybrid recommendations
    alpha = 0.7

    # Step 2: Start Ollama server and client
    with OllamaServer(host="127.0.0.1:11435"):
        client = Client(host="http://127.0.0.1:11435")
        client.pull("llama3.1")

        # Interactive menu
        while True:
            print(f"\nCurrent alpha: {alpha:.2f}")
            print("Choose an action:")
            print("  1. Get top movie recommendation")
            print("  2. Get list of top-rated movies")
            print("  3. Talk about a specific movie")
            print("  4. Personalize experience (adjust alpha)")
            print("  5. Chat with assistant")
            print("  6. Exit")
            choice = input("Enter choice (1-6): ").strip()

            if choice == '1':
                # Task 2a: single top movie
                print("Getting top movie recommendation...")
                movie = alg.recommend_top_n_movies(user_id, 1, alpha)
                title = movie['title'].values[0]
                print(f"Recommended for you: {title}")
                # Task 2b: Ollama comment on movie
                movie_response(client, title)

            elif choice == '2':
                # Task 2: list top-rated movies
                print("Getting top 5 movies...")
                movies = alg.recommend_top_n_movies(user_id, 5, alpha)
                for idx, row in movies.iterrows():
                    print(f"{idx+1}. {row['title']} (Score: {row['hybrid_score']:.2f})")
                print()

            elif choice == '3':
                # Task 3: Talk about specific movie
                movie_name = input("Enter movie name: ").strip()
                history = [
                    {"role": "system", "content": "You are a movie expert assistant."},
                    {"role": "user", "content": f"Let's talk about {movie_name}."}
                ]
                print(f"Entering discussion about '{movie_name}'. Type 'exit' or 'quit' to return to menu.")
                while True:
                    asyncio.run(chat_interaction(client, history))
                    history.append({"role": "assistant", "content": ""})
                    user_msg = input(f"You (about {movie_name}): ").strip()
                    if user_msg.lower() in ("exit", "quit"):
                        print(f"Exiting discussion about '{movie_name}'.\n")
                        break
                    history.append({"role": "user", "content": user_msg})


            elif choice == '4':
                # Task 1: Emotional interpretation to adjust alpha
                reaction = input("How do you feel about these recommendations? ").strip()
                alpha = asyncio.run(interpret_emotion(client, reaction))
                print(f"Adjusted alpha: {alpha:.2f}")

            elif choice == '5':
                # Task 3: free chat
                history = [{"role": "system", "content": "You are a helpful assistant."}]
                while True:
                    user_msg = input("You: ").strip()
                    if user_msg.lower() in ("exit", "quit"):  # end chat sub-loop
                        break
                    history.append({"role": "user", "content": user_msg})
                    asyncio.run(chat_interaction(client, history))
                    history.append({"role": "assistant", "content": ""})

            elif choice == '6':
                print("Thank you for using FilmBuddy! Goodbye!")
                break

            else:
                print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()
