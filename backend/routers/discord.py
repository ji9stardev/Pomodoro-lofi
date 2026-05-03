from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os
from datetime import datetime, timedelta

from backend.schemas import DiscordUser

router = APIRouter(prefix="/api/discord", tags=["Discord"])

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/api/discord/callback")

DISCORD_API_BASE = "https://discord.com/api/v10"
SCOPES = "identify"

# Almacenamiento en memoria del usuario autenticado
_discord_store: dict = {}


@router.get("/login")
def discord_login():
    """Redirige al flujo OAuth2 de Discord."""
    if not DISCORD_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Discord no configurado. Agrega DISCORD_CLIENT_ID al .env")

    auth_url = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def discord_callback(code: str = None, error: str = None):
    """Callback de Discord OAuth2. Intercambia código por tokens y obtiene perfil."""
    if error or not code:
        raise HTTPException(status_code=400, detail=f"Error en autorización Discord: {error}")

    async with httpx.AsyncClient() as client:
        # 1. Intercambiar código por token
        token_response = await client.post(
            f"{DISCORD_API_BASE}/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Error al obtener token de Discord")

        token_data = token_response.json()
        access_token = token_data["access_token"]

        # 2. Obtener datos del usuario
        user_response = await client.get(
            f"{DISCORD_API_BASE}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Error al obtener perfil de Discord")

        user_data = user_response.json()

    user_id = user_data["id"]
    username = user_data.get("global_name") or user_data.get("username", "Unknown")
    discriminator = user_data.get("discriminator", "0")
    avatar_hash = user_data.get("avatar")

    # Construir URL del avatar
    if avatar_hash:
        ext = "gif" if avatar_hash.startswith("a_") else "png"
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=128"
    else:
        # Avatar por defecto de Discord
        default_index = (int(discriminator) % 5) if discriminator != "0" else (int(user_id) >> 22) % 6
        avatar_url = f"https://cdn.discordapp.com/embed/avatars/{default_index}.png"

    _discord_store["username"] = username
    _discord_store["avatar_url"] = avatar_url
    _discord_store["user_id"] = user_id
    # Discord no expone el estado de presencia vía REST API sin bots
    # Se mostrará "online" por defecto al conectarse
    _discord_store["status"] = "online"
    _discord_store["connected"] = True

    return RedirectResponse(url="/?discord=connected")


@router.get("/me", response_model=DiscordUser)
def get_discord_user():
    """
    Retorna la información del usuario de Discord autenticado.
    
    Nota: El estado de presencia (online/idle/dnd) no está disponible
    via REST API pública sin un bot de Discord. Se muestra 'online' 
    al conectarse. Para presencia real, se requiere Discord Gateway WebSocket.
    """
    if not _discord_store.get("connected"):
        return DiscordUser(connected=False)

    return DiscordUser(
        username=_discord_store.get("username"),
        avatar_url=_discord_store.get("avatar_url"),
        status=_discord_store.get("status", "online"),
        connected=True
    )


@router.post("/logout")
def discord_logout():
    """Desconecta la sesión de Discord."""
    _discord_store.clear()
    return {"status": "disconnected"}
