"""Equipo de observabilidad que orquesta el flujo de análisis."""

import json
from typing import Any, Dict, List

from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.db.sqlite import AsyncSqliteDb

from agent.agents.report_agent import report_agent
from agent.agents.triage_agent import triage_agent
from agent.agents.watchdog_agent import watchdog_agent
from agent.tools import alert_tools
from agent.config import AdminAgentConfig

_config = AdminAgentConfig()

def _normalize_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza claves comunes del payload de Grafana."""
    return {
        "status": alert.get("status"),
        "labels": alert.get("labels") or {},
        "annotations": alert.get("annotations") or {},
        "startsAt": alert.get("startsAt") or alert.get("starts_at"),
        "endsAt": alert.get("endsAt") or alert.get("ends_at"),
        "fingerprint": alert.get("fingerprint"),
    }


async def analyze_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecuta clasificación, triage y reporte para una alerta."""
    alert_norm = _normalize_alert(alert)

    # Usar helpers internos en vez de tools directamente
    severity = alert_tools._classify_alert_severity_raw(
        alert_norm["labels"], alert_norm["annotations"]
    )
    is_duplicate = await alert_tools._deduplicate_alerts_raw(alert_norm["fingerprint"])
    context = alert_tools._enrich_alert_context_raw(alert_norm)

    watchdog_summary = {
        "severity": severity,
        "is_duplicate": is_duplicate,
        "context": context,
    }

    triage_result = "Alerta marcada como duplicada; triage omitido."
    if not is_duplicate:
        triage_response = await triage_agent.arun(
            input=(
                "Correlacioná métricas, logs y traces de esta alerta. "
                "Devolvé JSON con metrics, logs, traces y findings.\n\n"
                f"{json.dumps(alert_norm)}"
            )
        )
        # Extraer solo el contenido del mensaje
        triage_result = triage_response.content if hasattr(triage_response, 'content') else str(triage_response)

    report_response = await report_agent.arun(
        input=(
            "Generá un reporte markdown claro con timeline, evidencia y próximos pasos. "
            "Usá el triage como evidencia.\n\n"
            f"Alert: {json.dumps({**alert_norm, **watchdog_summary})}\n\n"
            f"Triage: {triage_result}"
        )
    )
    # Extraer solo el contenido del mensaje
    report_result = report_response.content if hasattr(report_response, 'content') else str(report_response)

    alert_id = await alert_tools.persist_alert(
        {**alert_norm, **watchdog_summary},
        analysis_report=str(report_result),
        is_duplicate=is_duplicate,
    )

    return {
        "alert_id": alert_id,
        "watchdog": watchdog_summary,
        "triage": triage_result,
        "report": report_result,
    }


async def analyze_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa un payload completo de Grafana Alertmanager."""
    alerts: List[Dict[str, Any]] = payload.get("alerts") or []
    results = []
    for alert in alerts:
        result = await analyze_alert(alert)
        results.append(result)
    return {"alerts": results}


observability_team = Team(
    members=[watchdog_agent, triage_agent, report_agent],
    name="ObservabilityTeam",
    role="Orquestar análisis de alertas",
    description=(
        "Equipo de análisis de alertas que coordina tres agentes especializados: "
        "Watchdog (clasificación y deduplicación), Triage (correlación de métricas/logs/traces), "
        "y Report (síntesis y generación de reportes). El equipo sigue un flujo secuencial "
        "donde cada agente depende del output del anterior para generar análisis completos de incidentes."
    ),
    model=OpenAIChat(id=_config.agno_model),
    db=AsyncSqliteDb(db_file=_config.agno_db_path),
    instructions=[
        "Coordinás el análisis de alertas de Grafana en tres fases secuenciales:",
        "FASE 1: Delegá a WatchdogAgent para clasificar severidad y detectar duplicados. Este agente devuelve {severity, is_duplicate, context}",
        "FASE 2: Si no es duplicado (is_duplicate=false), delegá a TriageAgent para correlacionar métricas/logs/traces. Este agente devuelve {metrics, logs, traces, findings}",
        "FASE 3: Delegá a ReportAgent para generar reporte markdown final usando los outputs de Watchdog y Triage",
        "IMPORTANTE: No saltees fases, cada agente depende del output del anterior",
        "Si WatchdogAgent marca como duplicado, omití el TriageAgent y delegá directamente al ReportAgent con un reporte simplificado",
        "Analizá las respuestas de cada agente antes de proceder al siguiente",
    ],
    expected_output=(
        "JSON con estructura: {alert_id: str, watchdog: {severity, is_duplicate, context}, "
        "triage: {metrics, logs, traces, findings} | str (si duplicado), "
        "report: markdown completo con Alert Summary, Timeline, Evidence, Root Cause Analysis, Next Steps}"
    ),
    additional_context=f"""
