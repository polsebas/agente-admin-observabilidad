"""Quick commands para consultas prediseñadas de observabilidad."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from agno.tools import tool

from agent.config import AdminAgentConfig
from agent.storage import query_helpers

_config = AdminAgentConfig()


@tool
def get_recent_incidents(
    hours: Optional[int] = 24,
    severity: Optional[str] = None,
    service: Optional[str] = None,
    include_duplicates: bool = False,
    analyze_with_ai: bool = False,
) -> str:
    """
    Obtiene reporte de incidencias recientes del sistema.
    
    Args:
        hours: Ventana de tiempo en horas (default: 24)
        severity: Filtrar por severidad específica (critical, major, minor, info)
        service: Filtrar por servicio específico
        include_duplicates: Incluir alertas duplicadas
        analyze_with_ai: Si True, usa ReportAgent para análisis enriquecido
        
    Returns:
        Markdown con reporte de incidencias
    """
    hours = hours or 24
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    # Query directa a storage
    alerts = query_helpers.get_alerts_in_timerange(
        start_time=start_time,
        end_time=end_time,
        severity=severity,
        service=service,
        include_duplicates=include_duplicates,
    )
    
    # Generar markdown
    report = f"# Incidencias Recientes (Últimas {hours} horas)\n\n"
    report += f"**Período**: {start_time.strftime('%Y-%m-%d %H:%M UTC')} - {end_time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    
    if not alerts:
        report += "✅ **No se registraron incidencias en este período.**\n"
        return report
    
    # Resumen ejecutivo
    severity_summary = query_helpers.get_alerts_summary_by_severity(hours)
    service_summary = query_helpers.get_alerts_summary_by_service(hours)
    
    report += "## Resumen Ejecutivo\n"
    report += f"- **Total de alertas**: {len(alerts)}\n"
    report += f"- **Critical**: {severity_summary['critical']} | "
    report += f"**Major**: {severity_summary['major']} | "
    report += f"**Minor**: {severity_summary['minor']} | "
    report += f"**Info**: {severity_summary['info']}\n"
    
    if service_summary:
        top_services = sorted(service_summary.items(), key=lambda x: x[1], reverse=True)[:3]
        report += f"- **Servicios más afectados**: " + ", ".join([f"{s} ({c})" for s, c in top_services]) + "\n"
    
    report += "\n"
    
    # Agrupar por severidad
    for sev in ["critical", "major", "minor", "info"]:
        sev_alerts = [a for a in alerts if a["labels"].get("severity", "").lower() == sev]
        if not sev_alerts:
            continue
        
        report += f"## Incidencias {sev.title()}\n\n"
        
        for alert in sev_alerts[:10]:  # Máximo 10 por severidad
            received_at = datetime.fromisoformat(alert["received_at"]).strftime("%Y-%m-%d %H:%M UTC")
            alertname = alert["labels"].get("alertname", "Unknown")
            service_name = alert["labels"].get("service", "unknown")
            summary = alert["annotations"].get("summary", "")
            status = alert["status"]
            
            report += f"### [{received_at}] {service_name} - {alertname}\n"
            report += f"- **Severidad**: {sev.title()}\n"
            report += f"- **Estado**: {status}\n"
            if summary:
                report += f"- **Resumen**: {summary}\n"
            if alert.get("is_duplicate"):
                report += f"- **Duplicada**: Sí\n"
            report += "\n"
    
    # TODO: Si analyze_with_ai=True, invocar ReportAgent para análisis más profundo
    if analyze_with_ai:
        report += "\n---\n\n"
        report += "_Nota: Análisis con IA no implementado aún. Use analyze_with_ai=False para reporte básico._\n"
    
    return report


@tool
def get_service_health_summary(
    services: Optional[List[str]] = None,
    include_metrics: bool = True,
    analyze_with_ai: bool = False,
) -> str:
    """
    Genera reporte del estado actual de salud de servicios.
    
    Args:
        services: Lista de servicios a revisar (default: todos monitoreados)
        include_metrics: Incluir métricas actuales (error rate, latency)
        analyze_with_ai: Si True, usa TriageAgent para análisis
        
    Returns:
        Markdown con health summary
    """
    services = services or _config.monitored_services
    
    report = "# Service Health Summary\n\n"
    report += f"**Timestamp**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    
    # Obtener alertas activas
    active_alerts = query_helpers.get_active_alerts()
    alerts_by_service = {}
    for alert in active_alerts:
        svc = alert["labels"].get("service", "unknown")
        if svc not in alerts_by_service:
            alerts_by_service[svc] = []
        alerts_by_service[svc].append(alert)
    
    # Determinar estado general
    critical_count = sum(1 for a in active_alerts if a["labels"].get("severity") == "critical")
    major_count = sum(1 for a in active_alerts if a["labels"].get("severity") == "major")
    
    if critical_count > 0:
        overall_status = "🔴 CRITICAL"
    elif major_count > 0:
        overall_status = "🟡 DEGRADED"
    else:
        overall_status = "🟢 HEALTHY"
    
    report += f"## Estado General: {overall_status}\n\n"
    report += f"- **Alertas activas**: {len(active_alerts)}\n"
    report += f"- **Critical**: {critical_count} | **Major**: {major_count}\n\n"
    
    # Health de cada servicio
    for service in services:
        service_alerts = alerts_by_service.get(service, [])
        
        # Determinar icono de estado
        if any(a["labels"].get("severity") == "critical" for a in service_alerts):
            status_icon = "🔴"
            status_text = "CRITICAL"
        elif any(a["labels"].get("severity") == "major" for a in service_alerts):
            status_icon = "🟡"
            status_text = "DEGRADED"
        elif service_alerts:
            status_icon = "🟠"
            status_text = "WARNING"
        else:
            status_icon = "🟢"
            status_text = "HEALTHY"
        
        report += f"### {service} {status_icon}\n"
        report += f"- **Status**: {status_text}\n"
        
        # Métricas actuales
        if include_metrics:
            metrics = query_helpers.get_current_service_metrics(service)
            if "error" not in metrics:
                error_rate = metrics.get("error_rate", "N/A")
                latency_p95 = metrics.get("latency_p95", "N/A")
                
                report += f"- **Error rate**: {error_rate}"
                if isinstance(error_rate, (int, float)) and error_rate > _config.error_rate_threshold:
                    report += " ⚠️"
                report += f" (threshold: {_config.error_rate_threshold * 100}%)\n"
                
                report += f"- **Latency P95**: {latency_p95}"
                if isinstance(latency_p95, (int, float)) and latency_p95 > _config.latency_threshold_ms:
                    report += " ⚠️"
                report += f" (threshold: {_config.latency_threshold_ms}ms)\n"
            else:
                report += f"- **Métricas**: Error obteniendo métricas ({metrics['error']})\n"
        
        # Alertas activas
        report += f"- **Alertas activas**: {len(service_alerts)}"
        if service_alerts:
            severities = [a["labels"].get("severity", "unknown") for a in service_alerts]
            report += f" ({', '.join(set(severities))})"
        report += "\n\n"
    
    # TODO: Si analyze_with_ai=True, invocar TriageAgent
    if analyze_with_ai:
        report += "\n---\n\n"
        report += "_Nota: Análisis con IA no implementado aún._\n"
    
    return report


@tool
def monitor_post_deployment(
    service: str,
    deployment_time: str,
    monitoring_window_hours: int = 2,
    analyze_with_ai: bool = True,
) -> str:
    """
    Monitorea un servicio después de un deployment buscando anomalías.
    
    Args:
        service: Nombre del servicio deployado
        deployment_time: Timestamp del deployment (ISO 8601)
        monitoring_window_hours: Ventana de monitoreo post-deploy (default: 2h)
        analyze_with_ai: Si True, usa TriageAgent para detectar anomalías
        
    Returns:
        Markdown con reporte de post-deployment
    """
    try:
        deploy_time = datetime.fromisoformat(deployment_time.replace("Z", "+00:00"))
    except ValueError:
        return f"# Error\n\nFormato de deployment_time inválido: {deployment_time}. Use formato ISO 8601."
    
    end_time = deploy_time + timedelta(hours=monitoring_window_hours)
    
    # Si end_time está en el futuro, usar tiempo actual
    now = datetime.now(timezone.utc)
    if end_time > now:
        end_time = now
        actual_window = (end_time - deploy_time).total_seconds() / 3600
    else:
        actual_window = monitoring_window_hours
    
    report = f"# Post-Deployment Monitoring: {service}\n\n"
    
    report += "## Deployment Info\n"
    report += f"- **Service**: {service}\n"
    report += f"- **Deploy time**: {deploy_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    report += f"- **Monitoring window**: {actual_window:.1f} hours\n"
    report += f"- **Current time**: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    
    # Alertas post-deploy
    alerts_post = query_helpers.get_alerts_in_timerange(
        start_time=deploy_time,
        end_time=end_time,
        service=service,
    )
    
    report += "## Alertas Post-Deploy\n"
    if not alerts_post:
        report += "✅ **No se detectaron alertas después del deployment.**\n\n"
    else:
        report += f"⚠️ **{len(alerts_post)} alertas detectadas:**\n\n"
        for alert in alerts_post[:5]:  # Máximo 5
            time_after_deploy = (datetime.fromisoformat(alert["received_at"]) - deploy_time).total_seconds() / 60
            alertname = alert["labels"].get("alertname", "Unknown")
            severity = alert["labels"].get("severity", "unknown")
            summary = alert["annotations"].get("summary", "")
            
            report += f"- **{int(time_after_deploy)} minutos post-deploy**: {alertname} ({severity})\n"
            if summary:
                report += f"  - {summary}\n"
        report += "\n"
    
    # Comparación pre/post deploy (placeholder)
    pre_deploy_start = deploy_time - timedelta(hours=2)
    alerts_pre = query_helpers.get_alerts_in_timerange(
        start_time=pre_deploy_start,
        end_time=deploy_time,
        service=service,
    )
    
    report += "## Comparación Pre/Post Deploy\n"
    report += f"- **Alertas pre-deploy** (2h antes): {len(alerts_pre)}\n"
    report += f"- **Alertas post-deploy** ({actual_window:.1f}h después): {len(alerts_post)}\n"
    
    if len(alerts_post) > len(alerts_pre):
        report += f"- **Cambio**: +{len(alerts_post) - len(alerts_pre)} alertas ⚠️\n"
    elif len(alerts_post) < len(alerts_pre):
        report += f"- **Cambio**: {len(alerts_post) - len(alerts_pre)} alertas ✅\n"
    else:
        report += "- **Cambio**: Sin cambios\n"
    
    report += "\n"
    
    # Recomendación
    report += "## Recomendación\n"
    if not alerts_post:
        report += "✅ **DEPLOYMENT EXITOSO** - No se detectaron anomalías en la ventana de monitoreo.\n"
    elif any(a["labels"].get("severity") == "critical" for a in alerts_post):
        report += "🔴 **ROLLBACK RECOMENDADO** - Se detectaron alertas críticas post-deploy.\n"
    elif len(alerts_post) > len(alerts_pre) * 2:
        report += "⚠️ **MONITOREO INTENSIVO** - Aumento significativo de alertas. Considerar rollback si persiste.\n"
    else:
        report += "🟡 **MONITOREO CONTINUO** - Alertas detectadas. Mantener observación.\n"
    
    # TODO: Si analyze_with_ai=True, invocar TriageAgent para análisis más profundo
    if analyze_with_ai:
        report += "\n---\n\n"
        report += "_Nota: Análisis detallado con IA no implementado aún._\n"
    
    return report


@tool
def analyze_trends(
    service: Optional[str] = None,
    metric: str = "alert_count",
    period_hours: int = 24,
    compare_with_previous: bool = True,
    analyze_with_ai: bool = True,
) -> str:
    """
    Analiza tendencias de métricas comparando períodos.
    
    Args:
        service: Servicio a analizar (default: todos)
        metric: Métrica a analizar (alert_count, error_rate, latency)
        period_hours: Período actual a analizar (default: 24h)
        compare_with_previous: Comparar con período anterior
        analyze_with_ai: Si True, usa ReportAgent para insights
        
    Returns:
        Markdown con análisis de tendencias
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=period_hours)
    
    report = f"# Trend Analysis: {metric}\n\n"
    report += f"**Período actual**: {start_time.strftime('%Y-%m-%d %H:%M UTC')} - {end_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
    if service:
        report += f"**Servicio**: {service}\n"
    report += "\n"
    
    if metric == "alert_count":
        # Análisis de tendencia de conteo de alertas
        if compare_with_previous:
            # Período anterior
            prev_end = start_time
            prev_start = prev_end - timedelta(hours=period_hours)
            
            comparison = query_helpers.compare_metric_periods(
                service=service or "all",
                metric=metric,
                period1_start=start_time,
                period1_end=end_time,
                period2_start=prev_start,
                period2_end=prev_end,
            )
            
            p1_value = comparison["period1"]["value"]
            p2_value = comparison["period2"]["value"]
            change_pct = comparison["change_pct"]
            
            report += "## Comparación de Períodos\n"
            report += f"- **Período actual** (últimas {period_hours}h): {p1_value} alertas\n"
            report += f"- **Período anterior** ({period_hours}h previas): {p2_value} alertas\n"
            report += f"- **Cambio**: {change_pct:+.1f}%"
            
            if abs(change_pct) > 50:
                report += " ⚠️ (cambio significativo)"
            elif change_pct > 0:
                report += " ↗️"
            elif change_pct < 0:
                report += " ↘️"
            report += "\n\n"
        
        # Resumen del período actual
        alerts = query_helpers.get_alerts_in_timerange(
            start_time=start_time,
            end_time=end_time,
            service=service,
        )
        
        if alerts:
            severity_summary = {}
            for alert in alerts:
                sev = alert["labels"].get("severity", "unknown")
                severity_summary[sev] = severity_summary.get(sev, 0) + 1
            
            report += "### Desglose por Severidad\n"
            for sev, count in sorted(severity_summary.items(), key=lambda x: x[1], reverse=True):
                report += f"- **{sev.title()}**: {count}\n"
            report += "\n"
    
    else:
        # Otras métricas (error_rate, latency) - placeholder
        report += f"⚠️ Análisis de métrica '{metric}' no implementado aún. Use 'alert_count'.\n"
    
    # TODO: Si analyze_with_ai=True, invocar ReportAgent para insights
    if analyze_with_ai:
        report += "\n---\n\n"
        report += "_Nota: Insights con IA no implementados aún._\n"
    
    return report


