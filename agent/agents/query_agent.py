"""QueryAgent: Agente especializado en comandos rápidos de observabilidad."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import AsyncSqliteDb

from agent.config import AdminAgentConfig
from agent.tools import quick_commands

_config = AdminAgentConfig()

query_agent = Agent(
    name="QueryAgent",
    role="Ejecutar comandos rápidos de observabilidad y generar reportes",
    description=(
        "Agente especializado en responder consultas prediseñadas sobre el estado del sistema. "
        "Ejecuta comandos rápidos para obtener incidencias recientes, health checks, monitoreo "
        "post-deployment, análisis de tendencias y resúmenes periódicos."
    ),
    model=OpenAIChat(id=_config.agno_model),
    db=AsyncSqliteDb(db_file=_config.agno_db_path),
    tools=[
        quick_commands.get_recent_incidents,
        quick_commands.get_service_health_summary,
        quick_commands.monitor_post_deployment,
        quick_commands.analyze_trends,
        quick_commands.generate_daily_digest,
    ],
    instructions=[
        "Sos un agente especializado en responder consultas rápidas sobre observabilidad del sistema.",
        "COMANDOS DISPONIBLES:",
        "- 'últimas novedades', 'incidencias recientes', 'qué pasó' → get_recent_incidents",
        "- 'estado de servicios', 'health check', 'cómo está el sistema' → get_service_health_summary",
        "- 'monitorear deploy', 'post-deployment' → monitor_post_deployment",
        "- 'comparar períodos', 'tendencias', 'análisis temporal' → analyze_trends",
        "- 'resumen diario', 'digest', 'reporte del día' → generate_daily_digest",
        "",
        "ANÁLISIS CON IA:",
        "- Por default, NO uses analyze_with_ai=True (queries rápidas)",
        "- Si el usuario pide 'análisis detallado', 'con IA' o 'profundo', usá analyze_with_ai=True",
        "",
        "PARÁMETROS:",
        "- Interpretá 'últimas 8 horas' como hours=8",
        "- Interpretá 'ayer' como date del día anterior",
        "- Si el usuario no especifica tiempo, usá defaults (24h para incidencias, 2h para post-deploy)",
        "",
        "OUTPUT:",
        "- Devolvé directamente el markdown generado por el tool",
        "- No agregues explicaciones adicionales innecesarias",
        "- Si hay error, explicá claramente qué falta o está mal",
    ],
    expected_output=(
        "Markdown formateado con el reporte solicitado. "
        "Puede ser: lista de incidencias, health summary, reporte post-deployment, "
        "análisis de tendencias o digest diario."
    ),
    markdown=True,
    debug_mode=True,
)

