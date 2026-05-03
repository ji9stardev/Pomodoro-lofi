"""
Pomodoro Lo-Fi — Backend FastAPI v3.1
"""

import os
from pathlib import Path
from dotenv import load_dotenv

APP_VERSION = "3.1.0"

# Cargar variables de entorno
load_dotenv(Path(__file__).parent / "backend" / ".env")
load_dotenv(Path(__file__).parent / ".env")

# Fallback demo
_defaults = {
    "DISCORD_CLIENT_ID":     "demo_discord_client_id",
    "DISCORD_CLIENT_SECRET": "demo_discord_client_secret",
    "DISCORD_REDIRECT_URI":  "http://localhost:8000/api/discord/callback",
    "OPENWEATHER_API_KEY":   "demo_openweather_key",
    "WEATHER_CITY":          "",
}
for _k, _v in _defaults.items():
    os.environ.setdefault(_k, _v)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base
from backend.routers import stats, weather, discord

# Importar routers opcionales
try:
    from backend.routers import ai_theme
    _has_ai = True
except ImportError:
    _has_ai = False

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pomodoro Lo-Fi API",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats.router)
app.include_router(weather.router)
app.include_router(discord.router)
if _has_ai:
    app.include_router(ai_theme.router)

# Frontend
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        # Modo mantenimiento
        if os.getenv("MAINTENANCE_MODE", "false").lower() == "true":
            maintenance_file = frontend_path / "maintenance.html"
            if maintenance_file.exists():
                return FileResponse(str(maintenance_file))
            # Fallback inline si el archivo no existe
            return HTMLResponse(content="""
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Mantenimiento</title>
<style>body{background:#1a0040;color:white;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;flex-direction:column;gap:16px;}
h1{font-size:2rem;}p{color:rgba(255,255,255,0.5);}</style></head>
<body><div style="font-size:4rem">⚙️</div><h1>En Mantenimiento</h1><p>Volvemos pronto 🍅</p></body></html>
""")
        return FileResponse(str(frontend_path / "index.html"))


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "maintenance": os.getenv("MAINTENANCE_MODE", "false").lower() == "true",
        "discord_configured": bool(os.getenv("DISCORD_CLIENT_ID") and os.getenv("DISCORD_CLIENT_ID") != "demo_discord_client_id"),
        "weather_configured": bool(os.getenv("OPENWEATHER_API_KEY") and os.getenv("OPENWEATHER_API_KEY") != "demo_openweather_key"),
    }


@app.get("/version", tags=["System"])
async def get_version():
    return {"version": APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")