"""Agente Report: genera reportes legibles."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.message import Message
from agno.db.sqlite import AsyncSqliteDb

from agent.config import AdminAgentConfig
from agent.tools import report_tools

_config = AdminAgentConfig()

# Few-shot examples de reportes bien formateados
report_examples = [
    Message(
        role="user",
        content=(
            "Alert: High latency on auth-service, P95=2.5s. "
            "Triage: error_rate=0%, slow traces found with database queries taking 2-3s."
        ),
    ),
    Message(
        role="assistant",
        content="""# Alert Analysis Report

## Alert Summary
- **Service**: auth-service
- **Severity**: Major
- **Issue**: High latency (P95: 2.5s, threshold: 500ms)
- **Time**: 2025-12-10 14:30 UTC

## Timeline
- 14:25 UTC: Latency spike detected
- 14:27 UTC: P95 latency reaches 2.5s
- 14:30 UTC: Alert triggered

## Evidence
**Metrics**:
- Error rate: 0% (no errors detected)
- Latency P95: 2.5s (5x normal baseline of 500ms)

**Traces**:
- 15 slow traces found (>2s)
- Common pattern: database query to `users` table taking 2-3s

## Root Cause Analysis
High latency is caused by slow database queries on the `users` table. No errors detected, indicating the service is functional but degraded.

**Confidence**: High (consistent pattern across all slow traces)

## Next Steps
1. Investigar database performance: revisar índices en tabla `users`
2. Analizar query plan de las queries lentas
3. Considerar añadir índice en columna `email` si las queries filtran por ese campo
4. Monitorear database CPU y IOPS
""",
    ),
    Message(
        role="user",
        content=(
            "Alert: Error 5xx spike on payment-service. "
            "Triage: error_rate=15%, logs show 'Connection timeout to postgres', traces show failed DB connections."
        ),
    ),
    Message(
        role="assistant",
        content="""# Alert Analysis Report

## Alert Summary
- **Service**: payment-service
- **Severity**: Critical
- **Issue**: Error 5xx spike (15% error rate)
- **Time**: 2025-12-10 16:45 UTC

## Timeline
- 16:40 UTC: First connection timeout errors
- 16:43 UTC: Error rate reaches 10%
- 16:45 UTC: Alert triggered at 15% error rate

## Evidence
**Metrics**:
- Error rate: 15% (threshold: 1%)
- Latency P95: 5.2s (degraded)
- Service health: Partially degraded

**Logs**:
- 127 errors with pattern "Connection timeout to postgres"
- Database connection pool exhausted
- No application-level exceptions

**Traces**:
- 43 failed requests due to database timeout
- All failures occur at DB connection acquisition stage

## Root Cause Analysis
Payment service is experiencing database connection timeouts. Connection pool is exhausted, causing 15% of requests to fail. This indicates either insufficient connection pool size or database performance issues.

**Confidence**: High (clear pattern across metrics, logs, and traces)

## Next Steps
1. Revisar configuración del connection pool de payment-service (aumentar max_connections si es necesario)
2. Verificar performance de la base de datos postgres (CPU, memory, active connections)
3. Analizar queries lentas en postgres con pg_stat_statements
4. Considerar implementar circuit breaker para prevenir cascada de errores
5. Escalar horizontalmente payment-service si el problema persiste
""",
    ),
]

report_agent = Agent(
    name="ReportAgent",
    role="Generar reportes en markdown y sugerir próximos pasos",
    description=(
        "Agente de síntesis que genera reportes de análisis de alertas en formato markdown. "
        "Estructura la información de forma clara y accionable, incluyendo timeline de eventos, "
        "evidencia correlacionada de múltiples fuentes, análisis de causa raíz y sugerencias "
        "de próximos pasos para el equipo de DevOps."
    ),
    model=OpenAIChat(id=_config.agno_model),
    db=AsyncSqliteDb(db_file="./agno.db"),
    debug_mode=True,
    add_history_to_context=True,
    num_history_runs=1,
    additional_input=report_examples,
    tools=[
        report_tools.generate_markdown_report,
        report_tools.suggest_next_steps,
    ],
    instructions=[
        "Sos el agente de reporte final. Tu objetivo es comunicar hallazgos de forma clara y accionable.",
        "Usá la estructura: ## Alert Summary, ## Timeline, ## Evidence, ## Root Cause Analysis, ## Next Steps",
        "En Evidence, categorizá por fuente (Metrics, Logs, Traces) y destacá los valores clave",
        "En Root Cause Analysis, explicá la causa raíz con nivel de confianza (High/Medium/Low)",
        "En Next Steps, enumerá acciones concretas sin ejecutarlas (Fase 1 solo análisis)",
        "Usá markdown, sin emojis, lenguaje técnico pero claro",
    ],
    expected_output=(
        "Markdown con secciones: "
        "## Alert Summary (service, severity, issue, time), "
        "## Timeline (eventos cronológicos), "
        "## Evidence (Metrics, Logs, Traces con valores clave), "
        "## Root Cause Analysis (explicación + confidence level), "
        "## Next Steps (lista numerada de acciones recomendadas)"
    ),
    markdown=True,
)


