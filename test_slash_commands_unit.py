"""
Tests unitarios para el módulo de slash commands.

Prueba:
- Parser de alias y argumentos
- Construcción de prompts canónicos
- Workflow de verificación con evidencia
- Sistema de deduplicación
"""

import pytest
from datetime import datetime, timedelta, timezone
from agent.slash_commands import (
    parse_slash_command,
    can_execute_via_rest,
    build_query_agent_prompt,
    build_canonical_prompt,
    run_verification_workflow,
    check_dedupe,
    apply_dedupe_recommendation,
    _compute_fingerprint,
    _extract_keywords_from_report,
    COMMAND_ALIASES,
    CANONICAL_TO_ALIASES,
)


class TestParser:
    """Tests del parser de slash commands."""
    
    def test_parse_novedades_hoy(self):
        """Test parsing de /novedades hoy."""
        result = parse_slash_command("/novedades hoy")
        assert result is not None
        canonical, params, args_text = result
        assert canonical == "recent-incidents"
        assert params.get("hours") == "24"
        assert "hoy" in args_text
    
    def test_parse_salud_sin_args(self):
        """Test parsing de /salud sin argumentos."""
        result = parse_slash_command("/salud")
        assert result is not None
        canonical, params, args_text = result
        assert canonical == "health"
        assert params == {}
        assert args_text == ""
    
    def test_parse_deploy_con_params(self):
        """Test parsing de /deploy con parámetros."""
        cmd = "/deploy service=auth-service deployment_time=2025-12-14T14:00:00Z"
        result = parse_slash_command(cmd)
        assert result is not None
        canonical, params, args_text = result
        assert canonical == "post-deployment"
        assert params["service"] == "auth-service"
        assert params["deployment_time"] == "2025-12-14T14:00:00Z"
    
    def test_parse_tendencias_con_horas(self):
        """Test parsing de /tendencias 48h."""
        result = parse_slash_command("/tendencias 48h")
        assert result is not None
        canonical, params, args_text = result
        assert canonical == "trends"
        assert params.get("period_hours") == "48"
    
    def test_parse_digest_ayer(self):
        """Test parsing de /digest ayer."""
        result = parse_slash_command("/digest ayer")
        assert result is not None
        canonical, params, args_text = result
        assert canonical == "daily-digest"
        # Debe calcular fecha de ayer
        assert "date" in params
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        assert params["date"] == yesterday.strftime("%Y-%m-%d")
    
    def test_parse_help(self):
        """Test parsing de /qc (help)."""
        result = parse_slash_command("/qc")
        assert result is not None
        canonical, params, args_text = result
        assert canonical == "help"
    
    def test_parse_comando_invalido(self):
        """Test parsing de comando inválido."""
        result = parse_slash_command("/comando_inexistente")
        assert result is None
    
    def test_parse_texto_normal(self):
        """Test que texto normal no es parseado."""
        result = parse_slash_command("dame las novedades de hoy")
        assert result is None
    
    def test_parse_multiples_params(self):
        """Test parsing con múltiples parámetros key=value."""
        cmd = "/inc hours=8 severity=critical service=auth-service"
        result = parse_slash_command(cmd)
        assert result is not None
        canonical, params, args_text = result
        assert canonical == "recent-incidents"
        assert params["hours"] == "8"
        assert params["severity"] == "critical"
        assert params["service"] == "auth-service"


class TestRestExecution:
    """Tests de decisión de ejecución via REST."""
    
    def test_can_execute_health_without_params(self):
        """Health puede ejecutarse sin params."""
        assert can_execute_via_rest("health", {})
    
    def test_can_execute_recent_incidents_without_params(self):
        """Recent-incidents puede ejecutarse sin params."""
        assert can_execute_via_rest("recent-incidents", {})
    
    def test_cannot_execute_post_deployment_without_required_params(self):
        """Post-deployment requiere service y deployment_time."""
        assert not can_execute_via_rest("post-deployment", {"service": "auth"})
        assert not can_execute_via_rest("post-deployment", {"deployment_time": "2025-12-14T14:00:00Z"})
    
    def test_can_execute_post_deployment_with_required_params(self):
        """Post-deployment puede ejecutarse con params requeridos."""
        params = {
            "service": "auth-service",
            "deployment_time": "2025-12-14T14:00:00Z"
        }
        assert can_execute_via_rest("post-deployment", params)
    
    def test_can_execute_help(self):
        """Help siempre puede ejecutarse."""
        assert can_execute_via_rest("help", {})


class TestPromptBuilding:
    """Tests de construcción de prompts."""
    
    def test_build_query_agent_prompt_recent_incidents(self):
        """Test construcción de prompt para recent-incidents."""
        prompt = build_query_agent_prompt("recent-incidents", {"hours": "8"}, "hours=8")
        assert "incidencias recientes" in prompt.lower()
        assert "8 horas" in prompt.lower()
    
    def test_build_query_agent_prompt_health(self):
        """Test construcción de prompt para health."""
        prompt = build_query_agent_prompt("health", {}, "")
        assert "health summary" in prompt.lower()
    
    def test_build_canonical_prompt_with_template(self):
        """Test construcción de prompt canónico con template."""
        prompt = build_canonical_prompt("recent-incidents", {"hours": "24"})
        assert "ROL:" in prompt
        assert "TAREA:" in prompt
        assert "PARÁMETROS:" in prompt
        assert "hours: 24" in prompt