@tool
def generate_daily_digest(
    date: Optional[str] = None,
    include_all_services: bool = True,
    analyze_with_ai: bool = True,
) -> str:
    """
    Genera resumen diario de actividad del sistema.
    
    Args:
        date: Fecha del digest en formato YYYY-MM-DD (default: ayer)
        include_all_services: Incluir todos los servicios o solo con incidencias
        analyze_with_ai: Si True, usa ReportAgent para resumen ejecutivo
        
    Returns:
        Markdown con digest diario
    """
    if date:
        try:
            target_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        except ValueError:
            return f"# Error\n\nFormato de fecha inválido: {date}. Use formato YYYY-MM-DD."
    else:
        # Default: ayer
        target_date = datetime.now(timezone.utc) - timedelta(days=1)
    
    # Rango del día completo
    start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)
    
    report = f"# Daily Digest: {start_time.strftime('%Y-%m-%d')}\n\n"
    
    # Obtener todas las alertas del día
    alerts = query_helpers.get_alerts_in_timerange(
        start_time=start_time,
        end_time=end_time,
    )
    
    if not alerts:
        report += "✅ **No se registraron incidencias en este día.**\n"
        return report
    
    # Métricas del día
    severity_summary = {}
    service_summary = {}
    
    for alert in alerts:
        sev = alert["labels"].get("severity", "unknown")
        severity_summary[sev] = severity_summary.get(sev, 0) + 1
        
        svc = alert["labels"].get("service", "unknown")
        service_summary[svc] = service_summary.get(svc, 0) + 1
    
    critical_count = severity_summary.get("critical", 0)
    major_count = severity_summary.get("major", 0)
    
    # Resumen ejecutivo (placeholder - puede ser mejorado con IA)
    report += "## Resumen Ejecutivo\n"
    if critical_count == 0 and major_count == 0:
        report += f"El sistema operó sin incidentes críticos. Se registraron {len(alerts)} alertas menores.\n"
    else:
        report += f"Se registraron {critical_count} incidentes críticos y {major_count} mayores en el día. "
        top_service = max(service_summary.items(), key=lambda x: x[1])
        report += f"{top_service[0]} tuvo el mayor número de alertas ({top_service[1]}).\n"
    report += "\n"
    
    # Métricas del día
    report += "## Métricas del Día\n"
    report += f"- **Total alertas**: {len(alerts)}\n"
    report += f"- **Critical**: {severity_summary.get('critical', 0)} | "
    report += f"**Major**: {severity_summary.get('major', 0)} | "
    report += f"**Minor**: {severity_summary.get('minor', 0)} | "
    report += f"**Info**: {severity_summary.get('info', 0)}\n"
    report += "\n"
    
    # Incidentes destacados (top 3 critical)
    critical_alerts = [a for a in alerts if a["labels"].get("severity") == "critical"]
    if critical_alerts:
        report += "## Incidentes Destacados\n\n"
        for i, alert in enumerate(critical_alerts[:3], 1):
            time_str = datetime.fromisoformat(alert["received_at"]).strftime("%H:%M UTC")
            service_name = alert["labels"].get("service", "unknown")
            alertname = alert["labels"].get("alertname", "Unknown")
            summary = alert["annotations"].get("summary", "")
            
            report += f"{i}. **[{time_str}]** {service_name} - {alertname}\n"
            if summary:
                report += f"   - {summary}\n"
        report += "\n"
    
    # Servicios con mayor actividad
    if service_summary:
        report += "## Servicios con Mayor Actividad\n"
        top_services = sorted(service_summary.items(), key=lambda x: x[1], reverse=True)[:5]
        for service, count in top_services:
            if include_all_services or count > 0:
                report += f"- **{service}**: {count} alertas\n"
        report += "\n"
    
    # Tendencias vs día anterior (placeholder)
    prev_start = start_time - timedelta(days=1)
    prev_end = start_time
    prev_alerts = query_helpers.get_alerts_in_timerange(prev_start, prev_end)
    
    if prev_alerts:
        change_pct = ((len(alerts) - len(prev_alerts)) / len(prev_alerts)) * 100
        report += "## Tendencias vs Día Anterior\n"
        report += f"- **Alertas**: {change_pct:+.0f}%\n"
    
    # TODO: Si analyze_with_ai=True, ReportAgent genera resumen ejecutivo mejorado
    if analyze_with_ai:
        report += "\n---\n\n"
        report += "_Nota: Resumen ejecutivo con IA no implementado aún._\n"
    
    return report

