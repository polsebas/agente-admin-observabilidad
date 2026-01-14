"""
Mapa de aliases y parser para slash commands de Quick Commands.

Este módulo define los aliases/abreviaturas para cada quick command,
proporciona utilidades para parsear comandos desde el chat,
implementa prompts canónicos optimizados por intención,
y ejecuta workflows de verificación con evidencia para reducir ruido.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone
import re
import hashlib
import json
from collections import OrderedDict


# Mapa de aliases a comandos canónicos
COMMAND_ALIASES = {
    # Incidencias recientes (recent-incidents)
    "novedades": "recent-incidents",
    "nov": "recent-incidents",
    "incidencias": "recent-incidents",
    "inc": "recent-incidents",
    "ri": "recent-incidents",
    "recientes": "recent-incidents",
    
    # Salud (health)
    "salud": "health",
    "sal": "health",
    "health": "health",
    "estado": "health",
    
    # Post-deployment
    "deploy": "post-deployment",
    "dep": "post-deployment",
    "postdeploy": "post-deployment",
    "pd": "post-deployment",
    
    # Tendencias (trends)
    "tendencias": "trends",
    "tend": "trends",
    "trends": "trends",
    "tr": "trends",
    
    # Digest diario
    "digest": "daily-digest",
    "dig": "daily-digest",
    "diario": "daily-digest",
    "dd": "daily-digest",
    
    # Ayuda
    "qc": "help",
    "quick": "help",
    "quickhelp": "help",
    "help": "help",
}


# Mapa inverso: comando canónico → lista de aliases
CANONICAL_TO_ALIASES: Dict[str, List[str]] = {}
for alias, canonical in COMMAND_ALIASES.items():
    if canonical not in CANONICAL_TO_ALIASES:
        CANONICAL_TO_ALIASES[canonical] = []
    CANONICAL_TO_ALIASES[canonical].append(alias)


def parse_slash_command(input_text: str) -> Optional[Tuple[str, Dict[str, str], str]]:
    """
    Parsea un slash command del usuario.
    
    Args:
        input_text: Texto completo del input del usuario
        
    Returns:
        Tupla de (comando_canonico, params_dict, resto_texto) si es slash command,
        None si no es slash command.
        
    Examples:
        "/novedades hoy" -> ("recent-incidents", {"hours": "24"}, "hoy")
        "/salud service=auth-service" -> ("health", {"services": "auth-service"}, "service=auth-service")
        "/deploy service=x deployment_time=..." -> ("post-deployment", {...}, ...)
        "/qc" -> ("help", {}, "")
        "mensaje normal" -> None
    """
    if not input_text.startswith("/"):
        return None
    
    # Separar comando y argumentos
    parts = input_text[1:].split(maxsplit=1)
    if not parts:
        return None
    
    command_alias = parts[0].lower()
    args_text = parts[1] if len(parts) > 1 else ""
    
    # Resolver alias a comando canónico
    canonical = COMMAND_ALIASES.get(command_alias)
    if not canonical:
        return None
    
    # Si es help, no necesitamos parsear más
    if canonical == "help":
        return (canonical, {}, args_text)
    
    # Parsear argumentos
    params = {}
    
    # Patrón para key=value (ej: hours=8, service=auth-service, date=2025-12-09)
    key_value_pattern = r'(\w+)=([^\s]+)'
    matches = re.findall(key_value_pattern, args_text)
    for key, value in matches:
        params[key] = value
    
    # Atajos especiales
    args_lower = args_text.lower()
    
    # "hoy" -> últimas 24h
    if "hoy" in args_lower:
        if canonical == "recent-incidents":
            params.setdefault("hours", "24")
        elif canonical == "trends":
            params.setdefault("period_hours", "24")
    
    # "ayer" -> date de ayer
    if "ayer" in args_lower and canonical == "daily-digest":
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        params.setdefault("date", yesterday.strftime("%Y-%m-%d"))
    
    # Patrón de horas: "8h", "24h", etc.
    hour_pattern = r'(\d+)h\b'
    hour_match = re.search(hour_pattern, args_text, re.IGNORECASE)
    if hour_match:
        hours_value = hour_match.group(1)
        if canonical in ["recent-incidents"]:
            params.setdefault("hours", hours_value)
        elif canonical == "trends":
            params.setdefault("period_hours", hours_value)
    
    return (canonical, params, args_text)


def can_execute_via_rest(canonical_command: str, params: Dict[str, str]) -> bool:
    """
    Determina si un comando puede ejecutarse directamente via REST
    o si necesita fallback a QueryAgent.
    
    Args:
        canonical_command: Comando canónico (ej: "recent-incidents")
        params: Diccionario de parámetros parseados
        
    Returns:
        True si se puede ejecutar via REST, False si necesita QueryAgent
    """
    # Help siempre via REST
    if canonical_command == "help":
        return True
    
    # recent-incidents: no requiere params obligatorios
    if canonical_command == "recent-incidents":
        return True
    
    # health: no requiere params obligatorios
    if canonical_command == "health":
        return True
    
    # trends: no requiere params obligatorios
    if canonical_command == "trends":
        return True
    
    # daily-digest: no requiere params obligatorios
    if canonical_command == "daily-digest":
        return True
    
    # post-deployment: REQUIERE service y deployment_time
    if canonical_command == "post-deployment":
        return "service" in params and "deployment_time" in params
    
    return False


def build_rest_url(base_url: str, canonical_command: str, params: Dict[str, str]) -> str:
    """
    Construye la URL REST para un comando.
    
    Args:
        base_url: URL base del servidor (ej: "http://localhost:7777")
        canonical_command: Comando canónico
        params: Parámetros parseados
        
    Returns:
        URL completa con query params
    """
    if canonical_command == "help":
        return f"{base_url}/api/quick/help"
    
    # Mapa de comandos canónicos a endpoints
    endpoint_map = {
        "recent-incidents": "/api/quick/recent-incidents",
        "health": "/api/quick/health",
        "post-deployment": "/api/quick/post-deployment",
        "trends": "/api/quick/trends",
        "daily-digest": "/api/quick/daily-digest",
    }
    
    endpoint = endpoint_map.get(canonical_command)
    if not endpoint:
        raise ValueError(f"Unknown canonical command: {canonical_command}")
    
    url = f"{base_url}{endpoint}"
    
    # Agregar query params
    if params:
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={value}")
        url += "?" + "&".join(query_parts)
    
    return url


def build_query_agent_prompt(canonical_command: str, params: Dict[str, str], original_text: str) -> str:
    """
    Construye un prompt para QueryAgent basado en el comando parseado.
    
    Args:
        canonical_command: Comando canónico
        params: Parámetros parseados
        original_text: Texto original del argumento
        
    Returns:
        Prompt en lenguaje natural para QueryAgent
    """
    # Mapeo de comandos a frases naturales
    command_phrases = {
        "recent-incidents": "Dame las incidencias recientes",
        "health": "Dame el health summary de los servicios",
        "post-deployment": "Monitorear post-deployment",
        "trends": "Analizar tendencias",
        "daily-digest": "Generar resumen diario",
    }
    
    base_prompt = command_phrases.get(canonical_command, f"Ejecutar comando {canonical_command}")
    
    # Agregar contexto de los params
    if canonical_command == "recent-incidents":
        if "hours" in params:
            base_prompt += f" de las últimas {params['hours']} horas"
        if "severity" in params:
            base_prompt += f" con severidad {params['severity']}"
        if "service" in params:
            base_prompt += f" del servicio {params['service']}"
    
    elif canonical_command == "health":
        if "services" in params:
            base_prompt += f" {params['services']}"
        if params.get("include_metrics") == "false":
            base_prompt += " sin métricas detalladas"
    
    elif canonical_command == "post-deployment":
        if "service" in params:
            base_prompt += f" de {params['service']}"
        if "deployment_time" in params:
            base_prompt += f" deployado el {params['deployment_time']}"
        if "monitoring_window_hours" in params:
            base_prompt += f" durante {params['monitoring_window_hours']} horas"
    
    elif canonical_command == "trends":
        metric = params.get("metric", "alert_count")
        base_prompt += f" de {metric}"
        if "service" in params:
            base_prompt += f" para el servicio {params['service']}"
        if "period_hours" in params:
            base_prompt += f" en las últimas {params['period_hours']} horas"
    
    elif canonical_command == "daily-digest":
        if "date" in params:
            base_prompt += f" para la fecha {params['date']}"
        elif "ayer" in original_text.lower():
            base_prompt += " de ayer"
    
    # Detectar si el texto original contiene atajos o params que ya fueron procesados
    # Lista de tokens que no deben agregarse porque ya fueron procesados
    processed_tokens = set()
    
    # Atajos especiales que ya se convirtieron en params
    args_lower = original_text.lower()
    if "hoy" in args_lower and ("hours" in params or "period_hours" in params):
        processed_tokens.add("hoy")
    if "ayer" in args_lower and "date" in params:
        processed_tokens.add("ayer")
    
    # Patrón de horas (8h, 24h) que ya se convirtió en params
    hour_pattern = r'(\d+)h\b'
    if re.search(hour_pattern, original_text, re.IGNORECASE) and ("hours" in params or "period_hours" in params):
        # Marcar todo el patrón Xh como procesado
        for match in re.finditer(hour_pattern, original_text, re.IGNORECASE):
            processed_tokens.add(match.group(0).lower())
    
    # Keys de params que aparecen como key=value
    for key in params.keys():
        if f"{key}=" in original_text:
            # Marcar el pattern completo key=value como procesado
            pattern = rf'{key}=([^\s]+)'
            match = re.search(pattern, original_text)
            if match:
                processed_tokens.add(match.group(0))
    
    # Si había texto adicional que NO fue procesado, agregarlo
    # Tokenizar el texto original y filtrar los tokens procesados
    remaining_text = original_text
    for token in processed_tokens:
        remaining_text = remaining_text.replace(token, "")
    
    # Limpiar espacios múltiples y trim
    remaining_text = " ".join(remaining_text.split()).strip()
    
    # Solo agregar si queda algo significativo (más de 2 caracteres)
    if remaining_text and len(remaining_text) > 2:
        base_prompt += f" {remaining_text}"
    
    return base_prompt


# ============================================================================
# PROMPTS CANÓNICOS OPTIMIZADOS POR INTENCIÓN
# ============================================================================

# Plantillas de prompts optimizados para cada comando
# Cada plantilla define:
# - Qué decidir/diagnosticar
# - Evidencia mínima requerida
# - Formato de salida esperado

CANONICAL_PROMPTS = {
    "recent-incidents": {
        "system_role": "Analista de incidencias y observabilidad",
        "task": """Analizar incidencias recientes y determinar si representan problemas accionables o ruido.
        
