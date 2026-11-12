"""
H.Huddair's Nexus-Pulse - Level 2
FastAPI Application Entrypoint & Static GUI Server
Location: Desktop/rabbi/api/app.py
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router, health_check, get_current_user
from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import enforce_security_boundary
from database.db_engine import get_db_engine
from auth.user_manager import get_user_manager
from vault.vault_manager import get_vault_manager

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
        expose_headers=["Content-Disposition"]
    )

    # Mount API routes
    app.include_router(router)

    # Mount UI Static directory
    if UI_DIR.exists():
        app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")

    # Root Health Check telemetry endpoint
    @app.get("/health", tags=["System"])
    def root_health():
        return health_check()

    # PWA Manifest
    @app.get("/manifest.json", tags=["PWA"])
    def serve_manifest():
        manifest_file = UI_DIR / "manifest.json"
        if manifest_file.exists():
            return FileResponse(manifest_file, media_type="application/manifest+json")
        raise HTTPException(status_code=404, detail="Manifest not found")

    # PWA Service Worker (served at root for full / scope)
    @app.get("/sw.js", tags=["PWA"])
    def serve_sw():
        sw_file = UI_DIR / "sw.js"
        if sw_file.exists():
            return FileResponse(
                sw_file,
                media_type="application/javascript",
                headers={
                    "Service-Worker-Allowed": "/",
                    "Cache-Control": "no-cache"
                }
            )
        raise HTTPException(status_code=404, detail="Service worker not found")

    # Favicon
    @app.get("/favicon.ico", tags=["PWA"])
    def serve_favicon():
        fav_file = UI_DIR / "assets" / "favicon.ico"
        if fav_file.exists():
            return FileResponse(fav_file, media_type="image/x-icon")
        return Response(status_code=204)

    # Root file download fallbacks
    @app.get("/backup/download", tags=["Data Export"])
    @app.post("/backup/download", tags=["Data Export"])
    @app.get("/leads/export", tags=["Data Export"])
    @app.post("/leads/export", tags=["Data Export"])
    def root_download_export(format: Optional[str] = "json", current_user: Dict[str, Any] = Depends(get_current_user)):
        from .routes import backup_and_download
        return backup_and_download(format=format, current_user=current_user)

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
