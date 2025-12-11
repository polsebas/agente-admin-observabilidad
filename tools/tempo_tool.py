"""
Funciones para consultar Tempo vía API HTTP.
"""
from typing import Any, Dict, List

import requests

from agent.config import AdminAgentConfig

_config = AdminAgentConfig()
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})


def _tempo_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_config.tempo_url}{path}"
    resp = _session.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def search_traces(service: str, tags: Dict[str, str] | None = None, limit: int = 20) -> Dict[str, Any]:
    """Busca traces por service y tags."""
    search = {
        "serviceName": service,
        "tags": tags or {},
        "maxDuration": 0,
        "minDuration": 0,
        "limit": limit,
    }
    url = f"{_config.tempo_url}/api/search"
    resp = _session.post(url, json=search, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_trace(trace_id: str) -> Dict[str, Any]:
    """Obtiene un trace completo por ID."""
    return _tempo_get(f"/api/traces/{trace_id}", params={})


def get_slow_traces(service: str, min_duration_ms: int = 1000, limit: int = 10) -> Dict[str, Any]:
    """Traces lentos filtrados por duración mínima."""
    tags = {"duration_ms": f">{min_duration_ms}"}
    return search_traces(service=service, tags=tags, limit=limit)


def get_error_traces(service: str, limit: int = 10) -> Dict[str, Any]:
    """Traces con errores."""
    tags = {"status_code": "ERROR"}
    return search_traces(service=service, tags=tags, limit=limit)


