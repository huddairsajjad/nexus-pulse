"""
H.Huddair's Nexus-Pulse [Level 2 Enterprise]
Production Application Entrypoint for Railway & Cloud Containers
Configured with dynamic port binding (0.0.0.0 and $PORT), /health telemetry, CORS, and PWA assets.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from api.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[NEXUS-PULSE] Booting production server on {host}:{port}")
    uvicorn.run("app:app", host=host, port=port, log_level="info")