## SLOs y Thresholds Críticos
- Availability target: 99.9% uptime (máximo 43 minutos downtime/mes)
- Error rate threshold: < {_config.error_rate_threshold * 100}% (configurable)
- Latency P95 threshold: < {_config.latency_threshold_ms}ms (configurable)
- Latency P99 threshold: < {_config.latency_threshold_ms * 2}ms

## Servicios Monitoreados y Criticidad
Servicios configurados: (Descubrimiento dinámico habilitado)

Criticidad por tipo:
- Critical: Servicios core (auth, payment, api-gateway) - impacto inmediato en usuarios/revenue
- Major: Servicios de backend - degradación visible pero no bloqueante
- Minor: Servicios de soporte - impacto mínimo o diferido

## Runbooks y Documentación
- Alerta duplicada: Consolidar con alerta padre, NO re-analizar, referenciar ID padre
- Deployment history: Revisar últimas 24-48h para alertas Critical/Major
- Postmortems: Buscar patrones similares en incidentes históricos

## On-Call y Escalation (referencia para reportes)
- Severidad Critical: Mencionar necesidad de notificación inmediata al on-call
- Severidad Major: Mencionar notificación al team lead dentro de 15 minutos
- Severidad Minor: Sugerir creación de ticket para siguiente día laboral
- Alertas duplicadas: NO escalar, consolidar con alerta padre

Contactos por servicio (incluir en reportes cuando sea relevante):
- auth-service: @team-auth
- payment-service: @team-payments
- api-gateway: @team-gateway
- infrastructure: @team-sre

## Dependencias entre Servicios (para análisis de causa raíz)
Dependencias conocidas:
- auth-service → postgres, redis-cache, ldap/identity-provider
- payment-service → postgres, external payment APIs (Stripe/PayPal), message queue
- api-gateway → todos los servicios backend

Patrones de fallo en cascada:
- Si postgres falla → esperar errores en auth-service, payment-service, user-service
- Si redis falla → aumento de latencia en auth-service (degradación, NO outage completo)
- Si message queue falla → payment-service puede bufferear localmente (capacidad limitada)

## Políticas de Análisis (Fase 1 - Solo Análisis)
IMPORTANTE:
- NUNCA sugerir acciones automáticas (restart, scale, rollback, runbooks) en reportes
- SIEMPRE incluir evidencia de al menos 2 fuentes (metrics+logs o metrics+traces)
- Nivel de confianza OBLIGATORIO en Root Cause Analysis: High/Medium/Low con justificación
- Incluir comandos/queries específicas en Next Steps (PromQL, LogQL, SQL)
- Timeline siempre en UTC con formato ISO 8601
- Lenguaje técnico pero claro (audiencia: SREs y DevOps engineers)

## Retención de Datos Disponibles
- Prometheus: Métricas con retención de 15 días
- Loki: Logs con retención de 7 días
- Tempo: Traces con retención de 3 días (sampling rate: 5%)

Implicación: Para análisis históricos >3 días, solo métricas y logs disponibles.

## Ventana de Deduplicación
- Ventana actual: {_config.alert_dedup_window_minutes} minutos
- Alertas con mismo fingerprint en esta ventana se marcan como duplicadas
- Para alertas duplicadas: referenciar alerta padre y omitir triage completo
""",
    add_history_to_context=True,
    num_history_runs=2,
    max_tool_calls_from_history=10,
    add_datetime_to_context=True,
    show_members_responses=True,
    markdown=True,
    debug_mode=True,
)


