from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.agents.observability_team import analyze_payload
from agent.storage import alert_storage

router = APIRouter()


class GrafanaAlert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str] = Field(default_factory=dict)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    fingerprint: str


class GrafanaAlertPayload(BaseModel):
    receiver: Optional[str] = None
    status: str
    alerts: List[GrafanaAlert]
    externalURL: Optional[str] = None


@router.post("/alerts")
async def receive_alert(payload: GrafanaAlertPayload) -> Dict[str, Any]:
    """Recibe webhook de Grafana Alertmanager y dispara análisis."""
    result = await analyze_payload(payload.model_dump())
    return result


@router.get("/alerts/history")
async def get_alert_history(limit: int = 50) -> Dict[str, Any]:
    """Historial de alertas analizadas."""
    alerts = alert_storage.list_alerts(limit=limit)
    return {"alerts": alerts}


@router.get("/reports/{alert_id}")
async def get_report(alert_id: str) -> Dict[str, Any]:
    """Obtiene el reporte markdown de un análisis previo."""
    alert = alert_storage.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return {"alert_id": alert_id, "report": alert.get("analysis_report")}


