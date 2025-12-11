"""
Funciones de solo lectura usando Docker SDK.
"""
from typing import Any, Dict, List, Optional

import docker
from docker.models.containers import Container

from agent.config import AdminAgentConfig

_config = AdminAgentConfig()
_client = docker.DockerClient(base_url=f"unix://{_config.docker_socket}")


def list_containers() -> List[Dict[str, Any]]:
    """Lista contenedores con estado básico."""
    containers = _client.containers.list(all=True)
    return [
        {
            "id": c.short_id,
            "name": c.name,
            "status": c.status,
            "image": c.image.tags,
        }
        for c in containers
    ]


def _get_container(name: str) -> Optional[Container]:
    try:
        return _client.containers.get(name)
    except Exception:
        return None


def get_container_stats(service: str) -> Dict[str, Any]:
    """Devuelve stats en vivo de un contenedor."""
    cont = _get_container(service)
    if not cont:
        return {"error": "container not found"}
    stats = cont.stats(stream=False)
    return stats


def get_container_logs(service: str, tail: int = 100) -> Dict[str, Any]:
    """Obtiene logs recientes del contenedor."""
    cont = _get_container(service)
    if not cont:
        return {"error": "container not found"}
    logs = cont.logs(tail=tail).decode("utf-8", errors="ignore")
    return {"logs": logs}


def check_container_health(service: str) -> Dict[str, Any]:
    """Devuelve health status si existe."""
    cont = _get_container(service)
    if not cont:
        return {"error": "container not found"}
    attrs = cont.attrs or {}
    health = attrs.get("State", {}).get("Health")
    return {"health": health} if health else {"health": "unknown"}


