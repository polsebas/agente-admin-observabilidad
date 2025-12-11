"""Agente Watchdog: clasifica y deduplica alertas."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import AsyncSqliteDb

from agent.config import AdminAgentConfig
from agent.tools import alert_tools

_config = AdminAgentConfig()

watchdog_agent = Agent(
    name="WatchdogAgent",
    role="Clasificar severidad, deduplicar y enriquecer alertas",
    description=(
        "Agente de primera línea que recibe alertas de Grafana y realiza clasificación inicial. "
        "Enriquece el contexto extrayendo información clave, clasifica la severidad basándose en "
        "labels y annotations, y detecta alertas duplicadas usando fingerprints para evitar análisis redundantes."
    ),
    model=OpenAIChat(id=_config.agno_model),
    db=AsyncSqliteDb(db_file="./agno.db"),
    debug_mode=True,
    add_history_to_context=True,
    num_history_runs=3,
    tools=[
        alert_tools.classify_alert_severity,
        alert_tools.check_alert_history,
        alert_tools.deduplicate_alerts,
        alert_tools.enrich_alert_context,
    ],
    instructions=[
        "Sos el primer agente en analizar alertas de Grafana.",
        "PASO 1: Enriquecer contexto - extraé service, instance, alertname, severity, summary, description, startsAt, fingerprint",
        "PASO 2: Clasificar severidad - usá labels.severity si existe; sino inferí de annotations: critical (sistema caído), major (error 5xx), minor (warning), info (informativo)",
        "PASO 3: Verificar duplicados - buscá el fingerprint en la ventana de 60 minutos usando check_alert_history",
        "PASO 4: Si es duplicado, marcá con deduplicate_alerts y devolvé is_duplicate=true; si no, devolvé is_duplicate=false",
        "FORMATO DE SALIDA: JSON con {severity: str, is_duplicate: bool, context: {service, instance, alertname, severity, summary, description, startsAt, fingerprint}}",
    ],
    expected_output=(
        "JSON estructurado con campos: severity (critical|major|minor|info), is_duplicate (bool), "
        "context (objeto con service, instance, alertname, severity, summary, description, startsAt, fingerprint)"
    ),
    additional_context=(
        "Niveles de severidad:\n"
        "- critical: Sistema caído, servicio inaccesible, pérdida de datos\n"
        "- major: Errores 5xx, degradación significativa, SLA en riesgo\n"
        "- minor: Warnings, latencia elevada pero tolerable, recursos al límite\n"
        "- info: Notificaciones informativas, eventos esperados\n\n"
        "Ventana de deduplicación: 60 minutos (configurable en ALERT_DEDUP_WINDOW)"
    ),
    markdown=True,
)


