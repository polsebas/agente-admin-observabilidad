# Context Engineering - Quick Reference

Guía rápida para modificar el contexto de los agentes. Ver [CONTEXT_ENGINEERING.md](CONTEXT_ENGINEERING.md) para detalles completos.

## 🚀 Modificaciones Comunes

### ✏️ Cambiar Instrucciones de un Agente

```python
# agent/agents/<agent_name>.py
instructions=[
    "Nueva instrucción paso a paso",
    "PASO 1: Hacer X",
    "PASO 2: Hacer Y",
]
```

### 📝 Actualizar Additional Context del Team

```python
# agent/agents/observability_team.py
additional_context=f"""
## Nueva Sección
- Info relevante
- Políticas
- Runbooks
"""
```

### 🎯 Añadir Servicio Monitoreado

```python
# agent/config.py
monitored_services: List[str] = [
    "auth-service",
    "nuevo-servicio",  # AÑADIR AQUÍ
]
```

### 📊 Cambiar Thresholds

```python
# agent/config.py o .env
latency_threshold_ms: int = 300  # de 500ms a 300ms
error_rate_threshold: float = 0.005  # de 1% a 0.5%
```

### 📚 Añadir Few-Shot Example

```python
# agent/agents/report_agent.py
report_examples = [
    Message(role="user", content="..."),
    Message(role="assistant", content="..."),
    # AÑADIR NUEVO EJEMPLO
]
```

---

## 📋 Parámetros por Agente (Resumen)

| Agente | description | instructions | expected_output | additional_context | dependencies | history_runs |
|--------|------------|--------------|-----------------|-------------------|--------------|--------------|
| **WatchdogAgent** | ✅ | 6 pasos | JSON | Severidades, ventana | - | 3 |
| **TriageAgent** | ✅ | 6 pasos | JSON | - | Servicios, thresholds | 2 |
| **ReportAgent** | ✅ | 6 reglas | Markdown | - | - | 1 |
| **ObservabilityTeam** | ✅ | 6 fases | JSON | **SLOs, runbooks, dependencias** | - | 2 |

---

## 🔍 Testing Rápido

```bash
# 1. Reiniciar servidor
pkill -f "uvicorn main:app"
cd /home/pablo/source/agente-admin && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 7777

# 2. Enviar alerta de prueba
curl -X POST http://localhost:7777/api/alerts \
  -H "Content-Type: application/json" \
  -d @test-alert.json

# 3. Ver logs (debug_mode=True muestra system message)
tail -f ~/.cursor/projects/home-pablo-source-agente-admin/terminals/19.txt
```

---

## 📁 Archivos Clave

```
agent/
├── agents/
│   ├── watchdog_agent.py      ← Clasificación (description, instructions, additional_context)
│   ├── triage_agent.py         ← Correlación (description, instructions, dependencies)
│   ├── report_agent.py         ← Reportes (description, instructions, additional_input)
│   └── observability_team.py   ← Líder (description, instructions, additional_context)
├── config.py                   ← monitored_services, thresholds (dependencies)
└── tools/
    ├── alert_tools.py          ← Tools de clasificación
    └── observability_tools.py  ← Tools de correlación
```

---

## ⚠️ Common Pitfalls

| ❌ Don't | ✅ Do |
|----------|-------|
| Instrucciones vagas: "Analizá la alerta" | "PASO 1: Extraé service de labels.service o labels.job" |
| `num_history_runs=100` (muy caro) | `num_history_runs=2-5` (balance óptimo) |
| Hardcodear valores en instructions | Usar `dependencies` para config dinámica |
| Sin `expected_output` | Definir estructura exacta del output |
| Duplicar info en varios lugares | Centralizar en `additional_context` |

---

## 📊 Checklist de Calidad

Después de modificar el contexto, verificar:

- [ ] System message se genera correctamente (ver logs con `debug_mode=True`)
- [ ] Alerta de prueba se procesa sin errores
- [ ] Reporte tiene estructura esperada (Alert Summary, Timeline, Evidence, Root Cause, Next Steps)
- [ ] Nivel de confianza está presente (High/Medium/Low)
- [ ] Next steps son accionables y específicos
- [ ] Token usage razonable (< 10K tokens por alerta)
- [ ] Tiempo de respuesta aceptable (< 2 minutos)

---

## 🔗 Enlaces Rápidos

- [Documentación Completa](CONTEXT_ENGINEERING.md)
- [Agno Context Engineering](https://docs.agno.com/basics/context/team/overview)
- [Agent Reference](https://docs.agno.com/reference/agents/agent)
- [Team Reference](https://docs.agno.com/reference/teams/team)

