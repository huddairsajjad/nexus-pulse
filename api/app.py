"""
H.Huddair's Nexus-Pulse - Level 2
FastAPI Application Entrypoint & Static GUI Server
Location: Desktop/rabbi/api/app.py
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import enforce_security_boundary
from database.db_engine import get_db_engine
from auth.user_manager import get_user_manager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UI_DIR = PROJECT_ROOT / "ui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Enforce Anti-Theft Licensing
    fp = generate_machine_fingerprint()
    print("=" * 68)
    print("  H.HUDDAIR'S NEXUS-PULSE [LEVEL 2 ENTERPRISE] - INITIALIZING ENGINE")
    print("=" * 68)
    print(f"  Host Hardware ID: {fp['machine_id']}")
    try:
        license_info = enforce_security_boundary(fp["machine_id"])
        print(f"  Security Status : LICENSED (Client: {license_info.get('client_name')}, Tier: {license_info.get('tier')})")
    except Exception as e:
        print(f"  SECURITY ALERT  : {e}")
        raise

    # Initialize DB schema
    db = get_db_engine()
    um = get_user_manager()
    print(f"  Database Engine : OPERATIONAL ({db.db_path.name})")
    if um.has_admin():
        print(f"  User Auth Store : READY (Administrator Initialized)")
    else:
        print(f"  User Auth Store : FRESH (Clean Production State - Awaiting First-Run Admin Setup)")
    print(f"  GUI Dashboard   : READY at http://127.0.0.1:8000/")
    print("=" * 68)
    yield
    print("  Shutting down Nexus-Pulse Level 2 Core Engine...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="H.Huddair's Nexus-Pulse (Level 2 Enterprise)",
        description="Autonomous Multi-Agent B2B Lead Engine with Anti-Theft Hardware Protection & Human Approval Gate",
        version="2.0.0",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    app.include_router(router)

    # Mount UI Static directory
    if UI_DIR.exists():
        app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")

    # Serve main GUI application at root
    @app.get("/")
    def serve_gui():
        index_file = UI_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {
            "system": "H.Huddair's Nexus-Pulse",
            "tier": "Level-2-Enterprise",
            "status": "ONLINE",
            "api_docs": "/docs"
        }

    return app


app = create_app()
