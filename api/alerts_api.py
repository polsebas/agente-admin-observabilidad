from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.agents.observability_team import analyze_payload
from agent.models.alert import AlertmanagerWebhook
from agent.storage import alert_storage

router = APIRouter()


@router.post("/alerts")
async def receive_alert(payload: AlertmanagerWebhook) -> Dict[str, Any]:
    """Recibe webhook de Grafana Alertmanager y dispara análisis."""
    result = await analyze_payload(payload.model_dump(mode='json'))
    return result


@router.get("/alerts/history")
async def get_alert_history(limit: int = 50) -> Dict[str, Any]:
    """Historial de alertas analizadas."""
    alerts = await alert_storage.list_alerts(limit=limit)
    return {"alerts": alerts}


@router.get("/reports/{alert_id}")
async def get_report(alert_id: str) -> Dict[str, Any]:
    """Obtiene el reporte markdown de un análisis previo."""
    alert = await alert_storage.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return {"alert_id": alert_id, "report": alert.get("analysis_report")}


