from pydantic import BaseModel
from datetime import date
from typing import Optional


class StatsUpdate(BaseModel):
    """Payload para registrar un ciclo o segundos estudiados."""
    seconds_studied: float = 0.0
    cycle_completed: bool = False


class StatsResponse(BaseModel):
    date: date
    cycles_completed: int
    total_seconds_studied: float
    total_hours_studied: float  # Calculado en el servidor

    class Config:
        from_attributes = True


class WeatherResponse(BaseModel):
    city: str
    temperature: float
    condition: str          # "sunny" | "cloudy" | "rainy"
    condition_raw: str      # Descripción original de la API
    time_of_day: str        # "morning" | "afternoon" | "night"
    local_hour: int
    background_key: str     # ej: "morning_sunny", "night_rainy"


class SpotifyTrack(BaseModel):
    is_playing: bool
    track_name: Optional[str] = None
    artist: Optional[str] = None
    album_art: Optional[str] = None
    track_url: Optional[str] = None


class DiscordUser(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[str] = None   # "online" | "idle" | "dnd" | "offline"
    connected: bool = False