Tu objetivo es:
1. Obtener las incidencias del período especificado
2. Verificar evidencia complementaria (salud actual, tendencias)
3. Determinar cuáles son verdaderamente accionables vs observacionales
4. Recomendar notify (accionable) o fyi (solo información)

CRITERIOS PARA NOTIFY:
- Critical o Major con servicios degradados
- Aumento >50% en incidencias vs período anterior
- Patrón de alertas sostenido (>3 en 1h del mismo tipo)
- Error rate o latency por encima de umbrales

CRITERIOS PARA FYI:
- Minor o Info sin impacto en salud
- Alertas esporádicas sin patrón
- Problema ya conocido/duplicado
- Tendencia descendente (mejorando)
""",
        "evidence_checks": ["health", "trends"],
        "output_format": "markdown con secciones: Resumen Ejecutivo, Incidencias Destacadas, Evidencia, Recomendación"
    },
    
    "health": {
        "system_role": "Especialista en salud de sistemas",
        "task": """Evaluar el estado actual de salud del sistema y determinar si hay situaciones accionables.

Tu objetivo es:
1. Obtener health summary de servicios
2. Verificar incidencias recientes (24h) para contexto
3. Identificar degradaciones o problemas críticos
4. Recomendar notify si hay acción requerida

CRITERIOS PARA NOTIFY:
- Servicios en estado CRITICAL o DEGRADED
- Error rate > umbral configurado
- Latency P95 > umbral configurado
- Alertas críticas activas
- Tendencia de empeoramiento

