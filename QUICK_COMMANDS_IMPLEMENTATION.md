# Implementación de Quick Commands - Resumen

![Slash Commands Demo](docs/slash-commands-demo.png)
*Ejemplo real de slash command `/novedades hoy` con verificación automática y recomendaciones inteligentes*

**Fecha**: 2025-12-14  
**Versión**: 1.1  
**Estado**: ✅ COMPLETADO + SLASH COMMANDS

---

## 🎯 Objetivo

Implementar comandos rápidos (quick commands) como Agno tools que permiten consultas prediseñadas para casos de uso comunes en observabilidad, **ahora con soporte de Slash Commands para ejecución directa desde el chat**.

---

## ✅ Tareas Completadas

### 1. **Query Helpers** (Storage Layer)
📄 **Archivo**: `agent/storage/query_helpers.py`

**Funciones implementadas**:
- ✅ `get_alerts_in_timerange()` - Query optimizado para alertas en rango de tiempo
- ✅ `get_active_alerts()` - Obtiene alertas actualmente en estado 'firing'
- ✅ `get_current_service_metrics()` - Métricas actuales desde Prometheus
- ✅ `compare_metric_periods()` - Comparación entre dos períodos
- ✅ `get_alerts_summary_by_severity()` - Conteo por severidad
- ✅ `get_alerts_summary_by_service()` - Conteo por servicio

**Características**:
- Queries SQL optimizados con filtros
- Manejo de JSON en columnas (labels, annotations)
- Integración con Prometheus via `prometheus_tool`
- Manejo graceful de errores

---

### 2. **Quick Commands Tools** (Agno Tools)
📄 **Archivo**: `agent/tools/quick_commands.py`

**Comandos implementados**:

#### A. `get_recent_incidents`
- **Propósito**: Obtiene reporte de alertas recientes
- **Parámetros**: `hours`, `severity`, `service`, `include_duplicates`, `analyze_with_ai`
- **Output**: Markdown con resumen ejecutivo, agrupación por severidad
- **Casos de uso**: Inicio de turno on-call, revisión post-incidente

#### B. `get_service_health_summary`
- **Propósito**: Estado actual de salud de servicios
- **Parámetros**: `services`, `include_metrics`, `analyze_with_ai`
- **Output**: Markdown con íconos de estado (🟢🟡🔴), métricas actuales
- **Casos de uso**: Health check pre/post deployment, monitoreo continuo

#### C. `monitor_post_deployment`
- **Propósito**: Monitoreo post-deployment buscando anomalías
- **Parámetros**: `service`, `deployment_time`, `monitoring_window_hours`, `analyze_with_ai`
- **Output**: Markdown con comparación pre/post, recomendación (exitoso/rollback/monitoreo)
- **Casos de uso**: Validación post-release, detección temprana de problemas

#### D. `analyze_trends`
- **Propósito**: Análisis de tendencias comparando períodos
- **Parámetros**: `service`, `metric`, `period_hours`, `compare_with_previous`, `analyze_with_ai`
- **Output**: Markdown con comparación de períodos, desglose por severidad
- **Casos de uso**: Detección de degradación, análisis de fin de semana

#### E. `generate_daily_digest`
- **Propósito**: Resumen diario de actividad del sistema
- **Parámetros**: `date`, `include_all_services`, `analyze_with_ai`
- **Output**: Markdown con resumen ejecutivo, métricas del día, incidentes destacados
- **Casos de uso**: Reporte diario automatizado, revisión histórica

**Modo Híbrido**:
- ✅ Query directa (`analyze_with_ai=False`) - Respuesta inmediata (< 1s)
- ✅ Con análisis IA (`analyze_with_ai=True`) - Placeholder para futura integración

---

### 3. **QueryAgent** (Agno Agent)
📄 **Archivo**: `agent/agents/query_agent.py`

