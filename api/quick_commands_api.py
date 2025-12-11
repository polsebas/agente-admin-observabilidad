"""API REST para Quick Commands de observabilidad."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from agent.agents.query_agent import query_agent

router = APIRouter()


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


@router.get("/quick/help")
async def quick_commands_help():
    """
    Muestra ayuda sobre los comandos rápidos disponibles.
    """
    return {
        "quick_commands": {
            "recent-incidents": {
                "description": "Obtiene reporte de incidencias recientes",
                "parameters": {
                    "hours": "Ventana de tiempo (1-168h, default: 24)",
                    "severity": "Filtrar por severidad (critical, major, minor, info)",
                    "service": "Filtrar por servicio",
                    "include_duplicates": "Incluir duplicadas (default: false)",
                    "analyze_with_ai": "Análisis IA (default: false)",
                },
                "example": "/api/quick/recent-incidents?hours=8&severity=critical",
            },
            "health": {
                "description": "Estado actual de salud de servicios",
                "parameters": {
                    "services": "Servicios separados por coma (default: todos)",
                    "include_metrics": "Incluir métricas (default: true)",
                    "analyze_with_ai": "Análisis IA (default: false)",
                },
                "example": "/api/quick/health?services=auth-service,payment-service",
            },
            "post-deployment": {
                "description": "Monitoreo post-deployment",
                "parameters": {
                    "service": "Nombre del servicio (required)",
                    "deployment_time": "Timestamp ISO 8601 (required)",
                    "monitoring_window_hours": "Ventana de monitoreo (1-24h, default: 2)",
                    "analyze_with_ai": "Análisis IA (default: true)",
                },
                "example": "/api/quick/post-deployment?service=auth-service&deployment_time=2025-12-10T14:00:00Z",
            },
            "trends": {
                "description": "Análisis de tendencias",
                "parameters": {
                    "metric": "Métrica a analizar (alert_count, error_rate, latency, default: alert_count)",
                    "service": "Servicio a analizar (default: todos)",
                    "period_hours": "Período a analizar (1-168h, default: 24)",
                    "compare_with_previous": "Comparar con período anterior (default: true)",
                    "analyze_with_ai": "Análisis IA (default: true)",
                },
                "example": "/api/quick/trends?metric=alert_count&period_hours=24",
            },
            "daily-digest": {
                "description": "Resumen diario",
                "parameters": {
                    "date": "Fecha YYYY-MM-DD (default: ayer)",
                    "include_all_services": "Incluir todos los servicios (default: true)",
                    "analyze_with_ai": "Resumen ejecutivo con IA (default: true)",
                },
                "example": "/api/quick/daily-digest?date=2025-12-09",
            },
        },
    }