CRITERIOS PARA FYI:
- Todos los servicios HEALTHY
- Métricas dentro de umbrales
- Sin alertas críticas activas
""",
        "evidence_checks": ["recent-incidents"],
        "output_format": "markdown con secciones: Estado General, Servicios, Alertas Activas, Recomendación"
    },
    
    "post-deployment": {
        "system_role": "Especialista en post-deployment y rollback",
        "task": """Analizar el impacto de un deployment y determinar si es exitoso o requiere acción.

Tu objetivo es:
1. Comparar alertas pre/post deployment
2. Verificar tendencias durante la ventana de monitoreo
3. Detectar anomalías o degradaciones
4. Recomendar: exitoso, monitoreo continuo, o rollback

CRITERIOS PARA NOTIFY (Rollback):
- Alertas críticas nuevas post-deploy
- Aumento >2x en alertas vs pre-deploy
- Error rate o latency en degradación significativa
- Múltiples servicios impactados

CRITERIOS PARA NOTIFY (Monitoreo):
- Aumento moderado en alertas
- Una o dos alertas no críticas
- Tendencia no clara aún

CRITERIOS PARA FYI:
- Sin alertas nuevas post-deploy
- Métricas estables o mejorando
- Deployment limpio
""",
        "evidence_checks": ["trends", "recent-incidents"],
        "output_format": "markdown con secciones: Deployment Info, Comparación Pre/Post, Análisis de Anomalías, Recomendación"
    },
    
    "trends": {
        "system_role": "Analista de tendencias y predicción",
        "task": """Analizar tendencias de métricas y detectar cambios significativos.

