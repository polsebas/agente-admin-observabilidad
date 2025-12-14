"""API REST para Quick Commands de observabilidad."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agent.agents.query_agent import query_agent
from agent.slash_commands import (
    parse_slash_command,
    can_execute_via_rest,
    build_query_agent_prompt,
    CANONICAL_TO_ALIASES,
)

router = APIRouter()


class CommandRequest(BaseModel):
    """Request body para ejecutar un slash command."""
    command: str


@router.get("/quick/recent-incidents")
async def recent_incidents(
    hours: int = Query(default=24, ge=1, le=168, description="Ventana de tiempo en horas (1-168)"),
    severity: Optional[str] = Query(default=None, description="Filtrar por severidad (critical, major, minor, info)"),
    service: Optional[str] = Query(default=None, description="Filtrar por servicio"),
    include_duplicates: bool = Query(default=False, description="Incluir alertas duplicadas"),
    analyze_with_ai: bool = Query(default=False, description="Análisis enriquecido con IA"),
):
    """
    Obtiene reporte de incidencias recientes del sistema.
    
    **Ejemplos**:
    - `/api/quick/recent-incidents?hours=8` - Últimas 8 horas
    - `/api/quick/recent-incidents?hours=24&severity=critical` - Críticas de último día
    - `/api/quick/recent-incidents?service=auth-service&hours=12` - auth-service últimas 12h
    """
    try:
        prompt = f"Dame las incidencias recientes de las últimas {hours} horas"
        if severity:
            prompt += f" con severidad {severity}"
        if service:
            prompt += f" del servicio {service}"
        if include_duplicates:
            prompt += " incluyendo duplicadas"
        if analyze_with_ai:
            prompt += " con análisis detallado"
        
        result = await query_agent.arun(input=prompt)
        return {"report": result.content if hasattr(result, 'content') else str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener incidencias: {str(e)}")


@router.get("/quick/health")
async def service_health(
    services: Optional[str] = Query(default=None, description="Servicios separados por coma (ej: auth-service,payment-service)"),
    include_metrics: bool = Query(default=True, description="Incluir métricas actuales"),
    analyze_with_ai: bool = Query(default=False, description="Análisis con IA"),
):
    """
    Genera reporte del estado actual de salud de servicios.
    
    **Ejemplos**:
    - `/api/quick/health` - Todos los servicios monitoreados
    - `/api/quick/health?services=auth-service,payment-service` - Servicios específicos
    - `/api/quick/health?include_metrics=false` - Sin métricas detalladas
    """
    try:
        prompt = "Dame el health summary de los servicios"
        if services:
            prompt += f" {services}"
        if not include_metrics:
            prompt += " sin métricas detalladas"
        if analyze_with_ai:
            prompt += " con análisis detallado"
        
        result = await query_agent.arun(input=prompt)
        return {"report": result.content if hasattr(result, 'content') else str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener health summary: {str(e)}")


@router.get("/quick/post-deployment")
async def post_deployment(
    service: str = Query(..., description="Nombre del servicio deployado"),
    deployment_time: str = Query(..., description="Timestamp del deployment (ISO 8601)"),
    monitoring_window_hours: int = Query(default=2, ge=1, le=24, description="Ventana de monitoreo (1-24h)"),
    analyze_with_ai: bool = Query(default=True, description="Análisis con IA"),
):
    """
    Monitorea un servicio después de un deployment buscando anomalías.
    
    **Ejemplos**:
    - `/api/quick/post-deployment?service=auth-service&deployment_time=2025-12-10T14:00:00Z`
    - `/api/quick/post-deployment?service=payment-service&deployment_time=2025-12-10T16:30:00Z&monitoring_window_hours=4`
    """
    try:
        prompt = f"Monitorear post-deployment de {service} deployado el {deployment_time} durante {monitoring_window_hours} horas"
        if analyze_with_ai:
            prompt += " con análisis detallado"
        
        result = await query_agent.arun(input=prompt)
        return {"report": result.content if hasattr(result, 'content') else str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al monitorear post-deployment: {str(e)}")


@router.get("/quick/trends")
async def analyze_trends_endpoint(
    metric: str = Query(default="alert_count", description="Métrica a analizar (alert_count, error_rate, latency)"),
    service: Optional[str] = Query(default=None, description="Servicio a analizar (default: todos)"),
    period_hours: int = Query(default=24, ge=1, le=168, description="Período a analizar (1-168h)"),
    compare_with_previous: bool = Query(default=True, description="Comparar con período anterior"),
    analyze_with_ai: bool = Query(default=True, description="Análisis con IA"),
):
    """
    Analiza tendencias de métricas comparando períodos.
    
    **Ejemplos**:
    - `/api/quick/trends?metric=alert_count&period_hours=24` - Alertas últimas 24h vs 24h previas
    - `/api/quick/trends?metric=error_rate&service=auth-service&period_hours=12` - Error rate últimas 12h
    """
    try:
        prompt = f"Analizar tendencias de {metric}"
        if service:
            prompt += f" para el servicio {service}"
        prompt += f" en las últimas {period_hours} horas"
        if compare_with_previous:
            prompt += " comparando con el período anterior"
        if analyze_with_ai:
            prompt += " con análisis detallado"
        
        result = await query_agent.arun(input=prompt)
        return {"report": result.content if hasattr(result, 'content') else str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar tendencias: {str(e)}")


@router.get("/quick/daily-digest")
async def daily_digest(
    date: Optional[str] = Query(default=None, description="Fecha en formato YYYY-MM-DD (default: ayer)"),
    include_all_services: bool = Query(default=True, description="Incluir todos los servicios"),
    analyze_with_ai: bool = Query(default=True, description="Resumen ejecutivo con IA"),
):
    """
    Genera resumen diario de actividad del sistema.
    
    **Ejemplos**:
    - `/api/quick/daily-digest` - Digest de ayer
    - `/api/quick/daily-digest?date=2025-12-09` - Digest de fecha específica
    - `/api/quick/daily-digest?include_all_services=false` - Solo servicios con incidencias
    """
    try:
        prompt = "Generar resumen diario"
        if date:
            prompt += f" para la fecha {date}"
        else:
            prompt += " de ayer"
        if not include_all_services:
            prompt += " solo de servicios con incidencias"
        if analyze_with_ai:
            prompt += " con resumen ejecutivo detallado"
        
        result = await query_agent.arun(input=prompt)
        return {"report": result.content if hasattr(result, 'content') else str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar daily digest: {str(e)}")


@router.post("/quick/command")
async def execute_slash_command(request: CommandRequest):
    """
    Ejecuta un slash command con workflow de verificación, evidencia y dedupe.
    
    Este endpoint:
    1. Parsea el comando y resuelve aliases
    2. Ejecuta el comando base (vía QueryAgent o tool directo)
    3. Ejecuta workflow de verificación para obtener evidencia adicional
    4. Aplica deduplicación para evitar spam
    5. Devuelve reporte + evidencia + recomendación (notify/fyi)
    
    **Ejemplos**:
    - `{"command": "/novedades hoy"}` - Incidencias últimas 24h con verificación
    - `{"command": "/salud"}` - Health check con contexto de incidencias
    - `{"command": "/deploy service=auth-service deployment_time=2025-12-10T14:00:00Z"}` - Post-deployment con análisis
    """
    from agent.slash_commands import (
        run_verification_workflow,
        check_dedupe,
        apply_dedupe_recommendation,
    )
    
    try:
        parsed = parse_slash_command(request.command)
        
        if not parsed:
            raise HTTPException(status_code=400, detail=f"Comando inválido: {request.command}")
        
        canonical, params, args_text = parsed
        
        # Si es help, devolver ayuda
        if canonical == "help":
            help_data = await quick_commands_help()
            # Formatear como markdown para el chat
            report = "# Quick Commands - Ayuda\n\n"
            report += "Los comandos rápidos incluyen **verificación automática** de evidencia y **recomendaciones** sobre si la situación es accionable.\n\n"
            
            for cmd, info in help_data["quick_commands"].items():
                aliases = CANONICAL_TO_ALIASES.get(cmd, [])
                report += f"## {cmd}\n"
                report += f"**Aliases**: {', '.join([f'`/{a}`' for a in aliases])}\n\n"
                report += f"{info['description']}\n\n"
                report += f"**Ejemplo REST**: `{info['example']}`\n\n"
                if info.get("slash_examples"):
                    report += f"**Ejemplos slash**: " + ", ".join([f"`{ex}`" for ex in info["slash_examples"][:2]]) + "\n\n"
            
            report += "\n---\n\n"
            report += "## Interpretación de Recomendaciones\n\n"
            report += "- 🔔 **NOTIFY** (Accionable): Situación que requiere atención o acción inmediata\n"
            report += "- ℹ️ **FYI** (Informativo): Información útil pero sin acción requerida\n\n"
            report += "Cada reporte incluye:\n"
            report += "- **Evidencia**: Checks adicionales ejecutados para validar la situación\n"
            report += "- **Recomendación**: Nivel (notify/fyi), razón y confianza\n"
            
            return {"report": report}
        
        # Construir prompt para QueryAgent
        prompt = build_query_agent_prompt(canonical, params, args_text)
        
        # Ejecutar comando base con QueryAgent
        result = await query_agent.arun(input=prompt)
        base_report = result.content if hasattr(result, 'content') else str(result)
        
        # Ejecutar workflow de verificación con evidencia
        verification_result = run_verification_workflow(canonical, params, base_report)
        
        # Aplicar deduplicación
        is_duplicate, cached_report = check_dedupe(canonical, params, verification_result["report"])
        
        if is_duplicate:
            # Devolver resultado cacheado con nota de dedupe
            # Calcular tiempo transcurrido (aproximado)
            from datetime import datetime, timezone
            from agent.slash_commands import _dedupe_cache, _compute_fingerprint, _extract_keywords_from_report
            
            keywords = _extract_keywords_from_report(verification_result["report"])
            fingerprint = _compute_fingerprint(canonical, params, keywords)
            
            if fingerprint in _dedupe_cache:
                cached_entry = _dedupe_cache[fingerprint]
                time_since = (datetime.now(timezone.utc) - cached_entry["timestamp"]).total_seconds()
                verification_result = apply_dedupe_recommendation(verification_result, True, time_since)
        
        return verification_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando comando: {str(e)}")


@router.get("/quick/help")
async def quick_commands_help():
    """
    Muestra ayuda sobre los comandos rápidos disponibles.
    
    Incluye información sobre:
    - Aliases disponibles
    - Parámetros de cada comando
    - Ejemplos de uso (REST y slash)
    - Workflow de verificación automática
    """
    return {
        "quick_commands": {
            "recent-incidents": {
                "description": "Obtiene reporte de incidencias recientes con verificación de salud y tendencias",
                "aliases": CANONICAL_TO_ALIASES.get("recent-incidents", []),
                "parameters": {
                    "hours": "Ventana de tiempo (1-168h, default: 24)",
                    "severity": "Filtrar por severidad (critical, major, minor, info)",
                    "service": "Filtrar por servicio",
                    "include_duplicates": "Incluir duplicadas (default: false)",
                    "analyze_with_ai": "Análisis IA (default: false)",
                },
                "example": "/api/quick/recent-incidents?hours=8&severity=critical",
                "slash_examples": ["/novedades hoy", "/inc hours=8 severity=critical", "/ri 8h"],
                "verification_checks": ["health", "trends"],
            },
            "health": {
                "description": "Estado actual de salud de servicios con contexto de incidencias recientes",
                "aliases": CANONICAL_TO_ALIASES.get("health", []),
                "parameters": {
                    "services": "Servicios separados por coma (default: todos)",
                    "include_metrics": "Incluir métricas (default: true)",
                    "analyze_with_ai": "Análisis IA (default: false)",
                },
                "example": "/api/quick/health?services=auth-service,payment-service",
                "slash_examples": ["/salud", "/health services=auth-service,payment-service", "/estado"],
                "verification_checks": ["recent-incidents"],
            },
            "post-deployment": {
                "description": "Monitoreo post-deployment con comparación pre/post y análisis de anomalías",
                "aliases": CANONICAL_TO_ALIASES.get("post-deployment", []),
                "parameters": {
                    "service": "Nombre del servicio (required)",
                    "deployment_time": "Timestamp ISO 8601 (required)",
                    "monitoring_window_hours": "Ventana de monitoreo (1-24h, default: 2)",
                    "analyze_with_ai": "Análisis IA (default: true)",
                },
                "example": "/api/quick/post-deployment?service=auth-service&deployment_time=2025-12-10T14:00:00Z",
                "slash_examples": ["/deploy service=auth-service deployment_time=2025-12-10T14:00:00Z", "/pd service=auth deployment_time=2025-12-10T14:00:00Z"],
                "verification_checks": ["trends", "recent-incidents"],
            },
            "trends": {
                "description": "Análisis de tendencias con comparación de períodos y contexto de salud",
                "aliases": CANONICAL_TO_ALIASES.get("trends", []),
                "parameters": {
                    "metric": "Métrica a analizar (alert_count, error_rate, latency, default: alert_count)",
                    "service": "Servicio a analizar (default: todos)",
                    "period_hours": "Período a analizar (1-168h, default: 24)",
                    "compare_with_previous": "Comparar con período anterior (default: true)",
                    "analyze_with_ai": "Análisis IA (default: true)",
                },
                "example": "/api/quick/trends?metric=alert_count&period_hours=24",
                "slash_examples": ["/tendencias period_hours=48", "/tr metric=alert_count", "/tend 24h"],
                "verification_checks": ["health"],
            },
            "daily-digest": {
                "description": "Resumen diario con detección automática de incidentes críticos",
                "aliases": CANONICAL_TO_ALIASES.get("daily-digest", []),
                "parameters": {
                    "date": "Fecha YYYY-MM-DD (default: ayer)",
                    "include_all_services": "Incluir todos los servicios (default: true)",
                    "analyze_with_ai": "Resumen ejecutivo con IA (default: true)",
                },
                "example": "/api/quick/daily-digest?date=2025-12-09",
                "slash_examples": ["/digest ayer", "/diario date=2025-12-09", "/dd"],
                "verification_checks": [],
            },
        },
        "features": {
            "verification": "Cada comando ejecuta checks adicionales de evidencia para validar la situación",
            "deduplication": "Sistema de dedupe (TTL 30 min) para evitar notificaciones repetitivas",
            "recommendations": "Cada reporte incluye recomendación: NOTIFY (accionable) o FYI (informativo)",
        },
        "recommendation_criteria": {
            "notify": [
                "Alertas críticas o major con servicios degradados",
                "Aumento >50% en incidencias vs período anterior",
                "Error rate o latency por encima de umbrales",
                "Alertas críticas post-deployment",
            ],
            "fyi": [
                "Alertas minor/info sin impacto en salud",
                "Tendencia estable o descendente",
                "Sistema operando normalmente",
                "Query duplicada ejecutada recientemente",
            ],
        },
    }

