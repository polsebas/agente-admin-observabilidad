#!/bin/bash

# Script para ejecutar tests de slash commands
# Incluye tests unitarios e integración

set -e

echo "🧪 Tests de Slash Commands - Verificación y Evidencia"
echo "======================================================="
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que pytest esté instalado
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest no está instalado. Instalando..."
    pip install pytest
fi

echo -e "${BLUE}1. Tests Unitarios (Parser, Aliases, Dedupe)${NC}"
echo "----------------------------------------------"
python -m pytest test_slash_commands_unit.py -v --tb=short
echo ""

echo -e "${BLUE}2. Tests de Integración (Endpoints)${NC}"
echo "------------------------------------"
python -m pytest test_slash_commands_integration.py -v --tb=short
echo ""

echo -e "${GREEN}✅ Tests completados${NC}"
echo ""

# Resumen de cobertura (opcional, si coverage está instalado)
if command -v coverage &> /dev/null; then
    echo -e "${BLUE}3. Cobertura de Código${NC}"
    echo "----------------------"
    coverage run -m pytest test_slash_commands_unit.py test_slash_commands_integration.py
    coverage report --include="agent/slash_commands.py,api/quick_commands_api.py"
    echo ""
fi

echo -e "${YELLOW}💡 Tip: Para tests específicos, usa:${NC}"
echo "   pytest test_slash_commands_unit.py::TestParser::test_parse_novedades_hoy -v"
echo ""

echo -e "${YELLOW}📖 Ver documentación completa en:${NC}"
echo "   docs/QUICK_COMMANDS.md"
echo ""
