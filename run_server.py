"""
H.Huddair's Nexus-Pulse - Level 2
Unified Application Server & Background Automation Runner
Boots the FastAPI backend, serves the React Cyberpunk GUI,
and opens the default browser directly to the dashboard.
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from api.app import app


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether the specified port is already open and accepting connections."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def open_browser_delayed(url: str = "http://127.0.0.1:8000/", delay: float = 1.2):
    """Waits for uvicorn to bind port 8000, then automatically opens default browser."""
    time.sleep(delay)
    print(f"\n[LAUNCHER] Automatically opening default browser at {url} ...")
    webbrowser.open(url)


def main():
    port = int(os.environ.get("NEXUS_PORT", 8000))
    url = f"http://127.0.0.1:{port}/"

    print("=" * 68)
    print("  H.HUDDAIR'S NEXUS-PULSE [LEVEL 2 ENTERPRISE LAUNCHER]")
    print(f"  Target URL: {url}")
    print("=" * 68)

    # Check if port is already running to avoid WinError 10048
    if is_port_in_use(port):
        print(f"\n[NOTICE] Port {port} is already active! Nexus-Pulse server is running.")
        print(f"[LAUNCHER] Opening {url} directly in default browser...\n")
        webbrowser.open(url)
        return

    # Launch browser on separate daemon thread
    browser_thread = threading.Thread(target=open_browser_delayed, args=(url,), daemon=True)
    browser_thread.start()

    # Run uvicorn server (serves REST API + React Cyberpunk Dashboard)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
