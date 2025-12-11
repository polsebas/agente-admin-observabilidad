"""Tools para generar reportes legibles a partir del análisis."""

import datetime
from typing import Any, Dict, List, Optional

from agno.tools import tool


@tool
def generate_markdown_report(
    alert: Optional[Dict[str, Any]] = None, triage: Optional[Dict[str, Any]] = None
) -> str:
    """Genera un reporte markdown resumido."""
    alert = alert or {}
    triage = triage or {}
    labels = alert.get("labels", {}) or {}
    annotations = alert.get("annotations", {}) or {}
    severity = alert.get("severity", labels.get("severity", "unknown"))
    alertname = labels.get("alertname", "Alert")
    service = labels.get("service") or alert.get("service") or "desconocido"
    started = alert.get("startsAt") or alert.get("starts_at") or ""
    generated = datetime.datetime.utcnow().isoformat() + "Z"

    metrics = triage.get("metrics") or triage.get("prometheus") or {}
    logs = triage.get("logs") or {}
    traces = triage.get("traces") or {}
    findings = triage.get("findings") or triage.get("summary") or ""

    lines: List[str] = [
        f"# Alert Analysis Report",
        f"**Generated**: {generated}",
        f"**Alert**: {alertname} - {service}",
        f"**Severity**: {severity}",
        f"",
        "---",
        "",
        "## Summary",
        annotations.get("summary", "Sin resumen provisto."),
        "",
        "## Timeline",
        f"- Start: {started}",
        "",
        "## Evidence",
        "",
        "### Metrics (Prometheus)",
        f"{metrics}",
        "",
        "### Logs (Loki)",
        f"{logs}",
        "",
        "### Traces (Tempo)",
        f"{traces}",
        "",
        "## Findings",
        f"{findings}",
    ]
    return "\n".join(lines)


@tool
def suggest_next_steps(triage: Optional[Dict[str, Any]] = None) -> List[str]:
    """Sugiere pasos de investigación sin ejecutar acciones."""
    triage = triage or {}
    service = triage.get("service") or "el servicio afectado"
    suggestions = [
        f"Revisar health y dependencias de {service}.",
        "Verificar cambios recientes de despliegue o configuración.",
        "Consultar métricas de base de datos y latencias externas.",
        "Revisar patrones de error en logs y correlacionar con traces lentos.",
    ]
    return suggestions


