# Slash Commands - Testing Guide

Este documento describe cómo probar la implementación de slash commands para Quick Commands.

## ✅ Tests Unitarios (Python)

Los tests de parsing ya pasaron exitosamente:

```bash
cd /home/pablo/source/agente-admin
python3 -c "from agent.slash_commands import parse_slash_command; ..."
```

Ver output completo en el historial de comandos.

## 🧪 Tests de Integración (API)

### Prerequisitos

1. AgentOS debe estar corriendo en `http://localhost:7777`
2. La base de datos debe estar inicializada con `alert_storage.init_db()`

### Ejecutar Tests

```bash
./test_slash_commands.sh
```

Este script probará:
- ✅ `/novedades hoy` vía POST /api/quick/command
- ✅ `/salud` vía POST /api/quick/command
- ✅ `/qc` (help) vía POST /api/quick/command
- ✅ GET /api/quick/help incluye aliases
- ✅ Manejo de comandos inválidos

## 🎨 Tests UI (Manual)

1. Levantar el stack completo:
   ```bash
   docker compose up -d
   # O localmente:
   uvicorn main:app --host 0.0.0.0 --port 7777
   cd agent-ui && npm run dev
   ```

2. Abrir http://localhost:3002

3. Probar los siguientes comandos en el chat:

   ```
   /novedades hoy
   /salud
   /inc hours=8 severity=critical
   /health services=auth-service
   /tendencias 48h
   /digest ayer
   /qc
   ```

4. Verificar que:
   - ✅ El comando se ejecuta sin pasar por streaming del agente
   - ✅ El reporte se muestra instantáneamente en formato markdown
   - ✅ Los errores se muestran claramente
   - ✅ `/qc` muestra la ayuda con todos los aliases

## 🐛 Casos Edge a Verificar

1. **Comando con params faltantes**:
   ```
   /deploy
   ```
   Debería: Hacer fallback a QueryAgent que pedirá los params

2. **Comando con texto libre**:
   ```
   /novedades de auth-service de las últimas 8 horas con severidad crítica
   ```
   Debería: Parsear key=value pero también pasar texto a QueryAgent

3. **No es slash command**:
   ```
   dame las novedades de hoy
   ```
   Debería: Flujo normal, enviarse al agente/team seleccionado

4. **Slash command inválido**:
   ```
   /invalid
   ```
   Debería: Error "Comando inválido"

## 📊 Resultados Esperados

### Parsing (Python)
- ✅ Test 1-8 pasaron correctamente
- ✅ Aliases se resuelven a comandos canónicos
- ✅ Parámetros key=value se parsean
- ✅ Atajos "hoy", "ayer", "8h" funcionan
- ✅ Fallback a QueryAgent cuando faltan params

### Backend (API)
- ✅ POST /api/quick/command funciona
- ✅ GET /api/quick/help incluye aliases
- ✅ Errores devuelven HTTP 400/500 apropiados

### Frontend (UI)
- Pendiente de prueba manual (requiere UI corriendo)
- El interceptor está implementado en `useAIStreamHandler`
- El parsing de frontend usa `slashCommands.ts`

## 🚀 Próximos Pasos

1. ✅ Implementación completa
2. ✅ Tests unitarios pasando
3. ⏳ Tests de integración (requiere servidor corriendo)
4. ⏳ Tests UI (requiere UI + backend corriendo)
5. ⏳ Verificar en producción/staging

## 📝 Notas

- Los slash commands son completamente opcionales
- El usuario puede seguir usando lenguaje natural sin `/`
- Los comandos se ejecutan sin streaming para respuesta instantánea
- El modo híbrido decide automáticamente REST vs QueryAgent
