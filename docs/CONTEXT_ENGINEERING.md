# Context Engineering - Sistema de Observabilidad

Este documento explica cómo funciona el context engineering en el sistema de análisis de alertas con Agno Framework, y cómo modificarlo para futuros cambios.

## 📚 Índice

1. [Qué es Context Engineering](#qué-es-context-engineering)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Parámetros por Agente](#parámetros-por-agente)
4. [Cómo Modificar el Contexto](#cómo-modificar-el-contexto)
5. [Best Practices](#best-practices)
6. [Referencias](#referencias)

---

## Qué es Context Engineering

**Context Engineering** es el proceso de diseñar y controlar la información (contexto) que se envía a los modelos de lenguaje (LLMs) para guiar su comportamiento y outputs.

En Agno, el contexto de un agente o team consiste en:
- **System message**: Contexto principal con instrucciones, descripción, roles, etc.
- **User message**: Mensaje del usuario o alerta a procesar
- **Chat history**: Historial de conversación previa (si está habilitado)
- **Additional input**: Ejemplos few-shot u otro input adicional

### ¿Por qué es importante?

Un buen context engineering resulta en:
- ✅ Respuestas más precisas y consistentes
- ✅ Mejor comprensión del dominio y políticas
- ✅ Outputs estructurados y predecibles
- ✅ Reducción de alucinaciones o errores

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    ObservabilityTeam (Líder)                 │
│  - Coordina el flujo secuencial de análisis                 │
│  - Delega tareas a agentes especializados                   │
│  - Conoce SLOs, runbooks, dependencias (additional_context) │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬───────────────────┐
        │                       │                   │
        ▼                       ▼                   ▼
┌──────────────┐      ┌─────────────────┐   ┌─────────────┐
│ WatchdogAgent│      │  TriageAgent    │   │ ReportAgent │
│ Clasificación│      │  Correlación    │   │  Síntesis   │
│ Deduplicación│      │  Métricas/Logs/ │   │  Reportes   │
│              │      │  Traces         │   │  Markdown   │
└──────────────┘      └─────────────────┘   └─────────────┘
```

**Flujo de Análisis:**
1. **WatchdogAgent**: Clasifica severidad, detecta duplicados, enriquece contexto
2. **TriageAgent**: Correlaciona métricas de Prometheus, logs de Loki, traces de Tempo
3. **ReportAgent**: Genera reporte markdown con timeline, evidencia, causa raíz, next steps

---

## Parámetros por Agente

### WatchdogAgent

**Ubicación**: `agent/agents/watchdog_agent.py`

| Parámetro | Valor | Propósito |
|-----------|-------|-----------|
| `description` | Descripción de rol de primera línea | Explica al LLM su función en el sistema |
| `role` | "Clasificar severidad, deduplicar y enriquecer alertas" | Rol conciso del agente |
| `instructions` | 6 pasos detallados | Guía paso a paso del proceso de clasificación |
| `expected_output` | JSON con campos específicos | Define estructura del output esperado |
| `additional_context` | Niveles de severidad, ventana de deduplicación | Info estática que no cambia entre runs |
| `add_history_to_context` | `True` | Recuerda alertas previas del mismo servicio |
| `num_history_runs` | `3` | Últimas 3 runs en contexto |
| `tools` | `classify_alert_severity`, `check_alert_history`, etc. | Herramientas disponibles |

**Cuándo modificar:**
- **Cambio en niveles de severidad**: Editar `additional_context`
- **Nuevo paso en clasificación**: Añadir a `instructions`
- **Más contexto histórico**: Aumentar `num_history_runs`

---

### TriageAgent

**Ubicación**: `agent/agents/triage_agent.py`

| Parámetro | Valor | Propósito |
|-----------|-------|-----------|
| `description` | Proceso de correlación de señales | Explica análisis de métricas/logs/traces |
| `role` | "Correlacionar métricas, logs y traces..." | Rol del agente |
| `instructions` | 6 pasos de correlación temporal | Metodología de análisis |
| `expected_output` | JSON con secciones metrics/logs/traces/findings | Estructura del output |
| `dependencies` | Servicios monitoreados, thresholds | Configuración dinámica inyectada |
| `add_dependencies_to_context` | `True` | Incluye config en el contexto |
| `add_history_to_context` | `True` | Recuerda análisis previos |
| `num_history_runs` | `2` | Últimos 2 análisis |

**Cuándo modificar:**
- **Nuevo threshold**: Actualizar `agent/config.py` (se inyecta automáticamente)
- **Nuevo servicio monitoreado**: Añadir a `monitored_services` en config
- **Nuevo paso de correlación**: Añadir a `instructions`

---

### ReportAgent

**Ubicación**: `agent/agents/report_agent.py`

| Parámetro | Valor | Propósito |
|-----------|-------|-----------|
| `description` | Estándares de reporte | Define calidad y estilo de reportes |
| `role` | "Generar reportes en markdown..." | Rol del agente |
| `instructions` | 6 reglas de formato y estilo | Guías de escritura |
| `expected_output` | Markdown con 5 secciones | Estructura del reporte |
| `additional_input` | 2 ejemplos de reportes completos | Few-shot learning |
| `add_history_to_context` | `True` | Mantiene estilo consistente |
| `num_history_runs` | `1` | Solo último reporte como referencia |

**Cuándo modificar:**
- **Cambio en formato de reporte**: Actualizar `expected_output` e `instructions`
- **Nuevo ejemplo de reporte**: Añadir a `additional_input` (few-shot examples)
- **Nueva sección en reporte**: Actualizar `expected_output` y añadir ejemplo

---

### ObservabilityTeam

**Ubicación**: `agent/agents/observability_team.py`

| Parámetro | Valor | Propósito |
|-----------|-------|-----------|
| `description` | Explicación del equipo y flujo secuencial | Contexto del team líder |
| `role` | "Orquestar análisis de alertas" | Rol del team líder |
| `instructions` | 6 reglas de delegación por fase | Flujo de coordinación |
| `expected_output` | Estructura JSON completa | Output final esperado |
| `additional_context` | SLOs, runbooks, dependencias, políticas | **Info crítica para decisiones** |
| `add_history_to_context` | `True` | Recuerda alertas previas en sesión |
| `num_history_runs` | `2` | Últimos 2 análisis completos |
| `max_tool_calls_from_history` | `10` | Limita tool calls para optimizar tokens |
| `add_datetime_to_context` | `True` | Añade timestamp actual |
| `show_members_responses` | `True` | Muestra outputs de agentes (debug) |

**Cuándo modificar:**
- **Nuevo servicio crítico**: Actualizar `additional_context` sección "Servicios Monitoreados"
- **Cambio en SLOs**: Actualizar `additional_context` sección "SLOs y Thresholds"
- **Nueva política de análisis**: Añadir a `additional_context` sección "Políticas de Análisis"
- **Nueva dependencia**: Añadir a `additional_context` sección "Dependencias entre Servicios"

---

## Cómo Modificar el Contexto

### 1. Cambiar Instrucciones de un Agente

**Archivo**: `agent/agents/<nombre_agente>.py`

```python
# Ejemplo: Añadir nuevo paso al WatchdogAgent
instructions=[
    "Paso 1: ...",
    "Paso 2: ...",
    "NUEVO PASO 3: Verificar si el servicio está en mantenimiento programado",
    "Paso 4: ...",
]
```

### 2. Actualizar Additional Context del Team

**Archivo**: `agent/agents/observability_team.py`

```python
additional_context=f"""
## SLOs y Thresholds Críticos
- Availability target: 99.95% uptime  # CAMBIO AQUÍ
- Error rate threshold: < {_config.error_rate_threshold * 100}%
...

## NUEVA SECCIÓN: Ventanas de Mantenimiento
- Postgres backups: Diariamente 02:00-02:30 UTC
- Deployment windows: Martes y Jueves 14:00-16:00 UTC
- Durante mantenimiento: NO escalar alertas de servicios afectados
"""
```

### 3. Añadir Few-Shot Example al ReportAgent

**Archivo**: `agent/agents/report_agent.py`

```python
report_examples = [
    # Ejemplos existentes...
    
    # NUEVO EJEMPLO para un tipo de alerta diferente
    Message(
        role="user",
        content="Alert: Disk space > 90% on database server..."
    ),
    Message(
        role="assistant",
        content="""# Alert Analysis Report
...
"""
    ),
]
```

### 4. Modificar Configuración Dinámica (Dependencies)

**Archivo**: `agent/config.py`

```python
# Context dependencies para agents
monitored_services: List[str] = [
    "auth-service",
    "api-gateway",
    "payment-service",
    "user-service",
    "notification-service",
    "analytics-service",  # NUEVO SERVICIO
]
latency_threshold_ms: int = int(os.getenv("LATENCY_THRESHOLD_MS", "300"))  # CAMBIO de 500 a 300
error_rate_threshold: float = float(os.getenv("ERROR_RATE_THRESHOLD", "0.005"))  # CAMBIO de 0.01 a 0.005
```

Estos valores se inyectan automáticamente al `TriageAgent` vía `dependencies`.

### 5. Ajustar Historial de Contexto

**Cuándo aumentar `num_history_runs`:**
- ✅ Si los agentes necesitan más contexto histórico para mejores decisiones
- ❌ Si el contexto se vuelve muy grande (alto costo de tokens)

**Cuándo usar `max_tool_calls_from_history`:**
- Limita la cantidad de tool calls del historial incluidos en el contexto
- Útil para evitar que el contexto crezca demasiado en sesiones largas

```python
# Ejemplo: Aumentar historial para análisis más complejos
triage_agent = Agent(
    ...,
    add_history_to_context=True,
    num_history_runs=5,  # CAMBIO: de 2 a 5 runs previas
)
```

---

## Best Practices

### ✅ Do's

1. **Instrucciones Específicas y Paso a Paso**
   - ✅ "PASO 1: Extraé service, instance, alertname de labels"
   - ❌ "Extraé información relevante"

2. **Expected Output Estructurado**
   - ✅ "JSON con {severity: str, is_duplicate: bool, context: {...}}"
   - ❌ "Devolvé la información"

3. **Additional Context para Info Estática**
   - ✅ SLOs, runbooks, dependencias conocidas
   - ❌ Datos que cambian entre requests (usar dependencies)

4. **Few-Shot Examples para Outputs Complejos**
   - ✅ 2-3 ejemplos completos de reportes bien formateados
   - ❌ Un solo ejemplo o ejemplos incompletos

5. **Dependencies para Config Dinámica**
   - ✅ Servicios monitoreados, thresholds configurables
   - ❌ Hardcodear valores en instructions

### ❌ Don'ts

1. **No Sobrecargar el Contexto**
   - ❌ `num_history_runs=100` (muy caro en tokens)
   - ✅ `num_history_runs=2-5` (balance óptimo)

2. **No Duplicar Información**
   - ❌ Repetir los mismos SLOs en instructions Y additional_context
   - ✅ Definir una vez en additional_context

3. **No Usar Lenguaje Ambiguo**
   - ❌ "Analizá si es grave"
   - ✅ "Clasificá severidad como: critical, major, minor, info según estos criterios..."

4. **No Ignorar el Expected Output**
   - Siempre definir la estructura exacta que esperas
   - El LLM lo usará como guía para formatear el output

---

## Testing de Cambios

### 1. Probar con Alertas de Prueba

```bash
# Enviar alerta de prueba
curl -X POST http://localhost:7777/api/alerts \
  -H "Content-Type: application/json" \
  -d @test-alert.json
```

### 2. Revisar Logs de Debug

Con `debug_mode=True`, verás el system message completo en los logs:

```bash
tail -f /home/pablo/.cursor/projects/home-pablo-source-agente-admin/terminals/19.txt
```

Buscar líneas que comienzan con:
- `DEBUG ***************** Agent ID: ...`
- System message completo generado por Agno

### 3. Validar Outputs

- ✅ El reporte sigue la estructura esperada?
- ✅ El nivel de confianza está presente?
- ✅ Las sugerencias son accionables?
- ✅ El lenguaje es técnico pero claro?

---

## Ejemplos Prácticos de Modificaciones

### Ejemplo 1: Añadir Nuevo Tipo de Severidad

**Problema**: Queremos añadir severidad "warning" entre "minor" e "info"

**Solución**:

```python
# 1. Actualizar agent/tools/alert_tools.py
def _classify_alert_severity_raw(labels, annotations):
    sev = labels.get("severity", "").lower()
    if sev in {"critical", "crit", "p0", "p1"}:
        return "critical"
    if sev in {"major", "high", "p2"}:
        return "major"
    if sev in {"minor", "medium", "p3"}:
        return "minor"
    if sev in {"warning", "warn", "p4"}:  # NUEVO
        return "warning"
    # ... resto del código
    return "info"

# 2. Actualizar agent/agents/watchdog_agent.py - additional_context
additional_context=(
    "Niveles de severidad:\n"
    "- critical: Sistema caído, servicio inaccesible\n"
    "- major: Errores 5xx, degradación significativa\n"
    "- minor: Latencia elevada pero tolerable\n"
    "- warning: Advertencias preventivas, recursos cerca del límite\n"  # NUEVO
    "- info: Notificaciones informativas\n"
    ...
)

# 3. Actualizar instructions si es necesario
instructions=[
    ...,
    "PASO 2: Clasificar severidad - usá labels.severity si existe; sino inferí de annotations: "
    "critical (sistema caído), major (error 5xx), minor (latencia alta), warning (preventivo), info (informativo)",
    ...
]
```

### Ejemplo 2: Añadir Integración con Sistema de Ticketing

**Problema**: Queremos que el ReportAgent incluya info sobre creación de tickets

**Solución**:

```python
# 1. Actualizar agent/agents/observability_team.py - additional_context
additional_context=f"""
...

## Sistema de Ticketing (Jira)
- Severidad Critical/Major: Crear ticket automáticamente (no en Fase 1, solo mencionarlo)
- Template de ticket: https://jira.empresa.com/templates/incident
- Labels obligatorios: severity, affected_service, alert_fingerprint
- Proyecto: OPS-INCIDENTS

...
"""

# 2. Actualizar agent/agents/report_agent.py - instructions
instructions=[
    ...,
    "En Next Steps, si la severidad es Critical o Major, incluir: 'Crear ticket de incidente en Jira (proyecto OPS-INCIDENTS) con labels apropiados'",
]
```

### Ejemplo 3: Añadir Correlación con Deployments

**Problema**: Queremos que el TriageAgent correlacione alertas con deployments recientes

**Solución**:

```python
# 1. Crear nueva tool en agent/tools/observability_tools.py
@tool
def query_recent_deployments(service: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Consulta deployments recientes de un servicio en las últimas N horas."""
    # Implementación que consulta tu sistema de CI/CD
    pass

# 2. Añadir tool al TriageAgent en agent/agents/triage_agent.py
triage_agent = Agent(
    ...,
    tools=[
        observability_tools.query_prometheus_metrics,
        ...,
        observability_tools.query_recent_deployments,  # NUEVO
    ],
    instructions=[
        ...,
        "PASO 6: Correlacionar con deployments - buscar deployments recientes (últimas 24-48h) del servicio afectado usando query_recent_deployments",
        "FORMATO DE SALIDA: JSON con {..., deployments: {recent_deploys[], correlation}}",
    ],
)

# 3. Actualizar expected_output
expected_output=(
    "JSON estructurado con secciones: "
    "metrics (...), logs (...), traces (...), "
    "deployments (recent_deploys array, correlation string), "  # NUEVO
    "findings (...)"
)
```

---

## Monitoreo de Calidad del Context Engineering

### Métricas a Observar

1. **Token Usage**: Costo por análisis
   - Objetivo: < 10,000 tokens por alerta
   - Si supera: Reducir `num_history_runs` o `max_tool_calls_from_history`

2. **Tiempo de Respuesta**: Latencia del análisis
   - Objetivo: < 2 minutos por alerta
   - Si supera: Optimizar instructions o reducir tool calls

3. **Calidad de Reportes**: Evaluación manual
   - ✅ Estructura correcta?
   - ✅ Nivel de confianza presente?
   - ✅ Next steps accionables?
   - ✅ Sin alucinaciones?

4. **Tasa de Re-análisis**: % alertas que requieren re-run
   - Objetivo: < 5%
   - Si supera: Mejorar instructions o examples

---

## Referencias

### Documentación de Agno

- [Context Engineering - Overview](https://docs.agno.com/basics/context/team/overview)
- [Context Engineering - For Teams](https://docs.agno.com/basics/context/team/usage)
- [Agent Reference](https://docs.agno.com/reference/agents/agent)
- [Team Reference](https://docs.agno.com/reference/teams/team)
- [Few-Shot Prompting](https://docs.agno.com/basics/context/team/overview#additional-input)

### Guías Externas

- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering](https://docs.anthropic.com/claude/docs/prompt-engineering)

### Archivos Clave del Proyecto

- `agent/agents/watchdog_agent.py` - Agente de clasificación
- `agent/agents/triage_agent.py` - Agente de correlación
- `agent/agents/report_agent.py` - Agente de reportes
- `agent/agents/observability_team.py` - Team líder
- `agent/config.py` - Configuración centralizada
- `agent/tools/alert_tools.py` - Tools de alertas
- `agent/tools/observability_tools.py` - Tools de observabilidad

---

## Changelog

### 2025-12-10
- ✅ Implementado context engineering completo en todos los agentes
- ✅ Añadido `additional_context` al ObservabilityTeam con SLOs, runbooks, dependencias
- ✅ Configurados `add_history_to_context` y `num_history_runs` en todos los agentes
- ✅ Añadidos few-shot examples al ReportAgent
- ✅ Configuradas dependencies (servicios, thresholds) en TriageAgent
- ✅ Creada documentación completa de context engineering

---

## Contacto y Soporte

Para preguntas sobre context engineering o modificaciones al sistema:
- Ver ejemplos en: `test-alert-report.md`
- Consultar logs: `/home/pablo/.cursor/projects/home-pablo-source-agente-admin/terminals/`
- Referencias: Links en sección "Referencias" arriba

