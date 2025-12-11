"""Helper functions para queries optimizadas de alertas y métricas."""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from agent.config import AdminAgentConfig
from tools import prometheus_tool

_config = AdminAgentConfig()


def _connect():
    """Conecta a la base de datos SQLite."""
    return sqlite3.connect(_config.agno_db_path, check_same_thread=False)


def get_alerts_in_timerange(
    start_time: datetime,
    end_time: datetime,
    severity: Optional[str] = None,
    service: Optional[str] = None,
    include_duplicates: bool = False,
) -> List[Dict[str, Any]]:
    """
    Query optimizado para alertas en rango de tiempo.
    
    Args:
        start_time: Inicio del rango
        end_time: Fin del rango
        severity: Filtrar por severidad específica
        service: Filtrar por servicio específico
        include_duplicates: Incluir alertas duplicadas
        
    Returns:
        Lista de alertas en el rango especificado
    """
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Base query
        query = """
            SELECT id, fingerprint, status, labels, annotations, 
                   received_at, analysis_report, is_duplicate
            FROM alerts
            WHERE received_at >= ? AND received_at <= ?
        """
        params = [start_time.isoformat(), end_time.isoformat()]
        
        # Filtro de duplicados
        if not include_duplicates:
            query += " AND is_duplicate = 0"
        
        # Filtros adicionales por labels (severity y service)
        # Nota: labels está en JSON, necesitamos parsearlo
        query += " ORDER BY received_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        alerts = []
        for row in rows:
            alert = dict(zip(columns, row))
            
            # Parsear JSON de labels y annotations
            import json
            alert["labels"] = json.loads(alert["labels"]) if alert["labels"] else {}
            alert["annotations"] = json.loads(alert["annotations"]) if alert["annotations"] else {}
            
            # Filtros post-query (porque labels está en JSON)
            if severity and alert["labels"].get("severity", "").lower() != severity.lower():
                continue
            if service and alert["labels"].get("service") != service:
                continue
                
            alerts.append(alert)
        
        return alerts


def get_active_alerts() -> List[Dict[str, Any]]:
    """
    Obtiene todas las alertas actualmente en estado 'firing'.
    
    Returns:
        Lista de alertas activas
    """
    with _connect() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT id, fingerprint, status, labels, annotations, 
                   received_at, analysis_report, is_duplicate
            FROM alerts
            WHERE status = 'firing'
            AND is_duplicate = 0
            ORDER BY received_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        alerts = []
        import json
        for row in rows:
            alert = dict(zip(columns, row))
            alert["labels"] = json.loads(alert["labels"]) if alert["labels"] else {}
            alert["annotations"] = json.loads(alert["annotations"]) if alert["annotations"] else {}
            alerts.append(alert)
        
        return alerts


def get_current_service_metrics(service: str) -> Dict[str, Any]:
    """
    Obtiene métricas actuales de un servicio desde Prometheus.
    
    Args:
        service: Nombre del servicio
        
    Returns:
        Diccionario con métricas actuales (error_rate, latency_p95, etc.)
    """
    try:
        # Error rate
        error_rate = prometheus_tool.get_http_error_rate(service)
        
        # Latency P95
        latency_p95 = prometheus_tool.get_http_latency_p95(service)
        
        # Service health (up/down)
        health = prometheus_tool.get_service_health()
        service_health = next((h for h in health if h.get("service") == service), None)
        
        return {
            "service": service,
            "error_rate": error_rate,
            "latency_p95": latency_p95,
            "health": service_health,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "service": service,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def compare_metric_periods(
    service: str,
    metric: str,
    period1_start: datetime,
    period1_end: datetime,
    period2_start: datetime,
    period2_end: datetime,
) -> Dict[str, Any]:
    """
    Compara una métrica entre dos períodos.
    
    Args:
        service: Nombre del servicio
        metric: Métrica a comparar ("error_rate", "latency", "alert_count")
        period1_start: Inicio del período 1
        period1_end: Fin del período 1
        period2_start: Inicio del período 2
        period2_end: Fin del período 2
        
    Returns:
        Diccionario con comparación de métricas
    """
    if metric == "alert_count":
        # Comparar conteo de alertas entre períodos
        alerts_p1 = get_alerts_in_timerange(period1_start, period1_end, service=service)
        alerts_p2 = get_alerts_in_timerange(period2_start, period2_end, service=service)
        
        p1_count = len(alerts_p1)
        p2_count = len(alerts_p2)
        change_pct = ((p1_count - p2_count) / p2_count * 100) if p2_count > 0 else 0
        
        return {
            "metric": metric,
            "service": service,
            "period1": {
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat(),
                "value": p1_count,
            },
            "period2": {
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat(),
                "value": p2_count,
            },
            "change_pct": change_pct,
        }
    
    # Para métricas de Prometheus, necesitaríamos query_range
    # Por ahora, placeholder
    return {
        "metric": metric,
        "service": service,
        "error": "Comparación de métricas de Prometheus no implementada aún",
    }


def get_alerts_summary_by_severity(hours: int = 24) -> Dict[str, int]:
    """
    Obtiene conteo de alertas por severidad en las últimas N horas.
    
    Args:
        hours: Ventana de tiempo en horas
        
    Returns:
        Diccionario con conteo por severidad
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    alerts = get_alerts_in_timerange(start_time, end_time)
    
    summary = {"critical": 0, "major": 0, "minor": 0, "info": 0, "unknown": 0}
    
    for alert in alerts:
        severity = alert["labels"].get("severity", "unknown").lower()
        if severity in summary:
            summary[severity] += 1
        else:
            summary["unknown"] += 1
    
    return summary


def get_alerts_summary_by_service(hours: int = 24) -> Dict[str, int]:
    """
    Obtiene conteo de alertas por servicio en las últimas N horas.
    
    Args:
        hours: Ventana de tiempo en horas
        
    Returns:
        Diccionario con conteo por servicio
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    alerts = get_alerts_in_timerange(start_time, end_time)
    
    summary = {}
    
    for alert in alerts:
        service = alert["labels"].get("service", "unknown")
        summary[service] = summary.get(service, 0) + 1
    
    return summary

