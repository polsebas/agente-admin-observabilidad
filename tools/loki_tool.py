"""
Funciones para consultar Loki vía API HTTP.
"""
import datetime
from typing import Any, Dict, List, Optional

import requests

from agent.config import AdminAgentConfig
from agent.utils.http_client import shared_client

_config = AdminAgentConfig()

def _loki_query(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_config.loki_url}{path}"
    resp = shared_client.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def query_logs(query: str, limit: int = 100) -> Dict[str, Any]:
    """Consulta logs con la API query_range."""
    params = {
        "query": query,
        "limit": limit,
        "direction": "backward",
    }
    return _loki_query("/loki/api/v1/query", params)


def get_error_logs(service: str, since: str = "5m") -> Dict[str, Any]:
    """Logs de error recientes de un servicio."""
    query = f'{{service="{service}", level=~"error|ERROR|critical|CRITICAL"}}'
    params = {
        "query": query,
        "limit": 200,
        "start": _since_to_ns(since),
        "direction": "backward",
    }
    return _loki_query("/loki/api/v1/query_range", params)


def search_logs(service: str, keyword: str, since: str = "1h") -> Dict[str, Any]:
    """Búsqueda por keyword en logs del servicio."""
    query = f'{{service="{service}"}} |= "{keyword}"'
    params = {
        "query": query,
        "limit": 200,
        "start": _since_to_ns(since),
        "direction": "backward",
    }
    return _loki_query("/loki/api/v1/query_range", params)


def get_trace_logs(trace_id: str) -> Dict[str, Any]:
    """Devuelve logs asociados a un trace_id."""
    query = f'{{traceID="{trace_id}"}}'
    return query_logs(query, limit=300)


def _since_to_ns(since: str) -> int:
    """Convierte una ventana relativa (e.g., '5m', '1h') a nanosegundos timestamp."""
    now = datetime.datetime.utcnow()
    delta = _parse_delta(since)
    dt = now - delta
    return int(dt.timestamp() * 1e9)


def _parse_delta(since: str) -> datetime.timedelta:
    unit = since[-1]
    value = int(since[:-1])
    if unit == "s":
        return datetime.timedelta(seconds=value)
    if unit == "m":
        return datetime.timedelta(minutes=value)
    if unit == "h":
        return datetime.timedelta(hours=value)
    if unit == "d":
        return datetime.timedelta(days=value)
    # default minutes
    return datetime.timedelta(minutes=value)


