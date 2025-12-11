import json
import os
from typing import List


class AdminAgentConfig:
    """Configuración centralizada del Admin Agent."""

    # LLM
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    agno_model: str = os.getenv("AGNO_MODEL", "gpt-5-mini")

    # Observability endpoints
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    loki_url: str = os.getenv("LOKI_URL", "http://loki:3100")
    tempo_url: str = os.getenv("TEMPO_URL", "http://tempo:3200")

    # Database
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "somed_admin")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db: str = os.getenv("POSTGRES_DB", "somed")
    agno_db_path: str = os.getenv("AGNO_DB_PATH", "./agno.db")

    # Docker
    docker_socket: str = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")

    # Alerting
    alert_cooldown_seconds: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))
    alert_dedup_window_minutes: int = int(os.getenv("ALERT_DEDUP_WINDOW", "60"))
    alert_storage_enabled: bool = os.getenv("ALERT_STORAGE", "true").lower() in ("1", "true", "yes")
    webhook_urls: List[str] = []
    _webhook_env = os.getenv("WEBHOOK_URLS", "[]")
    try:
        webhook_urls = json.loads(_webhook_env) if _webhook_env else []
    except json.JSONDecodeError:
        webhook_urls = []

    # Telemetría Agno
    agno_telemetry: bool = os.getenv("AGNO_TELEMETRY", "true").lower() in ("1", "true", "yes")

    # Control Plane Agno (opcional)
    control_plane_url: str = os.getenv("AGNO_CP_URL", "")
    control_plane_api_key: str = os.getenv("AGNO_CP_API_KEY", "")

    # Context dependencies para agents
    monitored_services: List[str] = [
        "auth-service",
        "api-gateway",
        "payment-service",
        "user-service",
        "notification-service",
    ]
    latency_threshold_ms: int = int(os.getenv("LATENCY_THRESHOLD_MS", "500"))
    error_rate_threshold: float = float(os.getenv("ERROR_RATE_THRESHOLD", "0.01"))

    # Quick Commands
    quick_commands_enabled: bool = os.getenv("QUICK_COMMANDS_ENABLED", "true").lower() in ("1", "true", "yes")
    quick_commands_default_ai_analysis: bool = os.getenv("QUICK_COMMANDS_AI_ANALYSIS", "false").lower() in ("1", "true", "yes")
    daily_digest_time: str = os.getenv("DAILY_DIGEST_TIME", "09:00")  # UTC


