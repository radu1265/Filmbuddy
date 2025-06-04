# server_manager.py
import os
import sys
import signal
import subprocess
import atexit
from contextlib import ContextDecorator

# Windows flags
CREATE_NEW_PROC_GROUP = 0x00000200
CREATE_NO_WINDOW       = 0x08000000

_server_process = None

def start_server(host: str = "127.0.0.1:11435") -> None:
    global _server_process
    if _server_process:
        stop_server()

    os.environ["OLLAMA_HOST"] = host

    _server_process = subprocess.Popen(
        ["ollama", "serve"],
        creationflags=CREATE_NEW_PROC_GROUP | CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    atexit.register(stop_server)
    for sig in (signal.SIGINT, signal.SIGTERM, getattr(signal, "SIGBREAK", None)):
        if sig is not None:
            signal.signal(sig, _handle_signal)

def stop_server() -> None:
    global _server_process
    if not _server_process:
        return

    pid = _server_process.pid

    # 1) polite break (may not work if hidden)
    try:
        _server_process.send_signal(signal.CTRL_BREAK_EVENT)
        _server_process.wait(timeout=3)
    except Exception:
        pass

    # 2) force-kill the entire tree via taskkill
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _server_process = None

def _handle_signal(signum, frame):
    stop_server()
    sys.exit(0)

class OllamaServer(ContextDecorator):
    def __init__(self, host: str = "127.0.0.1:11435"):
        self.host = host

    def __enter__(self):
        start_server(self.host)

    def __exit__(self, exc_type, exc_value, traceback):
        stop_server()
        return False
