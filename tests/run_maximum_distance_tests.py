"""
Test runner para MaximumDistanceRule
"""

import json
import sys
sys.path.insert(0, '..')

from harmonic_rules import RulesEngine, MaximumDistanceRule

def run_maximum_distance_tests():
    """Ejecuta tests de MaximumDistanceRule"""
    
    with open('test_maximum_distance.json', 'r') as f:
        test_cases = json.load(f)
    
    print("\n" + "="*70)
    print("MAXIMUM DISTANCE TESTS - Distancia Máxima entre Voces")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"Test {test['id']}: {test['name']}")
        print(f"  Descripción: {test['description']}")
        
        # Crear engine
        engine = RulesEngine(key='C', mode='major')
        
        # Solo activar MaximumDistanceRule
        for rule in engine.rules:
            if rule.name != 'maximum_distance':
                engine.disable_rule(rule.name)
        
        # Validar
        errors = engine.validate_progression(test['chord1'], test['chord2'])
        md_errors = [e for e in errors if e['rule'] == 'maximum_distance']
        
        if test['expected'] == 'ERROR':
            if len(md_errors) > 0:
                voices_detected = md_errors[0]['voices']
                voices_expected = test['voices_affected']
                
                if set(voices_detected) == set(voices_expected):
                    print(f"  ✅ PASADO - Error detectado en {voices_detected}")
                    passed += 1
                else:
                    print(f"  ❌ FALLIDO - Voces incorrectas: esperaba {voices_expected}, obtuvo {voices_detected}")
                    failed += 1
            else:
                print(f"  ❌ FALLIDO - Debería detectar distancia excesiva")
                failed += 1
        else:  # expected == 'OK'
            if len(md_errors) == 0:
                print(f"  ✅ PASADO - Distancias válidas")
                passed += 1
            else:
                print(f"  ❌ FALLIDO - No debería detectar error: {md_errors[0]}")
                failed += 1
        
        print()
    
    print("="*70)
    print(f"RESULTADOS: {passed} pasados, {failed} fallidos de {len(test_cases)} tests")
    print("="*70)
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_maximum_distance_tests()
