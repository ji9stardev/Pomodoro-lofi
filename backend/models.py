from sqlalchemy import Column, Integer, Float, Date
from datetime import date
from backend.database import Base


class DailyStats(Base):
    """
    Almacena estadísticas de pomodoro por día.
    Un registro por fecha. Se actualiza con UPSERT.
    """
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, default=date.today)
    cycles_completed = Column(Integer, default=0, nullable=False)
    # Segundos totales estudiados (se convierte a horas en el frontend)
    total_seconds_studied = Column(Float, default=0.0, nullable=False)