**Características**:
- ✅ Agente especializado en comandos rápidos
- ✅ Interpreta lenguaje natural ("últimas 8 horas", "estado del sistema")
- ✅ Instrucciones claras sobre cuándo usar cada comando
- ✅ Manejo de parámetros por default
- ✅ Output directo en markdown
- ✅ Debug mode habilitado

**Ejemplos de uso**:
```python
user: "Dame las novedades de las últimas 8 horas"
# → get_recent_incidents(hours=8)

user: "Cómo está el sistema ahora?"
# → get_service_health_summary()
```

---

### 4. **Quick Commands API** (REST Endpoints)
📄 **Archivo**: `api/quick_commands_api.py`

**Endpoints implementados**:
- ✅ `GET /api/quick/recent-incidents`
- ✅ `GET /api/quick/health`
- ✅ `GET /api/quick/post-deployment`
- ✅ `GET /api/quick/trends`
- ✅ `GET /api/quick/daily-digest`
- ✅ `GET /api/quick/help` (documentación inline)

**Características**:
- Query parameters con validación (FastAPI Query)
- Descripciones detalladas para cada endpoint
- Ejemplos de uso en docstrings
- Manejo de errores con HTTPException
- Response: `{"report": "markdown..."}`

---

### 5. **Configuración**
📄 **Archivo**: `agent/config.py`

**Variables añadidas**:
```python
quick_commands_enabled: bool = True
quick_commands_default_ai_analysis: bool = False
daily_digest_time: str = "09:00"  # UTC
```

**Variables de entorno** (`.env`):
```bash
QUICK_COMMANDS_ENABLED=true
QUICK_COMMANDS_AI_ANALYSIS=false
DAILY_DIGEST_TIME=09:00
```

---

### 6. **Integración con AgentOS**
📄 **Archivo**: `main.py`

**Cambios**:
- ✅ Importar `query_agent` y `quick_commands_router`
- ✅ Añadir `query_agent` a la lista de agents de AgentOS
- ✅ Registrar `quick_commands_router` con prefix `/api`

**Resultado**:
- QueryAgent disponible en AgnoUI
- Endpoints REST accesibles en `http://localhost:7777/api/quick/*`

---

### 7. **Documentación**
📄 **Archivos**:
- ✅ `docs/QUICK_COMMANDS.md` (guía completa, 450+ líneas)
- ✅ `docs/README.md` (actualizado con referencia)
- ✅ `README.md` (sección de Quick Commands añadida)
- ✅ `QUICK_COMMANDS_IMPLEMENTATION.md` (este archivo)

**Contenido de la guía**:
- Introducción y casos de uso
- Descripción detallada de cada comando
- Modo híbrido (query directa vs IA)
- Uso vía API REST y QueryAgent
- Ejemplos prácticos por escenario
- Configuración y troubleshooting
- Integración con otras herramientas
- Best practices (Do's y Don'ts)

---

### 8. **Testing**
📄 **Archivo**: `test_quick_commands.sh`

**Tests implementados**:
- ✅ Recent incidents (24h, 8h + critical)
- ✅ Health summary (todos, específicos)
- ✅ Post-deployment monitoring
- ✅ Analyze trends (24h, servicio específico)
- ✅ Daily digest (ayer, fecha específica)
- ✅ Help endpoint

**Ejecución**:
```bash
chmod +x test_quick_commands.sh
./test_quick_commands.sh
```

---

## 📊 Resultados de Testing

### Pruebas Realizadas

**1. Help Endpoint** ✅
```bash
GET /api/quick/help
# Response: JSON con 5 comandos documentados
```

**2. Recent Incidents** ✅
```bash
GET /api/quick/recent-incidents?hours=72
# Output: 1 alerta critical de auth-service
# Formato: Markdown con resumen ejecutivo
```

**3. Service Health** ✅
```bash
GET /api/quick/health?services=auth-service
# Output: Estado CRITICAL (1 alerta activa)
# Formato: Íconos 🔴, métricas con error (Prometheus down)
```

