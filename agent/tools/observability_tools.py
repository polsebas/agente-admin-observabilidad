"""Wrappers Agno para consultar métricas, logs y traces."""

import datetime
from typing import Any, Dict, List, Optional

from agno.tools import tool

from agent.config import AdminAgentConfig
from tools import loki_tool, prometheus_tool, tempo_tool

_config = AdminAgentConfig()


from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def _execute_with_retry(func, *args, **kwargs):
    return func(*args, **kwargs)


def _safe_call(func, *args, **kwargs) -> Dict[str, Any]:
    try:
        data = _execute_with_retry(func, *args, **kwargs)
        return {"data": data}
    except Exception as exc:
        # En caso de fallo tras retries, devolvemos el error
        return {"error": f"Failed after retries: {str(exc)}"}


@tool
def query_prometheus_metrics(query: str) -> Dict[str, Any]:
    """Ejecuta un query instantáneo a Prometheus."""
    return _safe_call(prometheus_tool.query_instant, query)


@tool
def query_prometheus_range(query: str, minutes: int = 15, step: str = "30s") -> Dict[str, Any]:
    """Ejecuta un query de rango tomando ventana relativa en minutos."""
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=minutes)
    return _safe_call(prometheus_tool.query_range, query, start, end, step)


@tool
def get_service_health() -> Dict[str, Any]:
    """Estado up/down de servicios registrados."""
    return _safe_call(prometheus_tool.get_service_health)


@tool
def get_monitored_services() -> Dict[str, Any]:
    """Descubre dinámicamente la lista de servicios monitoreados."""
    return _safe_call(prometheus_tool.get_monitored_services)


@tool
def get_http_error_rate(service: str) -> Dict[str, Any]:
    """Tasa de errores 5xx en 5m para un servicio."""
    return _safe_call(prometheus_tool.get_http_error_rate, service)


@tool
def get_http_latency_p95(service: str) -> Dict[str, Any]:
    """Latencia P95 en 5m para un servicio."""
    return _safe_call(prometheus_tool.get_http_latency_p95, service)


@tool
def query_loki_logs(service: str, keyword: str | None = None, since: str = "15m") -> Dict[str, Any]:
    """Busca logs de un servicio; opcionalmente filtra por keyword."""
    if keyword:
        return _safe_call(loki_tool.search_logs, service, keyword, since)
    return _safe_call(loki_tool.get_error_logs, service, since)


@tool
def query_loki_by_trace(trace_id: str) -> Dict[str, Any]:
    """Devuelve logs asociados a un trace_id."""
    return _safe_call(loki_tool.get_trace_logs, trace_id)


@tool
def query_tempo_traces(service: str, min_duration_ms: int = 500, limit: int = 20) -> Dict[str, Any]:
    """Busca traces lentos o con errores para un servicio."""
    return _safe_call(tempo_tool.get_slow_traces, service, min_duration_ms, limit)


@tool
def get_tempo_trace(trace_id: str) -> Dict[str, Any]:
    """Obtiene un trace completo por ID."""
    return _safe_call(tempo_tool.get_trace, trace_id)


