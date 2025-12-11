#!/bin/bash

# Script de testing para Quick Commands
# Asegurarse de que el servidor esté corriendo en http://localhost:7777

BASE_URL="http://localhost:7777/api/quick"

echo "==================================="
echo "Testing Quick Commands"
echo "==================================="
echo ""

# Test 1: Recent Incidents
echo "📝 Test 1: Recent Incidents (últimas 24 horas)"
curl -s "${BASE_URL}/recent-incidents?hours=24" | head -50
echo ""
echo "---"
echo ""

# Test 2: Recent Incidents (últimas 8 horas, solo critical)
echo "📝 Test 2: Recent Incidents (últimas 8 horas, critical)"
curl -s "${BASE_URL}/recent-incidents?hours=8&severity=critical" | head -50
echo ""
echo "---"
echo ""

# Test 3: Service Health Summary
echo "📝 Test 3: Service Health Summary (todos los servicios)"
curl -s "${BASE_URL}/health" | head -50
echo ""
echo "---"
echo ""

# Test 4: Service Health (servicios específicos)
echo "📝 Test 4: Service Health (auth-service, payment-service)"
curl -s "${BASE_URL}/health?services=auth-service,payment-service" | head -50
echo ""
echo "---"
echo ""

# Test 5: Post-Deployment Monitoring
DEPLOY_TIME=$(date -u -d '2 hours ago' +%Y-%m-%dT%H:%M:%SZ)
echo "📝 Test 5: Post-Deployment Monitoring (auth-service, 2h atrás)"
echo "Deploy time: $DEPLOY_TIME"
curl -s "${BASE_URL}/post-deployment?service=auth-service&deployment_time=$DEPLOY_TIME" | head -50
echo ""
echo "---"
echo ""

# Test 6: Analyze Trends (alert_count, 24h)
echo "📝 Test 6: Analyze Trends (alert_count, últimas 24h)"
curl -s "${BASE_URL}/trends?metric=alert_count&period_hours=24" | head -50
echo ""
echo "---"
echo ""

# Test 7: Analyze Trends (auth-service, 12h)
echo "📝 Test 7: Analyze Trends (auth-service, últimas 12h)"
curl -s "${BASE_URL}/trends?metric=alert_count&service=auth-service&period_hours=12" | head -50
echo ""
echo "---"
echo ""

# Test 8: Daily Digest (ayer)
echo "📝 Test 8: Daily Digest (ayer)"
curl -s "${BASE_URL}/daily-digest" | head -50
echo ""
echo "---"
echo ""

# Test 9: Daily Digest (fecha específica)
SPECIFIC_DATE=$(date -u -d '3 days ago' +%Y-%m-%d)
echo "📝 Test 9: Daily Digest (fecha específica: $SPECIFIC_DATE)"
curl -s "${BASE_URL}/daily-digest?date=$SPECIFIC_DATE" | head -50
echo ""
echo "---"
echo ""

# Test 10: Help
echo "📝 Test 10: Help (ver comandos disponibles)"
curl -s "${BASE_URL}/help" | python3 -m json.tool
echo ""
echo "---"
echo ""

echo "==================================="
echo "Tests Completados"
echo "==================================="

