"""
H.Huddair's Nexus-Pulse [Level 2 Enterprise]
Production Application Entrypoint for Railway & Cloud Containers
"""

# =====================================================================
# Railway IPv4 Socket Enforcement (Mandatory Network Fix)
# At the absolute top of the main entry point (main.py), before any network,
# HTTP, or SMTP libraries initialize, patch Python's socket.getaddrinfo to
# explicitly force socket.AF_INET (IPv4 only).
# Permanently eliminates: SMTP transmission failed: OSError: [Errno 101] Network is unreachable
# =====================================================================
import socket

if not getattr(socket, "_nexus_ipv4_enforced", False):
    _orig_getaddrinfo = socket.getaddrinfo

    def _ipv4_getaddrinfo(host, port, *args, **kwargs):
        kwargs.pop("family", None)
        rem = list(args)
        if rem:
            rem[0] = socket.AF_INET
            return _orig_getaddrinfo(host, port, *rem, **kwargs)
        return _orig_getaddrinfo(host, port, socket.AF_INET, **kwargs)

    socket.getaddrinfo = _ipv4_getaddrinfo
    socket._nexus_ipv4_enforced = True
# =====================================================================

import os
import sys
import logging
from pathlib import Path

# Configure root logging to stdout BEFORE anything else loads
# This ensures all logger.info()/logger.error() calls appear in Railway Deploy Logs
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    force=True,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)

import uvicorn
from api.app import app
from app import start_auxiliary_port_forwarder


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")

    # Start multi-port bridge for standard web proxy ports (8000, 8080, 3000)
    for aux_port in [8000, 8080, 3000]:
        if aux_port != port:
            start_auxiliary_port_forwarder(aux_port, port)

    print(f"[NEXUS-PULSE] Booting production server on {host}:{port} via main.py (IPv4 Enforced)")
    uvicorn.run("main:app", host=host, port=port, log_level="info")
