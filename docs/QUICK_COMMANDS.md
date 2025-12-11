# Quick Commands - Comandos Rápidos de Observabilidad

Comandos prediseñados para consultas comunes sobre el estado del sistema.

## 📚 Índice

1. [Introducción](#introducción)
2. [Comandos Disponibles](#comandos-disponibles)
3. [Modo Híbrido](#modo-híbrido)
4. [Uso vía API REST](#uso-vía-api-rest)
5. [Uso vía QueryAgent](#uso-vía-queryagent)
6. [Ejemplos Prácticos](#ejemplos-prácticos)
7. [Configuración](#configuración)

---

## Introducción

Los **Quick Commands** son consultas prediseñadas que permiten obtener información rápida sobre el estado del sistema sin necesidad de escribir queries complejas.

### Casos de Uso

- ✅ Ver incidencias recientes (últimas N horas)
- ✅ Check de salud de servicios (estado actual)
- ✅ Monitoreo post-deployment
- ✅ Análisis de tendencias comparativas
- ✅ Resúmenes diarios automáticos

---

## Comandos Disponibles

### 1. `get_recent_incidents` - Incidencias Recientes

Obtiene reporte de alertas recientes del sistema.

**Parámetros:**
- `hours` (int, default: 24): Ventana de tiempo en horas (1-168)
- `severity` (str, optional): Filtrar por severidad (critical, major, minor, info)
- `service` (str, optional): Filtrar por servicio específico
- `include_duplicates` (bool, default: false): Incluir alertas duplicadas
- `analyze_with_ai` (bool, default: false): Análisis enriquecido con IA

**Output:**
```markdown
# Incidencias Recientes (Últimas 24 horas)

## Resumen Ejecutivo
- Total de alertas: 15
- Critical: 2 | Major: 5 | Minor: 6 | Info: 2
- Servicios más afectados: auth-service (3), payment-service (2)

## Incidencias Críticas
### [2025-12-10 14:30 UTC] auth-service - HighErrorRate
- Severidad: Critical
- Estado: firing
- Resumen: Error rate above 5%
```

**Cuándo usar:**
- Al empezar el turno de on-call
- Después de una alerta crítica
- Para revisar actividad reciente del sistema

---

### 2. `get_service_health_summary` - Health Check

Estado actual de salud de servicios monitoreados.

**Parámetros:**
- `services` (list[str], optional): Lista de servicios a revisar (default: todos)
- `include_metrics` (bool, default: true): Incluir métricas actuales (error rate, latency)
- `analyze_with_ai` (bool, default: false): Análisis con TriageAgent

**Output:**
```markdown
# Service Health Summary

## Estado General: 🟢 HEALTHY
- Alertas activas: 0

### auth-service 🟢
- Status: HEALTHY
- Error rate: 0.05% (threshold: 1%)
- Latency P95: 250ms (threshold: 500ms)
- Alertas activas: 0

### payment-service 🟡
- Status: DEGRADED
- Error rate: 1.2% ⚠️ (threshold: 1%)
- Latency P95: 650ms ⚠️ (threshold: 500ms)
- Alertas activas: 1 (Major)
```

**Cuándo usar:**
- Check rápido del estado general
- Antes/después de deployments
- Durante incident response

---

### 3. `monitor_post_deployment` - Monitoreo Post-Deployment

Monitorea un servicio después de un deployment buscando anomalías.

**Parámetros:**
- `service` (str, required): Nombre del servicio deployado
- `deployment_time` (str, required): Timestamp del deployment (ISO 8601)
- `monitoring_window_hours` (int, default: 2): Ventana de monitoreo (1-24h)
- `analyze_with_ai` (bool, default: true): Análisis con TriageAgent

**Output:**
```markdown
# Post-Deployment Monitoring: auth-service

## Deployment Info
- Service: auth-service
- Deploy time: 2025-12-10 14:00:00 UTC
- Monitoring window: 2.0 hours

## Alertas Post-Deploy
⚠️ 1 alertas detectadas:
- 15 minutos post-deploy: HighLatency (major)
  - P95 latency increased from 200ms to 550ms

## Comparación Pre/Post Deploy
- Alertas pre-deploy (2h antes): 0
- Alertas post-deploy (2.0h después): 1
- Cambio: +1 alertas ⚠️

## Recomendación
🟡 MONITOREO CONTINUO - Alertas detectadas. Mantener observación.
```

**Cuándo usar:**
- Inmediatamente después de cada deployment
- Para validar que un deploy no introdujo problemas
- Como parte del proceso de release

---

### 4. `analyze_trends` - Análisis de Tendencias

Analiza tendencias de métricas comparando períodos.

**Parámetros:**
- `service` (str, optional): Servicio a analizar (default: todos)
- `metric` (str, default: "alert_count"): Métrica a analizar (alert_count, error_rate, latency)
- `period_hours` (int, default: 24): Período actual a analizar (1-168h)
- `compare_with_previous` (bool, default: true): Comparar con período anterior
- `analyze_with_ai` (bool, default: true): Análisis con ReportAgent

**Output:**
```markdown
# Trend Analysis: alert_count

## Comparación de Períodos
- Período actual (últimas 24h): 18 alertas
- Período anterior (24h previas): 12 alertas
- Cambio: +50.0% ⚠️ (cambio significativo)

### Desglose por Severidad
- Major: 8
- Critical: 4
- Minor: 4
- Info: 2
```

**Cuándo usar:**
- Para detectar degradación gradual del sistema
- Análisis de fin de semana/día
- Investigación de patrones

---

### 5. `generate_daily_digest` - Resumen Diario

Genera resumen diario de actividad del sistema.

**Parámetros:**
- `date` (str, optional): Fecha en formato YYYY-MM-DD (default: ayer)
- `include_all_services` (bool, default: true): Incluir todos los servicios
- `analyze_with_ai` (bool, default: true): Resumen ejecutivo con IA

**Output:**
```markdown
# Daily Digest: 2025-12-09

## Resumen Ejecutivo
Se registraron 2 incidentes críticos y 5 mayores en el día. auth-service tuvo el mayor número de alertas (8).

## Métricas del Día
- Total alertas: 18
- Critical: 2 | Major: 5 | Minor: 6 | Info: 5

## Incidentes Destacados
1. [09:15 UTC] auth-service - Database Connection Pool Exhausted
   - Database connection pool exhausted causing service degradation

## Servicios con Mayor Actividad
- auth-service: 8 alertas
- payment-service: 3 alertas

## Tendencias vs Día Anterior
- Alertas: +20%
```

**Cuándo usar:**
- Reporte automático diario (ej: cada mañana a las 9am)
- Revisión de actividad de días específicos
- Preparación de reportes para management

---

## Modo Híbrido

Los comandos soportan dos modos de operación:

### Query Directa (Rápido)
**`analyze_with_ai=False`**
- ✅ Respuesta inmediata (< 1 segundo)
- ✅ Consulta directa a base de datos
- ✅ Formato markdown estructurado
- ❌ Sin análisis contextual de IA

**Usar cuando:**
- Necesitas información rápida
- Check de estado básico
- Verificación de métricas actuales

### Con Análisis IA (Completo)
**`analyze_with_ai=True`**
- ✅ Análisis contextual profundo
- ✅ Insights y recomendaciones
- ✅ Correlación con historial
- ❌ Más lento (10-30 segundos)

**Usar cuando:**
- Investigación de incidentes
- Post-mortems
- Análisis de causa raíz

---

## Uso vía API REST

Los comandos están expuestos como endpoints REST en `/api/quick/*`.

### Incidencias Recientes

```bash
# Últimas 8 horas
GET /api/quick/recent-incidents?hours=8

# Solo críticas
GET /api/quick/recent-incidents?hours=24&severity=critical

# Servicio específico
GET /api/quick/recent-incidents?service=auth-service&hours=12

# Con análisis IA
GET /api/quick/recent-incidents?hours=24&analyze_with_ai=true
```

### Health Check

```bash
# Todos los servicios
GET /api/quick/health

# Servicios específicos
GET /api/quick/health?services=auth-service,payment-service

# Sin métricas detalladas
GET /api/quick/health?include_metrics=false
```

### Post-Deployment

```bash
# Monitoreo post-deploy (2h default)
GET /api/quick/post-deployment?service=auth-service&deployment_time=2025-12-10T14:00:00Z

# Ventana custom (4h)
GET /api/quick/post-deployment?service=payment-service&deployment_time=2025-12-10T16:30:00Z&monitoring_window_hours=4
```

### Análisis de Tendencias

```bash
# Tendencias de alertas (24h)
GET /api/quick/trends?metric=alert_count&period_hours=24

# Tendencias de servicio específico
GET /api/quick/trends?metric=alert_count&service=auth-service&period_hours=12
```

### Daily Digest

```bash
# Digest de ayer
GET /api/quick/daily-digest

# Digest de fecha específica
GET /api/quick/daily-digest?date=2025-12-09

# Solo servicios con incidencias
GET /api/quick/daily-digest?include_all_services=false
```

### Ayuda

```bash
# Ver todos los comandos disponibles
GET /api/quick/help
```

---

## Uso vía QueryAgent

Los comandos también se pueden invocar en lenguaje natural a través del QueryAgent.

### Ejemplos

```python
# Via AgnoUI o API de AgentOS
user: "Dame las novedades de las últimas 8 horas"
# QueryAgent invoca: get_recent_incidents(hours=8, analyze_with_ai=False)

user: "Cómo está el sistema ahora?"
# QueryAgent invoca: get_service_health_summary()

user: "Monitoreá el deploy de auth-service que hicimos a las 14:00"
# QueryAgent invoca: monitor_post_deployment(service="auth-service", deployment_time="14:00")

user: "Analizá las tendencias de la última semana"
# QueryAgent invoca: analyze_trends(period_hours=168)

user: "Resumen de ayer con análisis detallado"
# QueryAgent invoca: generate_daily_digest(analyze_with_ai=True)
```

---

## Ejemplos Prácticos

### Escenario 1: Inicio de Turno On-Call

```bash
# 1. Check general del sistema
curl http://localhost:7777/api/quick/health

# 2. Revisar incidencias de las últimas 8 horas
curl http://localhost:7777/api/quick/recent-incidents?hours=8

# 3. Si hay alertas, analizarlas con detalle
curl http://localhost:7777/api/quick/recent-incidents?hours=8&severity=critical&analyze_with_ai=true
```

### Escenario 2: Post-Deployment Validation

```bash
# 1. Deploy realizado a las 14:00 UTC
DEPLOY_TIME="2025-12-10T14:00:00Z"

# 2. Monitorear 2 horas post-deploy
curl "http://localhost:7777/api/quick/post-deployment?service=auth-service&deployment_time=$DEPLOY_TIME"

# 3. Si hay problemas, ver todas las alertas del servicio
curl "http://localhost:7777/api/quick/recent-incidents?service=auth-service&hours=3"
```

### Escenario 3: Investigación de Degradación

```bash
# 1. Analizar tendencias últimas 48h
curl "http://localhost:7777/api/quick/trends?metric=alert_count&period_hours=48&compare_with_previous=true"

# 2. Ver salud actual de todos los servicios
curl "http://localhost:7777/api/quick/health"

# 3. Analizar incidencias con IA
curl "http://localhost:7777/api/quick/recent-incidents?hours=48&analyze_with_ai=true"
```

### Escenario 4: Reporte Diario

```bash
# Generar digest de ayer (automático a las 9am UTC)
curl "http://localhost:7777/api/quick/daily-digest"

# Digest de una semana atrás
curl "http://localhost:7777/api/quick/daily-digest?date=2025-12-03"
```

---

## Configuración

### Variables de Entorno

En tu archivo `.env`:

```bash
# Habilitar quick commands (default: true)
QUICK_COMMANDS_ENABLED=true

# Análisis IA por default (default: false - más rápido)
QUICK_COMMANDS_AI_ANALYSIS=false

# Hora para daily digest automático (UTC)
DAILY_DIGEST_TIME=09:00
```

### Configuración de Thresholds

Los comandos usan los thresholds configurados en `agent/config.py`:

```python
# agent/config.py
monitored_services = [
    "auth-service",
    "api-gateway",
    "payment-service",
    # Añadir más servicios aquí
]

latency_threshold_ms = 500  # P95 threshold
error_rate_threshold = 0.01  # 1% threshold
```

---

## Tips y Best Practices

### ✅ Do's

1. **Usa quick commands para checks rápidos**
   - `recent-incidents` al iniciar turno
   - `health` antes de deployments
   - `post-deployment` después de cada release

2. **Optimiza con parámetros**
   - Usa `hours` pequeños para queries rápidas
   - Filtra por `service` o `severity` para enfocarte

3. **Análisis IA cuando sea necesario**
   - Investigaciones profundas: `analyze_with_ai=true`
   - Checks rápidos: `analyze_with_ai=false`

4. **Automatiza reportes**
   - Daily digest cada mañana
   - Health check cada hora
   - Post-deployment después de CI/CD

### ❌ Don'ts

1. **No uses `hours` muy grandes sin filtros**
   - ❌ `hours=720` (30 días) sin filtros
   - ✅ `hours=720&service=auth-service`

2. **No uses `analyze_with_ai=true` para todo**
   - Más lento y costoso
   - Reservar para análisis detallados

3. **No ignores los thresholds**
   - Si health check muestra ⚠️, investigar
   - Los íconos indican exceso de thresholds

---

## Integración con Otras Herramientas

### Slack Notifications

```bash
# Script para enviar health check a Slack cada hora
#!/bin/bash
REPORT=$(curl -s http://localhost:7777/api/quick/health)
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"$REPORT\"}"
```

### Grafana Dashboard

Crear panel con query a quick commands API:
- Health status como gauge
- Alert trends como time series
- Daily digest como table

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Monitor Post-Deployment
  run: |
    curl "http://observability:7777/api/quick/post-deployment?service=$SERVICE&deployment_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      | tee deploy-report.md
```

---

## Troubleshooting

### Problema: "No se encontraron alertas"

**Solución:**
- Verificar que `alert_storage.init_db()` se ejecutó
- Verificar que hay alertas en la ventana de tiempo
- Probar con `hours` más grande

### Problema: "Error obteniendo métricas"

**Solución:**
- Verificar que Prometheus está accesible
- Verificar `PROMETHEUS_URL` en config
- Ver logs del servidor para detalles

### Problema: Respuesta lenta

**Solución:**
- Usar `analyze_with_ai=false` para queries rápidas
- Reducir `hours` o añadir filtros
- Verificar que DB no está sobrecargada

---

## Próximos Pasos

### Mejoras Futuras

- [ ] Análisis IA completo (integración con ReportAgent/TriageAgent)
- [ ] Métricas de Prometheus en `analyze_trends`
- [ ] Comparación pre/post deploy con métricas reales
- [ ] Alertas proactivas (ej: si trends muestran degradación)
- [ ] Exportar reportes a PDF/HTML
- [ ] Integración con sistemas de ticketing (Jira, PagerDuty)

---

## Referencias

- [Documentación de Context Engineering](CONTEXT_ENGINEERING.md)
- [Quick Reference](CONTEXT_QUICK_REFERENCE.md)
- [API de Alertas](../api/alerts_api.py)
- [AgentOS Docs](https://docs.agno.com/agent-os/introduction)

---

**Última actualización**: 2025-12-10  
**Versión**: 1.0

