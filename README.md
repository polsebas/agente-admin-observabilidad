# 🤖 Sistema Agno para Observabilidad

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Agno Framework](https://img.shields.io/badge/Agno-2.2.12+-green.svg)](https://www.agno.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/github/stars/polsebas/agente-admin-observabilidad?style=social)](https://github.com/polsebas/agente-admin-observabilidad)

Sistema de análisis automático de alertas usando **Agno Framework** + **Grafana Stack**. Recibe alertas de Grafana, correlaciona métricas/logs/traces y genera reportes de análisis automáticos con causa raíz e insights accionables.

---

## 🌟 Características

- ✅ **ObservabilityTeam**: Equipo multi-agente para análisis de alertas
  - **WatchdogAgent**: Clasificación de severidad, deduplicación y enriquecimiento de contexto
  - **TriageAgent**: Correlación de métricas (Prometheus), logs (Loki) y traces (Tempo)
  - **ReportAgent**: Generación de reportes markdown con timeline, evidencia y próximos pasos
- ✅ **Quick Commands**: 5 comandos rápidos de observabilidad
  - `recent-incidents`: Incidencias recientes con filtros
  - `health`: Health check de servicios en tiempo real
  - `post-deployment`: Monitoreo post-deployment automático
  - `trends`: Análisis de tendencias comparativas
  - `daily-digest`: Resumen diario automático
- ✅ **QueryAgent**: Interpreta lenguaje natural para ejecutar quick commands
- ✅ **Context Engineering**: Configuración avanzada para reportes de alta calidad
- ✅ **API REST Completa**: Endpoints para webhooks, quick commands y reportes
- ✅ **AgentOS + AgnoUI**: Runtime oficial de Agno con interfaz web moderna
- ✅ **Grafana Stack**: Integración con Prometheus, Loki, Tempo y Grafana MCP

---

## 📚 Quick Start

### 1. Clonar el repositorio

```bash
git clone https://github.com/polsebas/agente-admin-observabilidad.git
cd agente-admin-observabilidad
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus claves
```

Obtener `OPENAI_API_KEY`: https://platform.openai.com/api-keys  
Obtener `GRAFANA_API_KEY`: Ver [sección de Grafana Service Account](#grafana-service-account-token)

### 3. Levantar el stack

#### Opción A: Con Docker Compose (Recomendado)

```bash
export OPENAI_API_KEY=sk-xxx
export GRAFANA_API_KEY=glsa_xxx
export GRAFANA_URL=http://host.docker.internal:3001

docker compose up -d
```

- **AgentOS**: http://localhost:7777
- **AgnoUI**: http://localhost:3002

#### Opción B: Local (Development)

```bash
# Instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar servidor
uvicorn main:app --host 0.0.0.0 --port 7777
```

---

## 🔧 Configuración de Grafana

### Grafana Service Account Token

1. Ir a Grafana → **Administration** → **Service Accounts**
2. **Add service account**:
   - Name: `mcp-grafana`
   - Role: **Admin** (o **Editor** mínimo)
3. **Add service account token**:
   - Name: `agno-token`
   - Copiar el token generado (`glsa_...`)
4. Exportar: `export GRAFANA_API_KEY=glsa_xxx`

### Webhook de Alertmanager

1. En Grafana → **Alerting** → **Contact points**
2. **Add contact point**:
   - Name: `agno-webhook`
   - Integration: **Webhook**
   - URL: `http://localhost:7777/api/alerts`
   - HTTP Method: **POST**
3. Probar conexión

---

## 📖 Uso

### Quick Commands (API REST)

```bash
# Health check de servicios
curl http://localhost:7777/api/quick/health

# Incidencias recientes (últimas 24h)
curl http://localhost:7777/api/quick/recent-incidents?hours=24

# Filtrar por severidad y servicio
curl "http://localhost:7777/api/quick/recent-incidents?hours=8&severity=critical&service=auth-service"

# Monitoreo post-deployment
curl "http://localhost:7777/api/quick/post-deployment?service=auth-service&deployment_time=2025-12-10T14:00:00Z"

# Análisis de tendencias
curl "http://localhost:7777/api/quick/trends?metric=alert_count&period_hours=48"

# Resumen diario
curl http://localhost:7777/api/quick/daily-digest

# Ver ayuda completa
curl http://localhost:7777/api/quick/help
```

### Webhook de Grafana

```bash
# Enviar alerta de prueba
curl -X POST http://localhost:7777/api/alerts \
  -H "Content-Type: application/json" \
  -d @test-alert.json
```

### QueryAgent (Lenguaje Natural)

Usa AgnoUI en http://localhost:3002 o la API directamente:

```python
# Ejemplos de queries en lenguaje natural
"Dame las novedades de las últimas 8 horas"
"Cómo está el sistema ahora?"
"Monitoreá el deploy de auth-service de las 14:00"
"Analizá las tendencias de la última semana"
```

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────┐
│         Grafana Alertmanager            │
│         (Webhook POST)                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         AgentOS (FastAPI)               │
│  Endpoint: /api/alerts                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       ObservabilityTeam                 │
│  ┌────────────────────────────────────┐ │
│  │  WatchdogAgent                     │ │
│  │  → Classify, Dedupe, Enrich        │ │
│  └─────────────┬──────────────────────┘ │
│                ▼                         │
│  ┌────────────────────────────────────┐ │
│  │  TriageAgent                       │ │
│  │  → Correlate Metrics/Logs/Traces  │ │
│  └─────────────┬──────────────────────┘ │
│                ▼                         │
│  ┌────────────────────────────────────┐ │
│  │  ReportAgent                       │ │
│  │  → Generate Markdown Report        │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Storage: SQLite (alert_storage)        │
│  + Markdown Reports                     │
└─────────────────────────────────────────┘
```

### Componentes Clave

- **WatchdogAgent**: Clasifica severidad (critical/major/minor/info), detecta duplicados, enriquece contexto
- **TriageAgent**: Correlaciona métricas de Prometheus, logs de Loki, traces de Tempo para identificar causa raíz
- **ReportAgent**: Genera reportes markdown con timeline, evidencia, análisis de causa raíz y próximos pasos
- **ObservabilityTeam**: Coordina el flujo secuencial entre los 3 agentes
- **QueryAgent**: Ejecuta quick commands desde lenguaje natural

---

## 📚 Documentación

### Context Engineering
- **[Guía de Context Engineering](docs/CONTEXT_ENGINEERING.md)**: Documentación completa sobre cómo se usa el context engineering en este proyecto, incluyendo arquitectura, parámetros por agente, best practices y ejemplos.
- **[Referencia Rápida de Contexto](docs/CONTEXT_QUICK_REFERENCE.md)**: Una guía concisa para consultas rápidas sobre los parámetros de contexto y su uso.
- **[Resumen de Implementación](docs/IMPLEMENTATION_SUMMARY.md)**: Un resumen ejecutivo de los cambios implementados, resultados y mejoras observables.

### Quick Commands
- **[Guía de Quick Commands](docs/QUICK_COMMANDS.md)**: Documentación completa de comandos rápidos de observabilidad, incluyendo 5 comandos principales, modo híbrido, ejemplos prácticos y casos de uso.
- **[Resumen de Implementación](QUICK_COMMANDS_IMPLEMENTATION.md)**: Resumen técnico de la implementación, arquitectura, testing y próximos pasos.

### General
- **[Índice de Documentación](docs/README.md)**: Punto de entrada a toda la documentación del proyecto.

---

## 🧪 Testing

```bash
# Probar quick commands
./test_quick_commands.sh

# Enviar alerta de prueba
curl -X POST http://localhost:7777/api/alerts \
  -H "Content-Type: application/json" \
  -d @test-alert.json

# Ver reporte generado
cat test-alert-report.md
```

---

## 🚀 Roadmap (Fase 2)

- [ ] **Análisis IA completo**: Integración real de `analyze_with_ai=True` con agentes
- [ ] **Métricas reales**: Comparación de métricas de Prometheus en tendencias
- [ ] **Automatización**: Daily digest automático con cron/scheduled tasks
- [ ] **Acciones automáticas**: Restart, scale, runbooks ejecutables
- [ ] **Exportación**: Reportes en PDF/HTML, integración con Jira/PagerDuty
- [ ] **Performance**: Cache de queries, paginación, índices optimizados
- [ ] **Dashboard**: Panel de Grafana con quick commands embebidos

---

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

Ver [docs/CONTEXT_ENGINEERING.md](docs/CONTEXT_ENGINEERING.md) para guías de desarrollo.

---

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

- [Agno Framework](https://www.agno.com/) - Multi-agent framework
- [Grafana](https://grafana.com/) - Observability stack
- [OpenAI](https://openai.com/) - LLM provider

---

## 📞 Contacto

**Pol Sebastian** - [@polsebas](https://github.com/polsebas)

**Project Link**: [https://github.com/polsebas/agente-admin-observabilidad](https://github.com/polsebas/agente-admin-observabilidad)

---

⭐ Si te gusta este proyecto, dale una estrella en GitHub!