**4. Trends Analysis** ✅
```bash
GET /api/quick/trends?metric=alert_count&period_hours=72&service=auth-service
# Output: +1 alerta vs período anterior
# Formato: Comparación de períodos, desglose por severidad
```

**5. Daily Digest** ✅
```bash
GET /api/quick/daily-digest
# Output: Sin incidencias en el día de ayer
```

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────┐
│         AgentOS (main.py)               │
│  - watchdog_agent, triage_agent         │
│  - report_agent, query_agent            │
│  - observability_team                   │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌───────────────┐  ┌──────────────────────┐
│  QueryAgent   │  │  Quick Commands API  │
│  (NL → Tool)  │  │  (REST Endpoints)    │
└───────┬───────┘  └──────────┬───────────┘
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Quick Commands      │
        │  (5 Agno Tools)      │
        │  - recent_incidents  │
        │  - health_summary    │
        │  - post_deployment   │
        │  - trends            │
        │  - daily_digest      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Query Helpers       │
        │  (Storage Layer)     │
        │  - get_alerts        │
        │  - get_metrics       │
        │  - compare_periods   │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌────────────┐        ┌──────────────┐
│ SQLite DB  │        │ Prometheus   │
│ (Alerts)   │        │ (Metrics)    │
└────────────┘        └──────────────┘
```

---

## 📈 Mejoras Observables

### Antes
- ❌ No había comandos prediseñados
- ❌ Queries manuales a base de datos
- ❌ Sin integración con lenguaje natural
- ❌ Sin reportes de tendencias/health

### Después
- ✅ 5 comandos rápidos disponibles
- ✅ API REST completa con documentación
- ✅ QueryAgent interpreta lenguaje natural
- ✅ Reportes automáticos en markdown
- ✅ Modo híbrido (rápido vs análisis IA)
- ✅ Integración con AgnoUI
- ✅ Testing automatizado

---

## 🚀 Casos de Uso Implementados

### Escenario 1: Inicio de Turno On-Call
```bash
# 1. Check general
curl http://localhost:7777/api/quick/health

# 2. Revisar últimas 8h
curl http://localhost:7777/api/quick/recent-incidents?hours=8

# 3. Si hay críticas, análisis detallado (futuro)
curl http://localhost:7777/api/quick/recent-incidents?hours=8&severity=critical&analyze_with_ai=true
```

### Escenario 2: Post-Deployment
```bash
DEPLOY_TIME="2025-12-11T14:00:00Z"
curl "http://localhost:7777/api/quick/post-deployment?service=auth-service&deployment_time=$DEPLOY_TIME"
```

### Escenario 3: Investigación de Degradación
```bash
# 1. Tendencias 48h
curl "http://localhost:7777/api/quick/trends?metric=alert_count&period_hours=48"

# 2. Health actual
curl "http://localhost:7777/api/quick/health"

