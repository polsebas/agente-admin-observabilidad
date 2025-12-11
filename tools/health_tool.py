"""
Resumen de salud del sistema usando otras tools.
"""
from typing import Any, Dict

from tools import prometheus_tool, docker_tool
from agent.config import AdminAgentConfig

_config = AdminAgentConfig()


def check_all_services() -> Dict[str, Any]:
    """Estado up/down de servicios + resumen de errores/latencias."""
    health = prometheus_tool.get_service_health()
    return {"services": health}


def check_database_health() -> Dict[str, Any]:
    """Revisa si postgres está vivo via metric 'up' del exporter."""
    res = prometheus_tool.query_instant('up{job="postgres"}')
    return {"postgres_up": res}


def check_observability_stack() -> Dict[str, Any]:
    """Verifica Prometheus, Loki y Tempo exponiendo métricas básicas."""
    prom = prometheus_tool.query_instant('up{job="prometheus"}')
    tempo = prometheus_tool.query_instant('up{job="tempo"}')
    # Loki: no scrapeado por Prometheus; validar contenedor
    loki_health = docker_tool.check_container_health("loki") if hasattr(docker_tool, "check_container_health") else {}
    return {
        "prometheus": prom,
        "tempo": tempo,
        "loki": loki_health,
    }


def get_system_status() -> Dict[str, Any]:
    """Resumen global de estado del sistema."""
    services = check_all_services()
    db = check_database_health()
    obs = check_observability_stack()
    return {
        "services": services,
        "database": db,
        "observability": obs,
    }


