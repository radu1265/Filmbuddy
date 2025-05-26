# main.py
from ollama import Client
# from ollama_server import OllamaServer

def chat_loop(client: Client):
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    while True:
        user_msg = input("You: ").strip()
        if user_msg.lower() in ("exit", "quit"):
            break
        messages.append({"role": "user", "content": user_msg})

        print("Assistant:", end=" ", flush=True)
        for chunk in client.chat(model="llama3.1", messages=messages, stream=True):
            print(chunk["message"]["content"], end="", flush=True)
        print()
        messages.append({"role": "assistant", "content": ""})

# if __name__ == "__main__":
    # Start server in a context so it always stops at the end
    # with OllamaServer(host="127.0.0.1:11435"):
    #     client = Client(host="http://127.0.0.1:11435")
    #     client.pull("llama3.1")
    #     chat_loop(client)
    # as soon as we leave the `with` block, stop_server() has run
