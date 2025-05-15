import ollama

# Use the generate function for a one-off prompt
result = ollama.generate(model='llama3.1', prompt='Why is the sky blue?')
print(result['response'])

# import requests

# def get_ollama_response(mode: str, movie: str) -> str:
    
#     url = "http://localhost:11434/api/generate"
#     model = "llama3.1"
#     prompt = "Tell the user in a friendly manner that this movie: {movie} is a greate fit for them."
#     if mode == "chat":
#         data = {
#             "model": model,
#             "messages": [
#                 {"role": "user", "content": prompt}
#             ]
#         }
    
#     elif mode == "json":
#         prompt_json = f''' You are a helpful assistant that will interpret the user's request and provide a JSON response.
#         interpretation = {{
#             "movie": "{movie}",
#             "rating": "rating between 1 and 5",
#             "genre": "genre of the movie",
#             "description": "short description of the movie",
#         }}

#     '''
#         data = {
#             "model": model,
#             "messages": [
#                 {"role": "user", "content": prompt_json}
#             ],
#             "json": True
#         }
#     return requests.post(url, json=data).json()

# if __name__ == "__main__":
#     # Example usage
#     mode = "chat"
#     movie = "Inception"
#     response = get_ollama_response(mode, movie)
#     print(response)
