from fastapi import APIRouter, HTTPException
from datetime import datetime
import httpx
import os

from backend.schemas import WeatherResponse

router = APIRouter(prefix="/api/weather", tags=["Weather"])

# Configuración por defecto: Talca, Chile
DEFAULT_CITY = os.getenv("WEATHER_CITY", "Talca,CL")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def classify_condition(weather_id: int, description: str) -> str:
    """
    Clasifica el clima de OpenWeatherMap en 3 categorías.
    Referencia: https://openweathermap.org/weather-conditions
    """
    # Lluvia, llovizna, tormenta, nieve
    if weather_id < 700:
        return "rainy"
    # Niebla, neblina, polvo, etc.
    if weather_id < 800:
        return "cloudy"
    # Cielo despejado
    if weather_id == 800:
        return "sunny"
    # Nubes parciales o totales
    return "cloudy"


def classify_time_of_day(hour: int) -> str:
    """Clasifica la hora del día en 3 períodos."""
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 19:
        return "afternoon"
    else:
        return "night"


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(lat: float = None, lon: float = None):
    """
    Consulta el clima actual del usuario.
    - Si el frontend manda lat/lon (GPS del usuario), usa esas coordenadas.
    - Si no, cae al default configurado en .env (Talca, CL).
    """
    if not OPENWEATHER_API_KEY:
        # Modo demo: retorna datos simulados para desarrollo sin API key
        local_hour = datetime.now().hour
        time_of_day = classify_time_of_day(local_hour)
        demo_condition = "cloudy"
        background_key = f"{time_of_day}_{demo_condition}"
        return WeatherResponse(
            city="Tu Ciudad (Demo Mode)",
            temperature=18.0,
            condition=demo_condition,
            condition_raw="broken clouds",
            time_of_day=time_of_day,
            local_hour=local_hour,
            background_key=background_key
        )

    # Si el usuario compartió su ubicación → usar coordenadas reales
    if lat is not None and lon is not None:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "es"
        }
    else:
        # Fallback: ciudad por defecto del .env
        params = {
            "q": DEFAULT_CITY,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "es"
        }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OPENWEATHER_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Error al conectar con OpenWeatherMap: {e.response.status_code}"
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="No se pudo conectar con OpenWeatherMap"
            )

    weather_id = data["weather"][0]["id"]
    description = data["weather"][0]["description"]
    temperature = data["main"]["temp"]
    city_name = data["name"]

    # Usar hora local del servidor (Chile/Talca = UTC-3 o UTC-4)
    # Para mayor precisión se podría usar el offset de la API
    utc_offset_seconds = data.get("timezone", -10800)  # -3h por defecto
    local_timestamp = data["dt"] + utc_offset_seconds
    local_hour = datetime.utcfromtimestamp(local_timestamp).hour

    condition = classify_condition(weather_id, description)
    time_of_day = classify_time_of_day(local_hour)
    background_key = f"{time_of_day}_{condition}"

    return WeatherResponse(
        city=city_name,
        temperature=round(temperature, 1),
        condition=condition,
        condition_raw=description,
        time_of_day=time_of_day,
        local_hour=local_hour,
        background_key=background_key
    )
