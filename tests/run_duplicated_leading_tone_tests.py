"""
Test runner para DuplicatedLeadingToneRule
"""

import json
import sys
sys.path.insert(0, '..')

from harmonic_rules import RulesEngine

def run_duplicated_leading_tone_tests():
    """Ejecuta tests de DuplicatedLeadingToneRule"""
    
    with open('test_duplicated_leading_tone.json', 'r') as f:
        test_cases = json.load(f)
    
    print("\n" + "="*70)
    print("DUPLICATED LEADING TONE TESTS - Sensible Duplicada")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"Test {test['id']}: {test['name']}")
        print(f"  Descripción: {test['description']}")
        
        # Crear engine
        engine = RulesEngine(key='C', mode='major')
        
        # Solo duplicated_leading_tone
        for rule in engine.rules:
            if rule.name != 'duplicated_leading_tone':
                engine.disable_rule(rule.name)
        
        # Validar
        errors = engine.validate_progression(test['chord1'], test['chord2'])
        dlt_errors = [e for e in errors if e['rule'] == 'duplicated_leading_tone']
        
        if test['expected'] == 'ERROR':
            if len(dlt_errors) > 0:
                voices_detected = set(dlt_errors[0]['voices'])
                voices_expected = set(test['voices_affected'])
                
                if voices_detected == voices_expected:
                    print(f"  ✅ PASADO - Duplicación detectada en {sorted(list(voices_detected))}")
                    passed += 1
                else:
                    print(f"  ❌ FALLIDO - Voces incorrectas: esperaba {voices_expected}, obtuvo {voices_detected}")
                    failed += 1
            else:
                print(f"  ❌ FALLIDO - Debería detectar sensible duplicada")
                failed += 1
        else:  # expected == 'OK'
            if len(dlt_errors) == 0:
                print(f"  ✅ PASADO - Sin duplicación detectada")
                passed += 1
            else:
                print(f"  ❌ FALLIDO - No debería detectar error: {dlt_errors[0]}")
                failed += 1
        
        print()
    
    print("="*70)
    print(f"RESULTADOS: {passed} pasados, {failed} fallidos de {len(test_cases)} tests")
    print("="*70)
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_duplicated_leading_tone_tests()
