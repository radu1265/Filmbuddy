import os
import sys
import signal
import subprocess
import atexit
from ollama import Client


# 1) Tell Ollama to listen on 127.0.0.1:11435
os.environ["OLLAMA_HOST"] = "127.0.0.1:11435"

# 2) Launch Ollama in a new process group so we can signal the whole group
CREATE_NEW_PROC_GROUP = 0x00000200
server = subprocess.Popen(
    ["ollama", "serve"],
    creationflags=CREATE_NEW_PROC_GROUP,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

def cleanup():
    """Try a gentle CTRL_BREAK, then a hard kill if needed."""
    try:
        # Send CTRL_BREAK_EVENT to the group
        server.send_signal(signal.CTRL_BREAK_EVENT)
        # Give it a few seconds to exit cleanly
        server.wait(timeout=5)
    except Exception:
        # If it's still alive, force-kill it (and its children)
        server.kill()

# 3) Always attempt cleanup on normal exit
atexit.register(cleanup)

# 4) Also catch Ctrl+C or external TERM to clean up immediately
def _on_signal(signum, frame):
    cleanup()
    sys.exit(0)  # re-raise default exit

signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)

# 5) Now initialize your client and pull the model
client = Client(host="http://127.0.0.1:11435")
client.pull("llama3.1")

# 6) Your chat loop
def chat_loop():
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

if __name__ == "__main__":
    try:
        chat_loop()
    finally:
        # Just in case
        cleanup()
