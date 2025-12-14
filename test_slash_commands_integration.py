"""
Tests de integraci?n para el endpoint POST /api/quick/command.

Prueba el flujo completo:
- Parseo de slash commands
- Ejecuci?n de verificaci?n
- Respuesta con evidencia y recomendaci?n
- Deduplicaci?n
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta


# Importar la app de FastAPI
SKIP_REASON = ""
try:
    from main import app
    client = TestClient(app)
    SKIP_INTEGRATION = False
except Exception as e:
    SKIP_INTEGRATION = True
    SKIP_REASON = f"No se pudo importar la app: {e}"


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestQuickCommandEndpoint:
    """Tests de integraci?n del endpoint /api/quick/command."""
    
    def test_help_command(self):
        """Test comando de ayuda."""
        response = client.post(
            "/api/quick/command",
            json={"command": "/qc"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "Quick Commands - Ayuda" in data["report"]
        assert "recent-incidents" in data["report"]
        assert "health" in data["report"]
    
    def test_novedades_hoy(self):
        """Test /novedades hoy."""
        response = client.post(
            "/api/quick/command",
            json={"command": "/novedades hoy"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura
        assert "report" in data
        assert "evidence" in data
        assert "recommendation" in data
        assert "canonical_command" in data
        
        # Verificar canonical command
        assert data["canonical_command"] == "recent-incidents"
        
        # Verificar recomendaci?n
        rec = data["recommendation"]
        assert "level" in rec
        assert rec["level"] in ["notify", "fyi"]
        assert "reason" in rec
        assert "confidence" in rec
        
        # Verificar evidencia
        assert isinstance(data["evidence"], list)
    
    def test_salud_sin_args(self):
        """Test /salud sin argumentos."""
        response = client.post(
            "/api/quick/command",
            json={"command": "/salud"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "report" in data
        assert data["canonical_command"] == "health"
        assert "evidence" in data
        assert "recommendation" in data
    
    def test_comando_invalido(self):
        """Test comando inv?lido retorna 400."""
        response = client.post(
            "/api/quick/command",
            json={"command": "/comando_invalido"}
        )
        assert response.status_code == 400
        assert "detail" in response.json()
    
    def test_texto_sin_slash_invalido(self):
        """Test texto sin slash es inv?lido."""
        response = client.post(
            "/api/quick/command",
            json={"command": "dame las novedades"}
        )
        assert response.status_code == 400
    
    def test_dedupe_ejecutar_dos_veces(self):
        """Test deduplicaci?n al ejecutar comando dos veces."""
        command = "/tendencias period_hours=24"
        
        # Primera ejecuci?n
        response1 = client.post(
            "/api/quick/command",
            json={"command": command}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Segunda ejecuci?n inmediata
        response2 = client.post(
            "/api/quick/command",
            json={"command": command}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # La segunda debe ser FYI (dedupe)
        # Nota: esto puede ser flaky si el reporte cambia entre ejecuciones
        # pero en un entorno de test controlado deber?a funcionar
        assert data2["recommendation"]["level"] == "fyi"
        assert "recientemente" in data2["recommendation"]["reason"].lower()


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestQuickHelpEndpoint:
    """Tests del endpoint GET /api/quick/help."""
    
    def test_help_endpoint(self):
        """Test endpoint de ayuda."""
        response = client.get("/api/quick/help")
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura
        assert "quick_commands" in data
        assert "features" in data
        assert "recommendation_criteria" in data
        
        # Verificar comandos
        commands = data["quick_commands"]
        assert "recent-incidents" in commands
        assert "health" in commands
        assert "post-deployment" in commands
        assert "trends" in commands
        assert "daily-digest" in commands
        
        # Verificar que cada comando tiene aliases
        for cmd_name, cmd_info in commands.items():
            assert "aliases" in cmd_info
            assert isinstance(cmd_info["aliases"], list)
            assert "verification_checks" in cmd_info or cmd_name == "daily-digest"


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestQuickCommandRESTEndpoints:
    """Tests de endpoints REST individuales."""
    
    def test_recent_incidents_endpoint(self):
        """Test GET /api/quick/recent-incidents."""
        response = client.get("/api/quick/recent-incidents?hours=24")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
    
    def test_health_endpoint(self):
        """Test GET /api/quick/health."""
        response = client.get("/api/quick/health")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
    
    def test_trends_endpoint(self):
        """Test GET /api/quick/trends."""
        response = client.get("/api/quick/trends?metric=alert_count&period_hours=24")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
    
    def test_daily_digest_endpoint(self):
        """Test GET /api/quick/daily-digest."""
        response = client.get("/api/quick/daily-digest")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
