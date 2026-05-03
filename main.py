"""
Pomodoro Lo-Fi — Backend FastAPI
================================
Servidor principal que orquesta todos los módulos:
  - Estadísticas diarias (SQLite)
  - Clima + hora del día (OpenWeatherMap)
  - Discord Profile (OAuth2)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno (busca en backend/.env y en la raíz)
load_dotenv(Path(__file__).parent / "backend" / ".env")
load_dotenv(Path(__file__).parent / ".env")

# ─── Fallback demo: se usan si no hay .env con claves reales ─────────────────
# Para producción, reemplaza estos valores con tus claves reales en un .env
_defaults = {
    "SPOTIFY_CLIENT_ID":     "demo_spotify_client_id",
    "SPOTIFY_CLIENT_SECRET": "demo_spotify_client_secret",
    "SPOTIFY_REDIRECT_URI":  "http://localhost:8000/api/spotify/callback",
    "DISCORD_CLIENT_ID":     "demo_discord_client_id",
    "DISCORD_CLIENT_SECRET": "demo_discord_client_secret",
    "DISCORD_REDIRECT_URI":  "http://localhost:8000/api/discord/callback",
    "OPENWEATHER_API_KEY":   "demo_openweather_key",
    "WEATHER_CITY":          "Talca,CL",
}
for _k, _v in _defaults.items():
    os.environ.setdefault(_k, _v)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base
from backend.routers import stats, weather, discord

# ─── Crear tablas en SQLite ───────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── Aplicación FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="Pomodoro Lo-Fi API",
    description="Backend para la aplicación de reloj Pomodoro con integraciones de Spotify, Discord y Clima.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(stats.router)
app.include_router(weather.router)

app.include_router(discord.router)

# ─── Archivos estáticos del frontend ─────────────────────────────────────────
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Sirve el index.html del frontend o la página de mantenimiento."""
        if os.getenv("MAINTENANCE_MODE", "false").lower() == "true":
            return FileResponse(str(frontend_path / "maintenance.html"))
        return FileResponse(str(frontend_path / "index.html"))


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Verifica que el servidor esté funcionando."""
    return {
        "status": "ok",
        "discord_configured": bool(os.getenv("DISCORD_CLIENT_ID")),
        "weather_configured": bool(os.getenv("OPENWEATHER_API_KEY")),
    }


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )