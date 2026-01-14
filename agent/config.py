import json
import os
import yaml
from typing import List, Any

def load_yaml_config(path: str = "config.yaml") -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading config.yaml: {e}")
            return {}
    return {}

_yaml_config = load_yaml_config()

def _get_conf(section: str, key: str, default: Any = None) -> Any:
    """Helper to get config with priority: ENV > YAML > Default"""
    # Try Env
    env_key = f"{section.upper()}_{key.upper()}" if section else key.upper()
    env_val = os.getenv(env_key)
    if env_val is not None:
        return env_val
    
    # Try YAML
    if section and section in _yaml_config:
        val = _yaml_config[section].get(key)
        if val is not None:
            return val
    elif not section and key in _yaml_config:
        val = _yaml_config.get(key)
        if val is not None:
            return val
            
    return default

class AdminAgentConfig:
    """Configuración centralizada del Admin Agent (YAML + Env vars)."""

    # LLM
    openai_model: str = str(_get_conf("llm", "openai_model", "gpt-5-mini"))
    agno_model: str = str(_get_conf("llm", "agno_model", "gpt-5-mini"))

    # Observability endpoints
    prometheus_url: str = str(_get_conf("observability", "prometheus_url", "http://prometheus:9090"))
    loki_url: str = str(_get_conf("observability", "loki_url", "http://loki:3100"))
    tempo_url: str = str(_get_conf("observability", "tempo_url", "http://tempo:3200"))

    # Database
    postgres_host: str = str(_get_conf("database", "postgres_host", "postgres"))
    postgres_port: int = int(_get_conf("database", "postgres_port", 5432))
    postgres_user: str = str(_get_conf("database", "postgres_user", "somed_admin"))
    postgres_password: str = str(_get_conf("database", "postgres_password", os.getenv("POSTGRES_PASSWORD", "")))
    postgres_db: str = str(_get_conf("database", "postgres_db", "somed"))
    agno_db_path: str = str(_get_conf("database", "agno_db_path", "./agno.db"))
    redis_url: str = str(_get_conf("database", "redis_url", os.getenv("REDIS_URL", "redis://redis:6379/0")))

    # Docker
    docker_socket: str = str(_get_conf("docker", "socket", "/var/run/docker.sock"))

    # Alerting
    alert_cooldown_seconds: int = int(_get_conf("alerting", "cooldown_seconds", 300))
    alert_dedup_window_minutes: int = int(_get_conf("alerting", "dedup_window_minutes", 60))
    alert_storage_enabled: bool = bool(_get_conf("alerting", "storage_enabled", True))
    
    # Webhooks
    webhook_urls: List[str] = _get_conf("alerting", "webhook_urls", [])

    # Telemetry
    agno_telemetry: bool = bool(_get_conf("telemetry", "agno_enabled", True))

    # Control Plane Agno (opcional)
    control_plane_url: str = os.getenv("AGNO_CP_URL", "")
    control_plane_api_key: str = os.getenv("AGNO_CP_API_KEY", "")

    # Context dependencies para agents
    # monitored_services removed - using dynamic discovery in tools
    latency_threshold_ms: int = int(_get_conf("thresholds", "latency_ms", 500))
    error_rate_threshold: float = float(_get_conf("thresholds", "error_rate", 0.01))

    # Quick Commands
    quick_commands_enabled: bool = bool(_get_conf("quick_commands", "enabled", True))
    quick_commands_default_ai_analysis: bool = bool(_get_conf("quick_commands", "ai_analysis", False))
    daily_digest_time: str = str(_get_conf("quick_commands", "daily_digest_time", "09:00"))
