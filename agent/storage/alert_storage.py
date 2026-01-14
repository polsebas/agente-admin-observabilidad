import datetime
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, DateTime, select, desc
from sqlalchemy.dialects.postgresql import JSONB

from agent.storage.db import Base, engine, AsyncSessionLocal

class AlertModel(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True)
    fingerprint = Column(String, index=True)
    status = Column(String)
    labels = Column(JSONB)
    annotations = Column(JSONB)
    received_at = Column(DateTime)
    analysis_report = Column(Text)
    is_duplicate = Column(Integer, default=0)


async def init_db() -> None:
    """Crea la tabla si no existe."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_alert(
    alert_id: str,
    fingerprint: str,
    status: str,
    labels: Dict[str, Any],
    annotations: Dict[str, Any],
    received_at: datetime.datetime,
    analysis_report: Optional[str] = None,
    is_duplicate: bool = False,
) -> None:
    """Persiste una alerta analizada."""
    # Asegurar que init_db se haya ejecutado al menos una vez (idea: en startup)
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            alert = AlertModel(
                id=alert_id,
                fingerprint=fingerprint,
                status=status,
                labels=labels,
                annotations=annotations,
                received_at=received_at,
                analysis_report=analysis_report or "",
                is_duplicate=1 if is_duplicate else 0,
            )
            await session.merge(alert)


async def get_recent_by_fingerprint(fingerprint: str, window_minutes: int) -> List[Dict[str, Any]]:
    """Devuelve alertas recientes con el mismo fingerprint."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AlertModel)
            .where(AlertModel.fingerprint == fingerprint, AlertModel.received_at >= cutoff)
            .order_by(AlertModel.received_at.desc())
        )
        rows = result.scalars().all()
        return [_model_to_dict(r) for r in rows]


async def get_alert(alert_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una alerta por ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AlertModel).where(AlertModel.id == alert_id))
        row = result.scalar_one_or_none()
        return _model_to_dict(row) if row else None


async def list_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Lista alertas recientes."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AlertModel).order_by(AlertModel.received_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [_model_to_dict(r) for r in rows]


def _model_to_dict(row: AlertModel) -> Dict[str, Any]:
    return {
        "id": row.id,
        "fingerprint": row.fingerprint,
        "status": row.status,
        "labels": row.labels,
        "annotations": row.annotations,
        "received_at": row.received_at.isoformat() if row.received_at else None,
        "analysis_report": row.analysis_report,
        "is_duplicate": bool(row.is_duplicate),
    }