Tu objetivo es:
1. Comparar período actual vs anterior
2. Identificar cambios porcentuales significativos
3. Detectar patrones (ascendente, descendente, estable)
4. Recomendar notify si hay tendencia preocupante

CRITERIOS PARA NOTIFY:
- Cambio >50% en alertas
- Tendencia ascendente sostenida (3+ períodos)
- Correlación con degradación de servicios
- Múltiples métricas empeorando

CRITERIOS PARA FYI:
- Cambio <30% en alertas
- Tendencia estable o descendente
- Sin correlación con degradación
""",
        "evidence_checks": ["health"],
        "output_format": "markdown con secciones: Período Analizado, Comparación, Tendencia, Recomendación"
    },
    
    "daily-digest": {
        "system_role": "Analista de reportes ejecutivos",
        "task": """Generar resumen diario destacando solo lo accionable y crítico.

Tu objetivo es:
1. Obtener actividad del día especificado
2. Identificar incidentes críticos y destacados
3. Comparar con día anterior para contexto
4. Recomendar notify solo si hubo incidentes importantes

CRITERIOS PARA NOTIFY:
- Incidentes críticos (>= 1)
- Incidentes major múltiples (>= 3)
- Aumento >100% vs día anterior
- Servicios con degradación prolongada

CRITERIOS PARA FYI:
- Sin incidentes críticos
- Actividad normal o baja
- Tendencia descendente
""",
        "evidence_checks": [],
        "output_format": "markdown con secciones: Resumen Ejecutivo, Incidentes Destacados, Tendencias, Recomendación"
    }
}


def build_canonical_prompt(intent: str, args: Dict[str, str], locale: str = "es-AR") -> str:
    """
    Construye un prompt canónico optimizado para un comando/intención.
    
    Args:
        intent: Comando canónico (recent-incidents, health, etc.)
        args: Argumentos parseados
        locale: Localización (default: es-AR)
        
    Returns:
        Prompt optimizado para QueryAgent o LLM
    """
    template = CANONICAL_PROMPTS.get(intent)
    if not template:
        # Fallback al prompt básico
        return build_query_agent_prompt(intent, args, "")
    
    # Construir prompt estructurado
    prompt_parts = [
        f"# ROL: {template['system_role']}",
        "",
        "# TAREA:",
        template['task'],
        "",
        "# PARÁMETROS:",
    ]
    
    # Agregar parámetros específicos
    if args:
        for key, value in args.items():
            prompt_parts.append(f"- {key}: {value}")
    else:
        prompt_parts.append("- (usar defaults)")
    
    prompt_parts.append("")
    prompt_parts.append(f"# FORMATO DE SALIDA: {template['output_format']}")
    prompt_parts.append("")
    prompt_parts.append("Genera el reporte solicitado en formato markdown.")
    
    return "\n".join(prompt_parts)


# ============================================================================
# WORKFLOW DE VERIFICACIÓN CON EVIDENCIA
# ============================================================================

def run_verification_workflow(
    intent: str,
    args: Dict[str, str],
    base_report: str
) -> Dict[str, Any]:
    """
    Ejecuta workflow de verificación para un comando, obteniendo evidencia adicional.
    
    Args:
        intent: Comando canónico
        args: Argumentos parseados
        base_report: Reporte base generado por el comando
        
    Returns:
        Dict con {
            "report": str,  # reporte final
            "evidence": List[Dict],  # lista de checks de evidencia
            "recommendation": Dict  # {level: notify|fyi, reason: str, confidence: float}
        }
    """
    from agent.storage import query_helpers
    
    evidence = []
    recommendation = {
        "level": "fyi",
        "reason": "Análisis completado sin situaciones críticas.",
        "confidence": 0.5
    }
    
    template = CANONICAL_PROMPTS.get(intent, {})
    evidence_checks = template.get("evidence_checks", [])
    
    # Ejecutar checks de evidencia según el comando
    if intent == "recent-incidents":
        # Check 1: Health actual
        if "health" in evidence_checks:
            try:
                active_alerts = query_helpers.get_active_alerts()
                critical_count = sum(1 for a in active_alerts if a["labels"].get("severity") == "critical")
                major_count = sum(1 for a in active_alerts if a["labels"].get("severity") == "major")
                
                health_pass = critical_count == 0 and major_count == 0
                evidence.append({
                    "source": "health_check",
                    "query": "get_active_alerts()",
                    "result_summary": f"{len(active_alerts)} alertas activas ({critical_count} critical, {major_count} major)",
                    "pass": health_pass,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Influencia en recomendación
                if not health_pass:
                    recommendation["level"] = "notify"
                    recommendation["reason"] = f"Sistema degradado: {critical_count} critical, {major_count} major activas"
                    recommendation["confidence"] = 0.9
            except Exception as e:
                evidence.append({
                    "source": "health_check",
                    "query": "get_active_alerts()",
                    "result_summary": f"Error: {str(e)}",
                    "pass": False,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        # Check 2: Trends (comparar con período anterior)
        if "trends" in evidence_checks:
            try:
                hours = int(args.get("hours", "24"))
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=hours)
                
                # Período actual
                alerts_current = query_helpers.get_alerts_in_timerange(start_time, end_time)
                
                # Período anterior
                prev_end = start_time
                prev_start = prev_end - timedelta(hours=hours)
                alerts_prev = query_helpers.get_alerts_in_timerange(prev_start, prev_end)
                
                change_pct = ((len(alerts_current) - len(alerts_prev)) / len(alerts_prev) * 100) if len(alerts_prev) > 0 else 0
                trends_pass = abs(change_pct) < 50
                
                evidence.append({
                    "source": "trends_check",
                    "query": f"compare_periods(hours={hours})",
                    "result_summary": f"Período actual: {len(alerts_current)}, anterior: {len(alerts_prev)}, cambio: {change_pct:+.1f}%",
                    "pass": trends_pass,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Influencia en recomendación
                if change_pct > 50:
                    recommendation["level"] = "notify"
                    recommendation["reason"] = f"Aumento significativo de incidencias: {change_pct:+.1f}%"
                    recommendation["confidence"] = 0.85
            except Exception as e:
                evidence.append({
                    "source": "trends_check",
                    "query": f"compare_periods(hours={hours})",
                    "result_summary": f"Error: {str(e)}",
                    "pass": False,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    elif intent == "health":
        # Check: Incidencias recientes (24h) para contexto
        if "recent-incidents" in evidence_checks:
            try:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                alerts = query_helpers.get_alerts_in_timerange(start_time, end_time)
                
                critical_count = sum(1 for a in alerts if a["labels"].get("severity") == "critical")
                incidents_pass = critical_count == 0
                
                evidence.append({
                    "source": "recent_incidents_check",
                    "query": "get_alerts_in_timerange(hours=24)",
                    "result_summary": f"{len(alerts)} alertas en 24h ({critical_count} critical)",
                    "pass": incidents_pass,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Influencia en recomendación
                if critical_count > 0:
                    recommendation["level"] = "notify"
                    recommendation["reason"] = f"Alertas críticas recientes: {critical_count} en últimas 24h"
                    recommendation["confidence"] = 0.9
            except Exception as e:
                evidence.append({
                    "source": "recent_incidents_check",
                    "query": "get_alerts_in_timerange(hours=24)",
                    "result_summary": f"Error: {str(e)}",
                    "pass": False,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    elif intent == "post-deployment":
        # Check 1: Trends alrededor del deployment
        if "trends" in evidence_checks:
            try:
                service = args.get("service", "")
                deployment_time_str = args.get("deployment_time", "")
                window_hours = int(args.get("monitoring_window_hours", "2"))
                
                if deployment_time_str:
                    deploy_time = datetime.fromisoformat(deployment_time_str.replace("Z", "+00:00"))
                    post_end = min(deploy_time + timedelta(hours=window_hours), datetime.now(timezone.utc))
                    alerts_post = query_helpers.get_alerts_in_timerange(deploy_time, post_end, service=service)
                    
                    # Pre-deploy
                    pre_start = deploy_time - timedelta(hours=2)
                    alerts_pre = query_helpers.get_alerts_in_timerange(pre_start, deploy_time, service=service)
                    
                    ratio = len(alerts_post) / len(alerts_pre) if len(alerts_pre) > 0 else (1 if len(alerts_post) == 0 else float('inf'))
                    trends_pass = ratio <= 2
                    
                    evidence.append({
                        "source": "post_deployment_trends",
                        "query": f"compare_pre_post_deploy(service={service})",
                        "result_summary": f"Pre: {len(alerts_pre)}, Post: {len(alerts_post)}, ratio: {ratio:.2f}x",
                        "pass": trends_pass,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Influencia en recomendación
                    critical_post = sum(1 for a in alerts_post if a["labels"].get("severity") == "critical")
                    if critical_post > 0:
                        recommendation["level"] = "notify"
                        recommendation["reason"] = f"Alertas críticas post-deploy: {critical_post}"
                        recommendation["confidence"] = 0.95
                    elif ratio > 2:
                        recommendation["level"] = "notify"
                        recommendation["reason"] = f"Aumento significativo de alertas post-deploy: {ratio:.1f}x"
                        recommendation["confidence"] = 0.8
            except Exception as e:
                evidence.append({
                    "source": "post_deployment_trends",
                    "query": "compare_pre_post_deploy",
                    "result_summary": f"Error: {str(e)}",
                    "pass": False,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    elif intent == "trends":
        # Check: Health actual para contexto
        if "health" in evidence_checks:
            try:
                active_alerts = query_helpers.get_active_alerts()
                critical_count = sum(1 for a in active_alerts if a["labels"].get("severity") == "critical")
                
                health_pass = critical_count == 0
                evidence.append({
                    "source": "health_check",
                    "query": "get_active_alerts()",
                    "result_summary": f"{len(active_alerts)} alertas activas ({critical_count} critical)",
                    "pass": health_pass,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Si hay tendencia ascendente Y sistema degradado → notify
                # (esto lo detectamos en el reporte base, aquí solo agregamos contexto)
            except Exception as e:
                evidence.append({
                    "source": "health_check",
                    "query": "get_active_alerts()",
                    "result_summary": f"Error: {str(e)}",
                    "pass": False,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    elif intent == "daily-digest":
        # Daily digest generalmente es FYI, pero notify si hubo incidentes críticos
        # Analizar el base_report para detectar keywords
        if "crítico" in base_report.lower() or "critical" in base_report.lower():
            critical_match = re.search(r'(\d+)\s+incidentes?\s+críticos?', base_report.lower())
            if critical_match:
                count = int(critical_match.group(1))
                if count > 0:
                    recommendation["level"] = "notify"
                    recommendation["reason"] = f"Día con {count} incidentes críticos"
                    recommendation["confidence"] = 0.9
    
    # Agregar evidencia al reporte
    evidence_section = "\n\n---\n\n## Evidencia de Verificación\n\n"
    for i, check in enumerate(evidence, 1):
        status_icon = "✅" if check["pass"] else "⚠️"
        evidence_section += f"**Check {i}**: {check['source']} {status_icon}\n"
        evidence_section += f"- Query: `{check['query']}`\n"
        evidence_section += f"- Resultado: {check['result_summary']}\n"
        evidence_section += f"- Timestamp: {check['timestamp']}\n\n"
    
    # Agregar recomendación al reporte
    recommendation_section = "\n\n---\n\n## Recomendación\n\n"
    if recommendation["level"] == "notify":
        recommendation_section += f"🔔 **NOTIFY** (Accionable)\n\n"
    else:
        recommendation_section += f"ℹ️ **FYI** (Informativo)\n\n"
    
    recommendation_section += f"**Razón**: {recommendation['reason']}\n\n"
    recommendation_section += f"**Confianza**: {recommendation['confidence']:.0%}\n"
    
    final_report = base_report + evidence_section + recommendation_section
    
    return {
        "report": final_report,
        "evidence": evidence,
        "recommendation": recommendation,
        "canonical_command": intent
    }


# ============================================================================
# DEDUPLICACIÓN / AGRUPADO (COOLDOWN)
# ============================================================================

from agent.storage.redis import get_redis

_DEDUPE_TTL_SECONDS = 30 * 60  # 30 minutos

def check_dedupe(intent: str, args: Dict[str, str], report: str) -> Tuple[bool, Optional[str]]:
    """
    Verifica si un comando/resultado ya fue ejecutado recientemente (dedupe).
    
    Args:
        intent: Comando canónico
        args: Argumentos
        report: Reporte generado
        
    Returns:
        Tupla de (is_duplicate, cached_report_if_duplicate)
    """
    redis = get_redis()
    
    # Calcular fingerprint
    keywords = _extract_keywords_from_report(report)
    fingerprint = _compute_fingerprint(intent, args, keywords)
    key = f"dedupe:{fingerprint}"
    
    # Buscar en redis
    cached_data = redis.get(key)
    if cached_data:
        try:
            cached_entry = json.loads(cached_data)
            return (True, cached_entry.get("report"))
        except json.JSONDecodeError:
            pass
    
    # No es duplicado, agregar al cache
    now = datetime.now(timezone.utc)
    entry = {
        "intent": intent,
        "args": args,
        "report": report,
        "timestamp": now.isoformat()
    }
    redis.setex(key, _DEDUPE_TTL_SECONDS, json.dumps(entry))
    
    return (False, None)


def apply_dedupe_recommendation(
    result: Dict[str, Any],
    is_duplicate: bool,
    time_since_seconds: Optional[float] = None
) -> Dict[str, Any]:
    """
    Aplica lógica de dedupe a la recomendación de un resultado.
    
    Args:
        result: Resultado del workflow de verificación
        is_duplicate: Si es duplicado
        time_since_seconds: Tiempo transcurrido desde el duplicado original
        
    Returns:
        Resultado modificado con recomendación ajustada
    """
    if not is_duplicate:
        return result
    
    # Es duplicado, cambiar a FYI
    result["recommendation"]["level"] = "fyi"
    
    if time_since_seconds:
        minutes_since = int(time_since_seconds / 60)
        result["recommendation"]["reason"] = f"Query ejecutada recientemente (hace {minutes_since} min). {result['recommendation']['reason']}"
    else:
        result["recommendation"]["reason"] = f"Query ejecutada recientemente. {result['recommendation']['reason']}"
    
    result["recommendation"]["confidence"] = max(result["recommendation"]["confidence"] - 0.2, 0.3)
    
    # Agregar nota al reporte
    dedupe_note = f"\n\n> **Nota**: Esta consulta fue ejecutada recientemente (hace ~{minutes_since if time_since_seconds else '?'} min). Los datos pueden no haber cambiado significativamente.\n"
    result["report"] = result["report"] + dedupe_note
    
    return result
