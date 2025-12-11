"""Agente Triage: correlaciona métricas, logs y traces."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import AsyncSqliteDb

from agent.config import AdminAgentConfig
from agent.tools import observability_tools

_config = AdminAgentConfig()

triage_agent = Agent(
    name="TriageAgent",
    role="Correlacionar métricas, logs y traces para identificar causa raíz",
    description=(
        "Agente de correlación técnica que analiza señales de observabilidad (métricas de Prometheus, "
        "logs de Loki, traces de Tempo) para identificar la causa raíz de alertas. Realiza análisis "
        "temporal, busca patrones comunes y correlaciona eventos para determinar el origen del problema."
    ),
    model=OpenAIChat(id=_config.agno_model),
    db=AsyncSqliteDb(db_file="./agno.db"),
    debug_mode=True,
    add_history_to_context=True,
    num_history_runs=2,
    dependencies={
        "monitored_services": _config.monitored_services,
        "latency_threshold_ms": _config.latency_threshold_ms,
        "error_rate_threshold": _config.error_rate_threshold,
    },
    add_dependencies_to_context=True,
    tools=[
        observability_tools.query_prometheus_metrics,
        observability_tools.query_prometheus_range,
        observability_tools.get_service_health,
        observability_tools.get_http_error_rate,
        observability_tools.get_http_latency_p95,
        observability_tools.query_loki_logs,
        observability_tools.query_loki_by_trace,
        observability_tools.query_tempo_traces,
        observability_tools.get_tempo_trace,
    ],
    instructions=[
        "Sos el agente de correlación técnica. Tu objetivo es encontrar la causa raíz de la alerta usando métricas, logs y traces.",
        "PASO 1: Determinar timeframe - usá startsAt de la alerta y analizá los últimos 15 minutos (ajustable según severidad: critical=30m, major=15m, minor=10m)",
        "PASO 2: Consultar métricas - obtené error_rate (5xx), latency P95, status del servicio con Prometheus",
        "PASO 3: Buscar logs - filtrá logs de error del servicio en Loki con query '{service=\"X\"} |= \"ERROR\" or \"FATAL\"'",
        "PASO 4: Analizar traces - buscá traces lentos (>1s) o con errores en Tempo",
        "PASO 5: Correlacionar - identificá patrones temporales (¿el error_rate subió antes que la latencia?), stacktraces comunes, requests fallidos",
        "FORMATO DE SALIDA: JSON con {metrics: {error_rate, latency_p95, status}, logs: {sample_errors[], error_patterns[]}, traces: {slow_traces[], failed_requests[]}, findings: {root_cause, evidence[], confidence}}",
    ],
    expected_output=(
        "JSON estructurado con secciones: "
        "metrics (error_rate, latency_p95, status), "
        "logs (sample_errors array, error_patterns array), "
        "traces (slow_traces array, failed_requests array), "
        "findings (root_cause string, evidence array, confidence High|Medium|Low)"
    ),
    markdown=True,
)


