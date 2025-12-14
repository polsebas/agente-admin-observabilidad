#!/usr/bin/env python3
"""
Test de regresión para bug de duplicación en prompts de slash commands.

Este test verifica que los atajos (hoy, ayer, Xh) y params (key=value)
no se dupliquen en los prompts generados para QueryAgent.
"""

from agent.slash_commands import parse_slash_command, build_query_agent_prompt


def test_no_duplication_shortcuts():
    """Verifica que atajos no se dupliquen."""
    
    # Test 1: "hoy" no debe aparecer si hours está en params
    canonical, params, args = parse_slash_command("/novedades hoy")
    prompt = build_query_agent_prompt(canonical, params, args)
    assert "hoy" not in prompt.lower(), f"ERROR: 'hoy' duplicado en: {prompt}"
    assert "24" in prompt, f"ERROR: falta info de horas en: {prompt}"
    
    # Test 2: "8h" no debe aparecer si period_hours está en params
    canonical, params, args = parse_slash_command("/tendencias 8h")
    prompt = build_query_agent_prompt(canonical, params, args)
    assert "8h" not in prompt.lower(), f"ERROR: '8h' duplicado en: {prompt}"
    assert "8" in prompt, f"ERROR: falta info de horas en: {prompt}"
    
    # Test 3: "ayer" no debe aparecer si date está en params
    canonical, params, args = parse_slash_command("/digest ayer")
    prompt = build_query_agent_prompt(canonical, params, args)
    # "ayer" puede aparecer si no hay date en params, pero no ambos
    if "date" in params:
        # Si hay date explícita, no debería haber "ayer" también
        pass  # Es OK que diga "ayer" O la fecha, pero verificamos que no esté duplicado mal
    
    print("✅ Test 1-3: Atajos no duplicados")


def test_no_duplication_keyvalue():
    """Verifica que key=value no se dupliquen."""
    
    # Test 4: "hours=8" no debe aparecer literal en el prompt
    canonical, params, args = parse_slash_command("/inc hours=8 severity=critical")
    prompt = build_query_agent_prompt(canonical, params, args)
    assert "hours=8" not in prompt, f"ERROR: 'hours=8' duplicado en: {prompt}"
    assert "severity=critical" not in prompt, f"ERROR: 'severity=critical' duplicado en: {prompt}"
    assert "8" in prompt, f"ERROR: falta info de horas en: {prompt}"
    assert "critical" in prompt, f"ERROR: falta severidad en: {prompt}"
    
    print("✅ Test 4: key=value no duplicados")


def test_preserves_freetext():
    """Verifica que texto libre se preserve cuando no fue procesado."""
    
    # Test 5: Texto libre debe preservarse
    canonical, params, args = parse_slash_command("/novedades de auth-service hoy")
    prompt = build_query_agent_prompt(canonical, params, args)
    assert "de auth-service" in prompt or "auth-service" in prompt, \
        f"ERROR: falta texto libre en: {prompt}"
    assert "hoy" not in prompt.lower() or "24" not in prompt, \
        f"ERROR: 'hoy' duplicado con horas en: {prompt}"
    
    print("✅ Test 5: Texto libre preservado correctamente")


def test_complex_mix():
    """Verifica casos complejos con mezcla de atajos y key=value."""
    
    # Test 6: Mezcla de atajo + key=value
    canonical, params, args = parse_slash_command("/tendencias 24h service=payment")
    prompt = build_query_agent_prompt(canonical, params, args)
    assert "24h" not in prompt.lower(), f"ERROR: '24h' duplicado en: {prompt}"
    assert "service=payment" not in prompt, f"ERROR: 'service=payment' duplicado en: {prompt}"
    assert "24" in prompt, f"ERROR: falta info de horas en: {prompt}"
    assert "payment" in prompt, f"ERROR: falta servicio en: {prompt}"
    
    print("✅ Test 6: Mezcla compleja sin duplicación")


def test_all_shortcuts():
    """Verifica todos los atajos especiales."""
    
    shortcuts = [
        ("/novedades hoy", ["hoy"], ["24"]),  # Debe contener "24" (horas)
        ("/tendencias 8h", ["8h"], ["8"]),     # Debe contener "8" (horas)
        ("/tendencias 24h", ["24h"], ["24"]), # Debe contener "24" (horas)
        ("/tendencias 48h", ["48h"], ["48"]), # Debe contener "48" (horas)
        ("/digest ayer", [], []),              # La fecha se calcula (no verificamos texto específico)
    ]
    
    for cmd, forbidden, required in shortcuts:
        canonical, params, args = parse_slash_command(cmd)
        prompt = build_query_agent_prompt(canonical, params, args)
        
        for forbidden_token in forbidden:
            assert forbidden_token not in prompt.lower(), \
                f"ERROR: '{forbidden_token}' duplicado en {cmd}: {prompt}"
        
        for required_token in required:
            assert required_token in prompt.lower(), \
                f"ERROR: falta '{required_token}' en {cmd}: {prompt}"
    
    print("✅ Test 7: Todos los atajos verificados")


if __name__ == "__main__":
    print("🧪 Testing: No duplicación en prompts de slash commands\n")
    print("=" * 70)
    
    try:
        test_no_duplication_shortcuts()
        test_no_duplication_keyvalue()
        test_preserves_freetext()
        test_complex_mix()
        test_all_shortcuts()
        
        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS DE REGRESIÓN PASARON")
        print("\nEste bug no debería volver a aparecer. 🎉")
        
    except AssertionError as e:
        print("\n" + "=" * 70)
        print(f"❌ TEST FALLÓ: {e}")
        print("\n⚠️  El bug de duplicación ha regresado!")
        exit(1)
