"""Tools de clasificación y deduplicación de alertas para Agno."""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from agno.tools import tool

from agent.config import AdminAgentConfig
from agent.storage import alert_storage

_config = AdminAgentConfig()


def _classify_alert_severity_raw(
    labels: Optional[Dict[str, str]] = None, annotations: Optional[Dict[str, str]] = None
) -> str:
    labels = labels or {}
    sev = labels.get("severity", "").lower()
    if sev in {"critical", "crit", "p0", "p1"}:
        return "critical"
    if sev in {"major", "high", "p2"}:
        return "major"
    if sev in {"minor", "medium", "p3"}:
        return "minor"
    if sev in {"warning", "warn", "p4"}:
        return "warning"
    text = " ".join((annotations or {}).values()).lower()
    if any(k in text for k in ["outage", "unreachable", "panic"]):
        return "critical"
    if any(k in text for k in ["error rate", "5xx", "timeout"]):
        return "major"
    return "info"


@tool
def classify_alert_severity(
    labels: Optional[Dict[str, str]] = None, annotations: Optional[Dict[str, str]] = None
) -> str:
    """Clasifica severidad usando labels/annotations estándar."""
    return _classify_alert_severity_raw(labels, annotations)


async def _check_alert_history_raw(fingerprint: str, window_minutes: int | None = None) -> List[Dict[str, Any]]:
    """Helper interno: Devuelve alertas recientes con mismo fingerprint."""
    minutes = window_minutes or _config.alert_dedup_window_minutes
    return await alert_storage.get_recent_by_fingerprint(fingerprint, minutes)


async def _deduplicate_alerts_raw(fingerprint: str, window_minutes: int | None = None) -> bool:
    """Helper interno: Indica si la alerta es duplicada en la ventana dada."""
    recent = await _check_alert_history_raw(fingerprint, window_minutes)
    return len(recent) > 0


@tool
async def check_alert_history(fingerprint: str, window_minutes: int | None = None) -> List[Dict[str, Any]]:
    """Devuelve alertas recientes con mismo fingerprint."""
    return await _check_alert_history_raw(fingerprint, window_minutes)


@tool
async def deduplicate_alerts(fingerprint: str, window_minutes: int | None = None) -> bool:
    """Indica si la alerta es duplicada en la ventana dada."""
    return await _deduplicate_alerts_raw(fingerprint, window_minutes)


def _enrich_alert_context_raw(alert: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper interno: Enriquece la alerta con servicio, instancia y timeframe."""
    alert = alert or {}
    labels = alert.get("labels", {}) or {}
    annotations = alert.get("annotations", {}) or {}
    service = labels.get("service") or labels.get("job") or annotations.get("service")
    instance = labels.get("instance")
    severity = _classify_alert_severity_raw(labels, annotations)
    starts_at = alert.get("startsAt") or alert.get("starts_at")
    ends_at = alert.get("endsAt") or alert.get("ends_at")
    return {
        "alertname": labels.get("alertname"),
        "service": service,
        "instance": instance,
        "severity": severity,
        "starts_at": starts_at,
        "ends_at": ends_at,
    }


@tool
def enrich_alert_context(alert: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Enriquece la alerta con servicio, instancia y timeframe."""
    return _enrich_alert_context_raw(alert)


async def persist_alert(
    alert: Dict[str, Any],
    analysis_report: Optional[str] = None,
    is_duplicate: bool = False,
) -> str:
    """Guarda la alerta en storage y devuelve el ID asignado."""
    alert_id = alert.get("fingerprint") or str(uuid.uuid4())
    fingerprint = alert.get("fingerprint", alert_id)
    # Ensure correct datetime object in DB
    received_at = datetime.datetime.utcnow()
    await alert_storage.save_alert(
        alert_id=alert_id,
        fingerprint=fingerprint,
        status=alert.get("status", "unknown"),
        labels=alert.get("labels", {}),
        annotations=alert.get("annotations", {}),
        received_at=received_at,
        analysis_report=analysis_report,
        is_duplicate=is_duplicate,
    )
    return alert_id
