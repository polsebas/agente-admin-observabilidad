# Changelog

Todos los cambios notables del proyecto se documentan en este archivo.

---

## [v1.1.0] - 2025-12-14

### ✨ Nuevas Características

#### Slash Commands en el Chat
- **Ejecutá Quick Commands directamente desde el chat** con sintaxis `/comando`
- **Aliases intuitivos**: `/novedades`, `/salud`, `/deploy`, `/tendencias`, `/digest`, `/qc`
- **Parsing inteligente**: Soporta `key=value` y shortcuts (`hoy`, `ayer`, `8h`, `24h`)
- **Modo híbrido**: REST directo o fallback a QueryAgent según parámetros disponibles

#### Sistema de Recomendaciones Inteligentes
- **Clasificación automática**: NOTIFY (🔔 accionable) vs FYI (ℹ️ informativo)
- **Criterios explícitos**: Basados en severidad, tendencias, y estado del sistema
- **Nivel de confianza**: Porcentaje de confianza (0-100%) en la recomendación
- **Razón detallada**: Explicación clara de por qué es NOTIFY o FYI

#### Verificación con Evidencia
- **Checks automáticos adicionales** para cada comando
- **Evidencia estructurada**: `{source, query, result_summary, pass, timestamp}`
- **Workflow por comando**:
  - `recent-incidents`: health + trends
  - `health`: recent-incidents (24h)
  - `post-deployment`: trends + recent-incidents
  - `trends`: health
  - `daily-digest`: análisis de keywords

#### Deduplicación Automática
- **Fingerprint estable**: hash(intent + params + keywords)
- **TTL de 30 minutos**: Evita notificaciones repetitivas
- **Cache in-memory**: 100 entradas FIFO con limpieza automática
- **Nota automática**: Marca duplicados como FYI con tiempo transcurrido

#### Prompts Canónicos Optimizados
- **Prompts específicos por intención**: Estructura `{system_role, task, evidence_checks, output_format}`
- **Criterios NOTIFY/FYI explícitos** en cada prompt
- **Tareas estructuradas**: Pasos claros de lo que debe hacer el AI

#### API Mejorada
- **Endpoint unificado**: `POST /api/quick/command` para todos los slash commands
- **Respuesta estructurada**: `{report, evidence, recommendation, canonical_command}`
- **Help expandido**: `GET /api/quick/help` con aliases, ejemplos slash, y verificación

### 🎨 UI/UX

#### Frontend (agent-ui)
- **Interceptor de slash commands** en `useAIStreamHandler.tsx`
- **Evidencia colapsable**: Bloque `<details>` con todos los checks
- **Recomendación destacada**: Sección visual con iconos y confianza
- **Formato Markdown profesional**: Con emojis de estado (✅/⚠️/🔔/ℹ️)

#### Guía Visual
- **Nueva documentación**: `docs/SLASH_COMMANDS_VISUAL_GUIDE.md`
- **Captura de pantalla**: Demo de `/novedades hoy` en acción
- **Anatomía completa**: Explicación detallada de cada elemento
- **Flujo de ejecución**: Diagrama paso a paso

### 📚 Documentación

#### Actualizaciones
- ✅ `README.md`: Sección de slash commands con imagen destacada
- ✅ `docs/QUICK_COMMANDS.md`: Guía completa de slash commands
- ✅ `docs/README.md`: Índice actualizado con nueva guía visual
- ✅ `QUICK_COMMANDS_IMPLEMENTATION.md`: Resumen v1.1 con nuevas features
- ✅ `docs/SLASH_COMMANDS_VISUAL_GUIDE.md`: Nueva guía visual completa

#### Nuevos Documentos
- 📸 `docs/slash-commands-demo.png`: Captura de pantalla demo
- 📄 `TESTING_SLASH_COMMANDS.md`: Guía de testing completa
- 📄 `SLASH_COMMANDS_VERIFICATION_SUMMARY.md`: Resumen ejecutivo
- 📄 `CHANGELOG.md`: Este archivo

### 🧪 Testing

#### Nuevos Tests
- ✅ `test_slash_commands_unit.py`: Tests unitarios del parser y funciones
- ✅ `test_slash_commands_integration.py`: Tests de integración del API
- ✅ `test_slash_commands.sh`: Script automatizado de ejecución

#### Cobertura
- Parser de slash commands y aliases
- Construcción de prompts canónicos
- Sistema de deduplicación (fingerprint, TTL)
- Workflow de verificación (estructura y evidencia)
- Endpoints API (`/api/quick/command`, `/api/quick/help`)

### 🐛 Bug Fixes

#### Memory Leak en MarkdownRenderer
- **Archivo**: `agent-ui/src/components/ui/typography/MarkdownRenderer/`
- **Archivos afectados**: `inlineStyles.tsx`, `styles.tsx`
- **Problema**: Object URLs de Blobs no se revocaban correctamente
- **Solución**: Cleanup function siempre registrada para Blob-based URLs
- **Prevención**: Early return eliminado que bloqueaba cleanup registration

#### Puerto Docker en Conflicto
- **Archivo**: `docker-compose.yml`
- **Cambio**: Puerto de grafana-mcp de `8000:8000` a `8001:8000`
- **Razón**: Puerto 8000 ocupado por otro servicio
- **Resultado**: Servicios agentos y grafana-mcp funcionando correctamente

### 🔧 Mejoras Técnicas

#### Backend
- Nuevo módulo `agent/slash_commands.py` (904 líneas)
- Funciones para deduplicación y verificación
- Prompts canónicos estructurados por comando
- Integración con `query_helpers` existentes

#### Frontend
- TypeScript interfaces actualizadas (`slashCommands.ts`)
- Hook de chat mejorado con interceptor
- Render estructurado de evidencia y recomendaciones

#### Docker
- Configuración de puertos actualizada
- Variables de entorno documentadas en `.env.example`
- Servicios corriendo en `localhost:7777` (agentos)

---

## [v1.0.0] - 2025-12-11

### ✨ Quick Commands - Implementación Inicial

#### Comandos Implementados
- ✅ `recent-incidents`: Incidencias recientes con filtros
- ✅ `health`: Health check de servicios en tiempo real
- ✅ `post-deployment`: Monitoreo post-deployment automático
- ✅ `trends`: Análisis de tendencias comparativas
- ✅ `daily-digest`: Resumen diario automático

#### Query Helpers
- Storage layer con funciones SQL optimizadas
- Integración con Prometheus, Loki, Tempo
- Manejo graceful de errores

#### API REST
- 5 endpoints GET (`/api/quick/*`)
- Endpoint de ayuda (`/api/quick/help`)
- Documentación inline completa

#### QueryAgent
- Interpretación de lenguaje natural
- Mapping automático a quick commands
- Instrucciones en castellano

#### Documentación
- Guía completa de Quick Commands
- Ejemplos prácticos por escenario
- Testing automatizado

---

## Formato

Este changelog sigue el formato de [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y el proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

**Tipos de cambios**:
- `✨ Nuevas Características` - para funcionalidades nuevas
- `🔧 Cambios` - para cambios en funcionalidades existentes
- `🗑️ Deprecado` - para funcionalidades que se eliminarán pronto
- `❌ Eliminado` - para funcionalidades eliminadas
- `🐛 Bug Fixes` - para correcciones de bugs
- `🔒 Seguridad` - para vulnerabilidades de seguridad
