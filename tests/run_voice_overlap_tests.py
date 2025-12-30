"""
Test runner para VoiceOverlapRule
"""

import json
import sys
sys.path.insert(0, '..')

from harmonic_rules import RulesEngine, VoiceOverlapRule

def run_voice_overlap_tests():
    """Ejecuta tests de VoiceOverlapRule"""
    
    with open('test_voice_overlap.json', 'r') as f:
        test_cases = json.load(f)
    
    print("\n" + "="*70)
    print("VOICE OVERLAP TESTS - Invasión de Voces")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"Test {test['id']}: {test['name']}")
        print(f"  Descripción: {test['description']}")
        
        # Crear engine
        engine = RulesEngine(key='C', mode='major')
        
        # Solo activar VoiceOverlapRule
        for rule in engine.rules:
            if rule.name != 'voice_overlap':
                engine.disable_rule(rule.name)
        
        # Validar
        errors = engine.validate_progression(test['chord1'], test['chord2'])
        vo_errors = [e for e in errors if e['rule'] == 'voice_overlap']
        
        if test['expected'] == 'ERROR':
            if len(vo_errors) > 0:
                voices_detected = vo_errors[0]['voices']
                voices_expected = test['voices_affected']
                
                if set(voices_detected) == set(voices_expected):
                    print(f"  ✅ PASADO - Invasión detectada en {voices_detected}")
                    passed += 1
                else:
                    print(f"  ❌ FALLIDO - Voces incorrectas: esperaba {voices_expected}, obtuvo {voices_detected}")
                    failed += 1
            else:
                print(f"  ❌ FALLIDO - Debería detectar invasión")
                failed += 1
        else:  # expected == 'OK'
            if len(vo_errors) == 0:
                print(f"  ✅ PASADO - Sin invasiones")
                passed += 1
            else:
                print(f"  ❌ FALLIDO - No debería detectar error: {vo_errors[0]}")
                failed += 1
        
        print()
    
    print("="*70)
    print(f"RESULTADOS: {passed} pasados, {failed} fallidos de {len(test_cases)} tests")
    print("="*70)
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_voice_overlap_tests()