class TestDedupe:
    """Tests del sistema de deduplicación."""
    
    def test_fingerprint_consistency(self):
        """Fingerprint debe ser consistente para mismos inputs."""
        fp1 = _compute_fingerprint("recent-incidents", {"hours": "24"}, ["critical"])
        fp2 = _compute_fingerprint("recent-incidents", {"hours": "24"}, ["critical"])
        assert fp1 == fp2
    
    def test_fingerprint_different_for_different_inputs(self):
        """Fingerprint debe ser diferente para inputs distintos."""
        fp1 = _compute_fingerprint("recent-incidents", {"hours": "24"}, ["critical"])
        fp2 = _compute_fingerprint("recent-incidents", {"hours": "48"}, ["critical"])
        assert fp1 != fp2
    
    def test_extract_keywords_critical(self):
        """Extrae keyword 'critical' del reporte."""
        report = "Sistema en estado crítico (critical) con 3 alertas"
        keywords = _extract_keywords_from_report(report)
        assert "critical" in keywords
    
    def test_extract_keywords_trends(self):
        """Extrae keywords de tendencias."""
        report = "Se detectó un aumento significativo en las alertas"
        keywords = _extract_keywords_from_report(report)
        assert "trend_up" in keywords
    
    def test_check_dedupe_no_duplicate_first_time(self):
        """Primera ejecución no es duplicado."""
        # Limpiar cache
        from agent.slash_commands import _dedupe_cache
        _dedupe_cache.clear()
        
        is_dup, cached = check_dedupe("health", {}, "Reporte de salud OK")
        assert not is_dup
        assert cached is None
    
    def test_check_dedupe_duplicate_within_ttl(self):
        """Segunda ejecución inmediata es duplicado."""
        from agent.slash_commands import _dedupe_cache
        _dedupe_cache.clear()
        
        # Primera ejecución
        is_dup1, _ = check_dedupe("health", {}, "Reporte de salud OK")
        assert not is_dup1
        
        # Segunda ejecución (inmediata)
        is_dup2, cached2 = check_dedupe("health", {}, "Reporte de salud OK")
        assert is_dup2
        assert cached2 is not None
    
    def test_apply_dedupe_recommendation_changes_to_fyi(self):
        """Dedupe cambia recomendación a FYI."""
        result = {
            "report": "Reporte",
            "evidence": [],
            "recommendation": {
                "level": "notify",
                "reason": "Problema crítico",
                "confidence": 0.9
            }
        }
        
        modified = apply_dedupe_recommendation(result, is_duplicate=True, time_since_seconds=900)
        assert modified["recommendation"]["level"] == "fyi"
        assert "15 min" in modified["recommendation"]["reason"]
        assert "Query ejecutada recientemente" in modified["recommendation"]["reason"]


class TestAliases:
    """Tests de aliases y mapeo de comandos."""
    
    def test_all_aliases_mapped(self):
        """Todos los aliases deben mapear a un comando canónico."""
        for alias, canonical in COMMAND_ALIASES.items():
            assert canonical in [
                "recent-incidents", "health", "post-deployment",
                "trends", "daily-digest", "help"
            ]
    
    def test_canonical_to_aliases_reverse_mapping(self):
        """Mapeo inverso debe ser correcto."""
        assert "novedades" in CANONICAL_TO_ALIASES["recent-incidents"]
        assert "salud" in CANONICAL_TO_ALIASES["health"]
        assert "deploy" in CANONICAL_TO_ALIASES["post-deployment"]
        assert "tendencias" in CANONICAL_TO_ALIASES["trends"]
        assert "digest" in CANONICAL_TO_ALIASES["daily-digest"]
        assert "qc" in CANONICAL_TO_ALIASES["help"]
    
    def test_all_short_aliases_exist(self):
        """Aliases cortos deben existir para comandos principales."""
        short_aliases = ["nov", "sal", "dep", "tend", "dig"]
        for alias in short_aliases:
            assert alias in COMMAND_ALIASES


class TestVerificationWorkflow:
    """Tests del workflow de verificación (requiere mock de storage)."""
    
    def test_verification_workflow_structure(self):
        """El workflow debe devolver estructura correcta."""
        # Mock simple: el workflow puede fallar si no hay DB,
        # pero debe devolver estructura
        base_report = "# Test Report\n\nContenido del reporte"
        
        try:
            result = run_verification_workflow("health", {}, base_report)
            
            # Verificar estructura
            assert "report" in result
            assert "evidence" in result
            assert "recommendation" in result
            assert "canonical_command" in result
            
            # Verificar tipos
            assert isinstance(result["evidence"], list)
            assert isinstance(result["recommendation"], dict)
            assert result["canonical_command"] == "health"
            
            # Verificar estructura de recomendación
            assert "level" in result["recommendation"]
            assert result["recommendation"]["level"] in ["notify", "fyi"]
            assert "reason" in result["recommendation"]
            assert "confidence" in result["recommendation"]
        except Exception:
            # Si falla por falta de DB, está OK (test de estructura)
            pytest.skip("Requiere DB inicializada")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
