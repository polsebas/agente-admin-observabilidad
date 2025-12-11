"""
Funciones auxiliares para consultar Prometheus.
Usa prometheus-api-client para queries instantáneos y de rango.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from prometheus_api_client import PrometheusConnect

from agent.config import AdminAgentConfig

_config = AdminAgentConfig()
_prom = PrometheusConnect(url=_config.prometheus_url, disable_ssl=True)


def query_instant(query: str) -> Any:
    """Ejecuta un query instantáneo a Prometheus."""
    return _prom.custom_query(query)


def query_range(query: str, start: datetime, end: datetime, step: str) -> Any:
    """Ejecuta un query de rango en Prometheus."""
    return _prom.custom_query_range(
        query=query,
        start_time=start,
        end_time=end,
        step=step,
    )


def get_service_health() -> List[Dict[str, Any]]:
    """Devuelve estado up/down de los servicios configurados."""
    res = query_instant('up{job=~"auth-service|stock-service|billing-service|clients-service|logistics-service|reports-service|api-gateway|ia-service"}')
    return res


def get_service_cpu_memory(service: str) -> Dict[str, Any]:
    """Métricas de CPU y memoria de un servicio (promedio 5m)."""
    cpu_query = f'rate(process_cpu_seconds_total{{service="{service}"}}[5m])'
    mem_query = f'process_resident_memory_bytes{{service="{service}"}}'
    return {
        "cpu": query_instant(cpu_query),
        "memory": query_instant(mem_query),
    }


def get_http_error_rate(service: str) -> Any:
    """Tasa de errores 5xx en 5m."""
    query = f'sum(rate(http_requests_received_total{{service="{service}",status=~"5.."}}[5m]))'
    return query_instant(query)


def get_http_latency_p95(service: str) -> Any:
    """Latencia P95 (histogram_quantile) en 5m."""
    query = (
        f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m])) by (le))'
    )
    return query_instant(query)


