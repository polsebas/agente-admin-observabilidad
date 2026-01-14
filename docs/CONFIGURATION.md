# Guía de Configuración

El sistema Agente Admin Observabilidad utiliza un sistema de configuración jerárquico que permite flexibilidad para desarrollo local y despliegues productivos.

La prioridad de configuración es:
1. **Variables de Entorno** (Formato `SECCION_CLAVE`)
2. **Archivo `config.yaml`**
3. **Valores por defecto** (definidos en código)

---

## Archivo `config.yaml`

El archivo `config.yaml` es la fuente de verdad central. Se recomienda montarlo como volumen en el contenedor Docker.

```yaml
# LLM Settings
llm:
  openai_model: "gpt-5-mini" # Modelo principal
  agno_model: "gpt-5-mini"   # Modelo para Agno framework

# Observability Endpoints
observability:
  prometheus_url: "http://prometheus:9090"
  loki_url: "http://loki:3100"
  tempo_url: "http://tempo:3200"

# Database Settings
database:
  postgres_host: "postgres"
  postgres_port: 5432
  postgres_user: "somed_admin"
  postgres_db: "somed"
  # postgres_password: "" # Recomendado usar env var
  redis_url: "redis://redis:6379/0"

# Alerting
alerting:
  cooldown_seconds: 300       # Tiempo de espera entre alertas similares
  dedup_window_minutes: 60    # Ventana de deduplicación
  storage_enabled: true       # Guardar historial en DB

# Monitoring Thresholds
thresholds:
  latency_ms: 500
  error_rate: 0.01
```

---

## Variables de Entorno

Puedes sobrescribir cualquier valor del YAML usando variables de entorno. El formato general es `SECCION_CLAVE` (en mayúsculas).

### Comunes

| YAML Path | Variable de Entorno | Descripción |
|-----------|---------------------|-------------|
| `llm.openai_model` | `LLM_OPENAI_MODEL` | Modelo OpenAI a utilizar |
| `observability.prometheus_url` | `OBSERVABILITY_PROMETHEUS_URL` | URL de Prometheus |
| `database.postgres_host` | `DATABASE_POSTGRES_HOST` | Host de PostgreSQL |

### Credenciales (Recomendado usar Env Vars)

| Variable | Descripción |
|----------|-------------|
| `OPENAI_API_KEY` | **Requerido**. API Key de OpenAI. |
| `GRAFANA_API_KEY` | Token de Service Account para consultar Grafana. |
| `DATABASE_POSTGRES_PASSWORD` | Contraseña de PostgreSQL (o `POSTGRES_PASSWORD` como fallback). |
| `DATABASE_REDIS_URL` | URL de conexión redis (o `REDIS_URL` como fallback). |

### Docker Compose

En el archivo `docker-compose.yml`, se inyectan estas variables automáticamente desde el archivo `.env`.

Ejemplo `.env`:
```bash
OPENAI_API_KEY=sk-...
POSTGRES_PASSWORD=secret
```
