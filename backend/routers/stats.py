from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from backend.database import get_db
from backend.models import DailyStats
from backend.schemas import StatsUpdate, StatsResponse

router = APIRouter(prefix="/api/stats", tags=["Statistics"])


def get_or_create_today(db: Session) -> DailyStats:
    """Obtiene el registro de hoy o lo crea si no existe."""
    today = date.today()
    record = db.query(DailyStats).filter(DailyStats.date == today).first()
    if not record:
        record = DailyStats(date=today, cycles_completed=0, total_seconds_studied=0.0)
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


@router.get("/today", response_model=StatsResponse)
def get_today_stats(db: Session = Depends(get_db)):
    """Retorna las estadísticas del día actual."""
    record = get_or_create_today(db)
    return StatsResponse(
        date=record.date,
        cycles_completed=record.cycles_completed,
        total_seconds_studied=record.total_seconds_studied,
        total_hours_studied=round(record.total_seconds_studied / 3600, 2)
    )


@router.post("/update", response_model=StatsResponse)
def update_stats(payload: StatsUpdate, db: Session = Depends(get_db)):
    """
    Actualiza las estadísticas del día.
    Llamar al completar un ciclo o al pausar/terminar una sesión de estudio.
    """
    record = get_or_create_today(db)
    record.total_seconds_studied += payload.seconds_studied
    if payload.cycle_completed:
        record.cycles_completed += 1
    db.commit()
    db.refresh(record)
    return StatsResponse(
        date=record.date,
        cycles_completed=record.cycles_completed,
        total_seconds_studied=record.total_seconds_studied,
        total_hours_studied=round(record.total_seconds_studied / 3600, 2)
    )


@router.delete("/reset", response_model=StatsResponse)
def reset_today_stats(db: Session = Depends(get_db)):
    """Reinicia las estadísticas del día (útil para testing)."""
    record = get_or_create_today(db)
    record.cycles_completed = 0
    record.total_seconds_studied = 0.0
    db.commit()
    db.refresh(record)
    return StatsResponse(
        date=record.date,
        cycles_completed=record.cycles_completed,
        total_seconds_studied=record.total_seconds_studied,
        total_hours_studied=0.0
    )
