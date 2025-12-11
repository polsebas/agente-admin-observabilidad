# Admin Agent Service

Servicio multi-agente (Agno Framework) para asistir al administrador del sistema:

- Monitoreo proactivo (métricas, logs, traces)
- Troubleshooting reactivo
- Análisis de causa raíz (fase 2)
- Alertas por webhook
- API REST y gRPC

## Endpoints (puertos internos)
- gRPC: `5109`
- API REST: `8001`
- Métricas Prometheus: `5110`

## Variables de entorno
- `OPENAI_API_KEY` (requerida)
- `PROMETHEUS_URL` (default `http://prometheus:9090`)
- `LOKI_URL` (default `http://loki:3100`)
- `TEMPO_URL` (default `http://tempo:3200`)
- `POSTGRES_HOST` (default `postgres`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `WEBHOOK_URLS` (JSON array con URLs de webhook)

## Ejecución local
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7777
```

## Levantar Grafana MCP (docker)
```bash
# requiere exportar credencial de service account de Grafana
export GRAFANA_API_KEY=glsa_xxx
# si Grafana corre en el host en 3001:
export GRAFANA_URL=http://host.docker.internal:3001
# en Linux: host-gateway habilitado en docker-compose extra_hosts
# (ajusta al puerto donde tengas Grafana)

docker compose up -d grafana-mcp
# expondrá MCP en http://localhost:8000
```

## Levantar AgentOS + AgnoUI con docker-compose
```bash
export OPENAI_API_KEY=sk-xxx
export GRAFANA_API_KEY=glsa_xxx
# si Grafana corre en el host en 3001:
export GRAFANA_URL=http://host.docker.internal:3001

docker compose up -d agentos agnoui grafana-mcp
# AgentOS -> http://localhost:7777
# AgnoUI  -> http://localhost:3002 (hablándole a http://agentos:7777 en la red)
```

## Conectar AgentOS al Agno Control Plane (opcional)
- Guía oficial: https://docs.agno.com/agent-os/connecting-your-os
- Variables opcionales:
  - `AGNO_CP_URL` : endpoint del Control Plane
  - `AGNO_CP_API_KEY` : API key del Control Plane
- Endpoint local típico: `http://localhost:7777`

## AgnoUI apuntando al AgentOS local
- En docker-compose: `NEXT_PUBLIC_AGNO_URL=http://agentos:7777` (expuesto en host `http://localhost:3002`)
- En local (sin docker): setea `NEXT_PUBLIC_AGNO_URL=http://localhost:7777` y corre `npm run dev` dentro de `agent-ui`.

## Configurar Webhook en Grafana Alertmanager
1. En Grafana: Alerting → Contact points → Add contact point
2. Integration: Webhook
3. URL: `http://localhost:7777/api/alerts`
4. HTTP Method: POST
5. Probar conexión

## 📚 Documentación

### Context Engineering
El sistema utiliza técnicas avanzadas de context engineering para mejorar la calidad y consistencia de los análisis de alertas.

- **[Context Engineering Guide](docs/CONTEXT_ENGINEERING.md)** - Documentación completa sobre cómo funciona el context engineering y cómo modificarlo
- **[Quick Reference](docs/CONTEXT_QUICK_REFERENCE.md)** - Guía rápida para cambios comunes

### Arquitectura del Sistema
```
ObservabilityTeam (Líder)
├── WatchdogAgent (Clasificación y deduplicación)
├── TriageAgent (Correlación de métricas/logs/traces)
└── ReportAgent (Generación de reportes)
```

### Componentes Clave
- **WatchdogAgent**: Clasifica severidad (critical/major/minor/info), detecta duplicados, enriquece contexto
- **TriageAgent**: Correlaciona métricas de Prometheus, logs de Loki, traces de Tempo para identificar causa raíz
- **ReportAgent**: Genera reportes markdown con timeline, evidencia, análisis de causa raíz y próximos pasos
- **ObservabilityTeam**: Coordina el flujo secuencial entre los 3 agentes

### Quick Commands (Comandos Rápidos)
Consultas prediseñadas para observabilidad del sistema. Ver [docs/QUICK_COMMANDS.md](docs/QUICK_COMMANDS.md) para documentación completa.

```bash
# Incidencias recientes (últimas 24h)
curl http://localhost:7777/api/quick/recent-incidents?hours=24

# Health check de servicios
curl http://localhost:7777/api/quick/health

# Monitoreo post-deployment
curl "http://localhost:7777/api/quick/post-deployment?service=auth-service&deployment_time=2025-12-10T14:00:00Z"

# Análisis de tendencias
curl http://localhost:7777/api/quick/trends?metric=alert_count&period_hours=24

# Resumen diario
curl http://localhost:7777/api/quick/daily-digest

# Ver ayuda de comandos
curl http://localhost:7777/api/quick/help
```

### Testing
```bash
# Enviar alerta de prueba
curl -X POST http://localhost:7777/api/alerts \
  -H "Content-Type: application/json" \
  -d @test-alert.json

# Ver reporte generado
cat test-alert-report.md

# Probar quick commands
./test_quick_commands.sh
```