# 3. Incidencias con IA (futuro)
curl "http://localhost:7777/api/quick/recent-incidents?hours=48&analyze_with_ai=true"
```

---

## 📁 Archivos Creados/Modificados

### Archivos Nuevos (7)
1. `agent/storage/query_helpers.py` (260 líneas)
2. `agent/tools/quick_commands.py` (550 líneas)
3. `agent/agents/query_agent.py` (55 líneas)
4. `api/quick_commands_api.py` (220 líneas)
5. `docs/QUICK_COMMANDS.md` (450 líneas)
6. `test_quick_commands.sh` (100 líneas)
7. `QUICK_COMMANDS_IMPLEMENTATION.md` (este archivo)

### Archivos Modificados (4)
1. `agent/config.py` (+5 líneas)
2. `main.py` (+3 líneas)
3. `README.md` (+20 líneas)
4. `docs/README.md` (+10 líneas)

**Total**: ~1,700 líneas de código nuevo  
**Total con documentación**: ~2,150 líneas

---

## 🔮 Próximos Pasos (Fase 2)

### Análisis IA Completo
- [ ] Integración real con ReportAgent para `analyze_with_ai=True`
- [ ] Integración con TriageAgent para análisis de tendencias
- [ ] Insights automáticos y recomendaciones contextuales

### Métricas Reales de Prometheus
- [ ] Implementar `compare_metric_periods` con queries PromQL
- [ ] Análisis de error_rate y latency en `analyze_trends`
- [ ] Comparación pre/post deploy con métricas reales

### Automatización
- [ ] Daily digest automático (cron job / scheduled task)
- [ ] Alertas proactivas basadas en tendencias
- [ ] Integración con Slack/Teams para notificaciones

### Exportación
- [ ] Exportar reportes a PDF/HTML
- [ ] Integración con Jira/PagerDuty
- [ ] Dashboard en Grafana con quick commands

### Performance
- [ ] Cache de queries frecuentes
- [ ] Paginación para grandes volúmenes
- [ ] Índices optimizados en SQLite

---

## ✅ Checklist de Validación

- [x] **Código**
  - [x] 5 comandos implementados y funcionando
  - [x] QueryAgent creado e integrado
  - [x] API REST con 6 endpoints
  - [x] Query helpers optimizados
  - [x] Manejo de errores graceful
  - [x] Sin linter errors

- [x] **Integración**
  - [x] QueryAgent en AgentOS
  - [x] Router registrado en main.py
  - [x] Configuración en config.py
  - [x] Variables de entorno documentadas

- [x] **Testing**
  - [x] Script de testing creado
  - [x] Tests manuales exitosos
  - [x] Verificación con datos reales
  - [x] Manejo de casos edge (sin datos, Prometheus down)

- [x] **Documentación**
  - [x] Guía completa (QUICK_COMMANDS.md)
  - [x] Ejemplos prácticos por escenario
  - [x] API endpoints documentados
  - [x] README actualizado
  - [x] Resumen de implementación

---

## 🆕 Slash Commands (v1.1 - 2025-12-14)

### Nuevas Características

#### 1. **Sistema de Slash Commands** ⚡
📄 **Archivos**: 
- `agent/slash_commands.py` - Parser, aliases y workflow de verificación
- `agent-ui/src/hooks/useAIStreamHandler.tsx` - Interceptor frontend
- `agent-ui/src/lib/slashCommands.ts` - Tipos e interfaces TypeScript

**Funcionalidades**:
- ✅ Ejecutar Quick Commands con sintaxis `/comando` desde el chat
- ✅ Aliases intuitivos: `/novedades`, `/salud`, `/deploy`, `/tendencias`, `/digest`
- ✅ Parsing de parámetros: `key=value` y shortcuts (`hoy`, `ayer`, `8h`)
- ✅ Modo híbrido: REST directo o fallback a QueryAgent

#### 2. **Prompts Canónicos Optimizados** 🎯
**Estructura por comando**:
```python
CANONICAL_PROMPTS = {
    "recent-incidents": {
        "system_role": "Analista de incidencias y observabilidad",
        "task": "Analizar incidencias y determinar si son accionables...",
        "evidence_checks": ["health", "trends"],
        "output_format": "markdown con secciones estructuradas"
    }
}
```

**Ventajas**:
- Prompts específicos para cada intención
- Criterios explícitos para NOTIFY vs FYI
- Formato de salida estable para UI

#### 3. **Workflow de Verificación con Evidencia** 📋
**Función**: `run_verification_workflow(intent, args, base_report)`

**Proceso**:
1. Ejecuta comando base (ej: `recent-incidents`)
2. Ejecuta checks adicionales según `evidence_checks`:
   - Para `recent-incidents`: `health` + `trends`
   - Para `health`: `recent-incidents` (últimas 24h)
   - Para `post-deployment`: `trends` + `recent-incidents`
3. Compila evidencia con `{source, query, result_summary, pass, timestamp}`
4. Determina recomendación con `{level, reason, confidence}`

**Ejemplo de evidencia**:
```json
{
  "source": "health_check",
  "query": "get_active_alerts()",
  "result_summary": "0 alertas activas (0 critical, 0 major)",
  "pass": true,
  "timestamp": "2025-12-14T18:53:32Z"
}
```

#### 4. **Sistema de Recomendaciones** 🔔
**Niveles**:
- **NOTIFY** (🔔 Accionable): Requiere atención inmediata
- **FYI** (ℹ️ Informativo): Solo información, sin acción requerida

**Criterios para NOTIFY**:
- Alertas critical/major con servicios degradados
- Aumento >50% en incidencias vs período anterior
- Error rate o latency por encima de umbrales
- Alertas críticas post-deployment

**Criterios para FYI**:
- Alertas minor/info sin impacto en salud
- Tendencia estable o descendente
- Sistema operando normalmente
- Query duplicada (dedupe)

#### 5. **Deduplicación Automática** 🔄
**Implementación**:
- Fingerprint estable: `hash(intent + params_sorted + report_keywords)`
- Cache in-memory con TTL de 30 minutos
- Capacidad: 100 entradas FIFO (`OrderedDict`)
- Limpieza automática de entradas expiradas

**Funciones**:
- `check_dedupe()`: Verifica si existe en cache
- `apply_dedupe_recommendation()`: Marca como FYI con nota

#### 6. **API Endpoint Unificado** 🚀
**Endpoint**: `POST /api/quick/command`

**Request**:
```json
{
  "command": "/novedades hoy"
}
```

**Response**:
```json
{
  "report": "# Incidencias Recientes...",
  "evidence": [...],
  "recommendation": {
    "level": "fyi",
    "reason": "Análisis completado sin situaciones críticas.",
    "confidence": 0.5
  },
  "canonical_command": "recent-incidents"
}
```

#### 7. **Frontend UI Mejorado** 🎨
**Características**:
- Interceptor de slash commands en el chat
- Render de evidencia en bloque colapsable `<details>`
- Sección destacada de recomendación con iconos
- Formato Markdown profesional

**Elementos visuales**:
- ✅ / ⚠️ : Estado de checks
- 🔔 / ℹ️ : Nivel de recomendación
- Timestamps legibles en locale
- Confianza en porcentaje

---

## 🎉 Conclusión

Se ha completado exitosamente la implementación de Quick Commands **v1.1** para el sistema de observabilidad. El sistema ahora ofrece:

### v1.0 (Original)
1. **5 comandos rápidos** para consultas comunes
2. **API REST completa** con documentación inline
3. **QueryAgent** para interpretar lenguaje natural
4. **Modo híbrido** (query directa + análisis IA preparado)
5. **Documentación completa** con ejemplos prácticos
6. **Testing automatizado** para validación continua

### v1.1 (Slash Commands) ✨
7. **Slash Commands** para ejecución desde el chat (`/novedades`, `/salud`, etc.)
8. **Sistema de Recomendaciones** NOTIFY vs FYI con confianza
9. **Verificación con Evidencia** automática para reducir ruido
10. **Deduplicación** con TTL de 30 min para evitar spam
11. **Prompts Optimizados** específicos por intención
12. **UI Mejorado** con evidencia colapsable y formato profesional
13. **Guía Visual** con capturas de pantalla

El sistema está **listo para producción** con reducción inteligente de ruido y notificaciones accionables. Las mejoras de Fase 2 pueden implementarse incrementalmente sin afectar la funcionalidad actual.

---

**Última actualización**: 2025-12-14 19:00 UTC  
**Estado**: ✅ v1.1 COMPLETADO Y PROBADO  
**Próximo hito**: Integración de análisis IA completo + Métricas reales de Prometheus (Fase 2)

