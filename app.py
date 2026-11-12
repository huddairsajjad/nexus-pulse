"""
H.Huddair's Nexus-Pulse [Level 2 Enterprise]
Production Application Entrypoint for Railway & Cloud Containers
Configured with dynamic port binding (0.0.0.0 and $PORT), auxiliary proxy forwarders, /health telemetry, CORS, and PWA assets.
"""

import os
import sys
import socket
import threading
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from api.app import app


def start_auxiliary_port_forwarder(source_port: int, target_port: int):
    """
    Listens on auxiliary ports (e.g. 8000, 8080, 3000) and forwards to the main Uvicorn port.
    Prevents 502 Bad Gateway if the Railway Public Domain Target Port differs from $PORT.
    """
    def handle_client(client_sock, target_sock):
        def forward(src, dst):
            try:
                while True:
                    data = src.recv(8192)
                    if not data:
                        break
                    dst.sendall(data)
            except Exception:
                pass
            finally:
                try:
                    src.close()
                except Exception:
                    pass
                try:
                    dst.close()
                except Exception:
                    pass

        threading.Thread(target=forward, args=(client_sock, target_sock), daemon=True).start()
        threading.Thread(target=forward, args=(target_sock, client_sock), daemon=True).start()

    def listener():
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", source_port))
            srv.listen(128)
            while True:
                client, _ = srv.accept()
                try:
                    target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    target.connect(("127.0.0.1", target_port))
                    handle_client(client, target)
                except Exception:
                    try:
                        client.close()
                    except Exception:
                        pass
        except Exception:
            pass

    t = threading.Thread(target=listener, daemon=True)
    t.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")

    # Start multi-port bridge for standard web proxy ports (8000, 8080, 3000)
    for aux_port in [8000, 8080, 3000]:
        if aux_port != port:
            start_auxiliary_port_forwarder(aux_port, port)

    print(f"[NEXUS-PULSE] Booting production server on {host}:{port}")
    uvicorn.run("app:app", host=host, port=port, log_level="info")
