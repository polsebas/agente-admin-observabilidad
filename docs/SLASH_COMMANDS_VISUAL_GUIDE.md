# 📸 Guía Visual de Slash Commands

## Interfaz de AgentUI

![Slash Commands Demo](slash-commands-demo.png)

## 🎯 Anatomía de un Slash Command

La imagen muestra un ejemplo completo de la ejecución de `/novedades hoy`:

### 1️⃣ **Input del Usuario**
```
/novedades hoy
```
- Comando: `/novedades` (alias de `recent-incidents`)
- Parámetro: `hoy` (últimas 24 horas)

### 2️⃣ **Respuesta Principal**
```
Incidencias recientes (últimas 24 horas)
Período: 2025-12-13 18:53 UTC - 2025-12-14 18:53 UTC

✅ No se registraron incidencias en este período.
```

### 3️⃣ **Evidencia de Verificación**
El sistema ejecuta **checks automáticos** para validar la situación:

#### Check 1: health_check ✅
- **Query**: `get_active_alerts()`
- **Resultado**: 0 alertas activas (0 critical, 0 major)
- **Timestamp**: 2025-12-14T18:53:32.052692+00:00

#### Check 2: trends_check ✅
- **Query**: `compare_periods(hours=24)`
- **Resultado**: Período actual: 0, anterior: 0, cambio: +0.0%
- **Timestamp**: 2025-12-14T18:53:32.053071+00:00

### 4️⃣ **Recomendación Inteligente**
```
ℹ️ FYI (Informativo)

Razón: Análisis completado sin situaciones críticas.

Confianza: 50%
```

**Interpretación**:
- **FYI** = Solo informativo, no requiere acción
- **Confianza 50%** = Nivel estándar cuando no hay problemas detectados

### 5️⃣ **Evidencia Expandible**
La evidencia se muestra en un bloque colapsable:
```markdown
▼ 📋 Evidencia de Verificación (click para expandir)
```

Al expandir, se muestran todos los checks ejecutados con sus detalles completos.

---

## ✨ Características Destacadas en la Captura

### 🔍 **Verificación Automática**
- No solo ejecuta el comando, sino que **valida** con checks adicionales
- **health_check**: Confirma estado actual del sistema
- **trends_check**: Compara con períodos anteriores

### 🎯 **Recomendaciones Inteligentes**
- Clasifica la situación como **NOTIFY** (accionable) o **FYI** (informativo)
- Incluye **razón** clara y **nivel de confianza**

### 📊 **Evidencia Transparente**
- Muestra **qué checks** se ejecutaron
- Indica si **pasaron o fallaron** (✅ / ⚠️)
- Incluye **timestamps** para auditoría

### 🔄 **Interfaz Limpia**
- Sidebar con configuración de agentes
- Área de chat principal con formato Markdown
- Evidencia colapsable para no saturar la vista

---

## 🚀 Otros Ejemplos de Uso

### Comando con Parámetros Específicos
```bash
/inc hours=8 severity=critical
```

### Comando de Salud
```bash
/salud
```
Ejecuta `health_check` con contexto de incidencias recientes.

### Post-Deployment
```bash
/deploy service=auth-service deployment_time=2025-12-14T14:00:00Z
```
Analiza anomalías post-deployment con comparación pre/post.

### Ayuda
```bash
/qc
```
Muestra ayuda completa con todos los aliases disponibles.

---

## 📋 Flujo de Ejecución

```
Usuario escribe: /novedades hoy
           ↓
   Parser de Slash Commands
           ↓
   Resolución de Alias: recent-incidents
           ↓
   Parseo de Parámetros: hours=24
           ↓
   QueryAgent: Ejecuta comando base
           ↓
   Verification Workflow
   ├─ health_check
   └─ trends_check
           ↓
   Análisis de Recomendación
   ├─ Nivel: notify / fyi
   ├─ Razón
   └─ Confianza
           ↓
   Deduplicación (TTL 30 min)
           ↓
   Render en UI con formato Markdown
```

---

## 🎨 Elementos de UI

### Sidebar Izquierdo
- **+ NEW CHAT**: Iniciar conversación nueva
- **AGENTOS**: Lista de endpoints disponibles
- **AUTH TOKEN**: Configuración de autenticación
- **MODE**: Selector de modo (TEAM / Individual agents)
- **GPT-5-MINI**: Modelo configurado
- **SESSIONS**: Historial de chats

### Panel Principal
- **Input de usuario**: Barra superior para comandos
- **Respuesta del agente**: Formato Markdown con secciones
- **Evidencia colapsable**: Details/Summary HTML
- **Recomendación destacada**: Con iconos y formato visual

---

## 💡 Tips de UX

1. **Formato claro**: Uso de emojis (✅, ⚠️, 🔔, ℹ️) para identificación rápida
2. **Colapsable**: La evidencia no satura la vista principal
3. **Timestamps**: Auditoría completa de cada check
4. **Confianza explícita**: El usuario sabe qué tan confiable es la recomendación
5. **Markdown**: Formato profesional y legible

---

Ver [documentación completa de Quick Commands](QUICK_COMMANDS.md) para más detalles.
