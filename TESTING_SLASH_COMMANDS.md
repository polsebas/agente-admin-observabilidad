# Testing - Slash Commands con Verificación y Evidencia

## Instalación de Dependencias de Testing

```bash
pip install pytest pytest-asyncio
```

## Ejecutar Tests

### Opción 1: Script Automatizado

```bash
./test_slash_commands.sh
```

### Opción 2: Tests Específicos

```bash
# Todos los tests unitarios
pytest test_slash_commands_unit.py -v

# Todos los tests de integración
pytest test_slash_commands_integration.py -v

# Test específico
pytest test_slash_commands_unit.py::TestParser::test_parse_novedades_hoy -v

# Con cobertura
coverage run -m pytest test_slash_commands_unit.py
coverage report --include="agent/slash_commands.py"
```

## Estructura de Tests

### Tests Unitarios (`test_slash_commands_unit.py`)

✅ **TestParser**: Parseo de comandos y aliases
- `/novedades hoy` → `recent-incidents` con `hours=24`
- `/salud` → `health` sin params
- `/deploy service=X deployment_time=Y` → extracción de params
- Atajos: `8h`, `ayer`, `hoy`

✅ **TestRestExecution**: Decisiones de ejecución REST vs QueryAgent
- Comandos sin params requeridos
- Post-deployment con/sin params

✅ **TestPromptBuilding**: Construcción de prompts canónicos
- Templates por comando
- Inyección de parámetros

✅ **TestDedupe**: Sistema de deduplicación
- Fingerprints consistentes
- Detección de duplicados dentro de TTL
- Cambio de recomendación a FYI

✅ **TestAliases**: Mapeo de aliases
- Todos los aliases mapeados correctamente
- Aliases cortos disponibles

✅ **TestVerificationWorkflow**: Workflow de verificación
- Estructura de respuesta correcta
- Evidencia y recomendación

### Tests de Integración (`test_slash_commands_integration.py`)

✅ **TestQuickCommandEndpoint**: Endpoint POST /api/quick/command
- `/qc` devuelve ayuda
- `/novedades hoy` ejecuta con evidencia y recomendación
- Comandos inválidos retornan 400
- Deduplicación funciona entre requests

✅ **TestQuickHelpEndpoint**: Endpoint GET /api/quick/help
- Estructura completa con aliases, features, criteria

✅ **TestQuickCommandRESTEndpoints**: Endpoints REST individuales
- GET /api/quick/recent-incidents
- GET /api/quick/health
- GET /api/quick/trends
- GET /api/quick/daily-digest

## Casos de Prueba Principales

### 1. Parser de Slash Commands

```python
# Test: /novedades hoy → recent-incidents con hours=24
result = parse_slash_command("/novedades hoy")
assert result[0] == "recent-incidents"
assert result[1]["hours"] == "24"
```

### 2. Workflow de Verificación

```python
# Test: Verificación genera evidencia
result = run_verification_workflow("recent-incidents", {"hours": "24"}, base_report)
assert "evidence" in result
assert "recommendation" in result
assert result["recommendation"]["level"] in ["notify", "fyi"]
```

### 3. Deduplicación

```python
# Test: Segundo comando idéntico es detectado como duplicado
check_dedupe("health", {}, "Report 1")  # Primera vez
is_dup, cached = check_dedupe("health", {}, "Report 1")  # Segunda vez
assert is_dup == True
```

### 4. Endpoint Integration

```bash
# Test manual con curl
curl -X POST http://localhost:7777/api/quick/command \
  -H "Content-Type: application/json" \
  -d '{"command": "/novedades hoy"}' | jq .

# Debe devolver:
# - report (markdown)
# - evidence (lista de checks)
# - recommendation (notify/fyi con reason y confidence)
# - canonical_command
```

## Verificación Manual

### 1. Test de Parser

```bash
python3 -c "
from agent.slash_commands import parse_slash_command
print(parse_slash_command('/novedades hoy'))
print(parse_slash_command('/salud'))
print(parse_slash_command('/deploy service=auth deployment_time=2025-12-14T14:00:00Z'))
"
```

### 2. Test de Aliases

```bash
python3 -c "
from agent.slash_commands import CANONICAL_TO_ALIASES
for cmd, aliases in CANONICAL_TO_ALIASES.items():
    print(f'{cmd}: {aliases}')
"
```

### 3. Test de Endpoint (requiere servidor corriendo)

```bash
# Levantar servidor
uvicorn main:app --port 7777 &

# Test commands
curl -X POST http://localhost:7777/api/quick/command \
  -H "Content-Type: application/json" \
  -d '{"command": "/qc"}'

curl -X POST http://localhost:7777/api/quick/command \
  -H "Content-Type: application/json" \
  -d '{"command": "/novedades hoy"}'

curl -X POST http://localhost:7777/api/quick/command \
  -H "Content-Type: application/json" \
  -d '{"command": "/salud"}'
```

## Casos Edge

### Comando Inválido

```bash
curl -X POST http://localhost:7777/api/quick/command \
  -d '{"command": "/comando_inexistente"}' | jq .
# Debe retornar 400
```

### Comando sin Slash

```bash
curl -X POST http://localhost:7777/api/quick/command \
  -d '{"command": "dame las novedades"}' | jq .
# Debe retornar 400
```

### Deduplicación (ejecutar 2 veces seguidas)

```bash
curl -X POST http://localhost:7777/api/quick/command \
  -d '{"command": "/tendencias period_hours=24"}' | jq '.recommendation.level'

# Inmediatamente después:
curl -X POST http://localhost:7777/api/quick/command \
  -d '{"command": "/tendencias period_hours=24"}' | jq '.recommendation'
# Debe ser "fyi" con nota de "recientemente"
```

## Cobertura Esperada

Módulos principales a testear:
- `agent/slash_commands.py`: Parser, prompts, verificación, dedupe
- `api/quick_commands_api.py`: Endpoints POST/GET
- `agent-ui/src/lib/slashCommands.ts`: Frontend parser

Objetivo de cobertura: **>80%** en módulos críticos

## Troubleshooting

### Error: "No module named pytest"

```bash
pip install pytest pytest-asyncio
```

### Error: "No module named agent"

Ejecutar desde el directorio raíz del proyecto:
```bash
cd /home/pablo/source/agente-admin
PYTHONPATH=. pytest test_slash_commands_unit.py
```

### Error: "Requiere DB inicializada"

Algunos tests de verificación requieren la DB. Inicializar:
```bash
python3 -c "
from agent.storage.alert_storage import init_db
init_db()
"
```

### Tests de Integración Fallan

Verificar que el servidor no esté corriendo (para evitar conflictos):
```bash
pkill -f "uvicorn main:app"
```

## CI/CD

Agregar a tu pipeline de CI:

```yaml
# .github/workflows/test.yml
- name: Run Slash Commands Tests
  run: |
    pip install pytest pytest-asyncio coverage
    pytest test_slash_commands_unit.py test_slash_commands_integration.py -v
    coverage report --fail-under=80
```

## Próximos Tests

- [ ] Tests de prompts canónicos (validar templates)
- [ ] Tests de criterios notify/fyi con casos reales
- [ ] Tests de performance (tiempo de respuesta < 2s)
- [ ] Tests de concurrencia (múltiples requests simultáneos)
- [ ] Tests de carga (100 requests/segundo)
- [ ] Tests E2E en frontend (Playwright/Cypress)

---

**Ver también**:
- [Documentación de Quick Commands](docs/QUICK_COMMANDS.md)
- [README principal](README.md)
