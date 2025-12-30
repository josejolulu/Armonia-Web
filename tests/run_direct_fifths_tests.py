"""
Test runner para DirectFifthsRule
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harmonic_rules import DirectFifthsRule

def run_direct_fifths_tests():
    """Ejecuta los tests de DirectFifthsRule"""
    
    # Cargar tests
    with open('tests/test_direct_fifths.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tests = data['tests']
    rule = DirectFifthsRule()
    
    print("=" * 80)
    print(f"TEST SUITE: {data['test_suite']}")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for test in tests:
        test_id = test['id']
        test_name = test['name']
        expected = test['expected']
        chord1 = test['chord1']
        chord2 = test['chord2']
        
        # Ejecutar regla
        violation = rule._detect_violation(chord1, chord2)
        
        # Determinar resultado
        if expected == "ERROR":
            if violation:
                # Verificar voces afectadas
                expected_voices = set(test.get('voices_affected', []))
                actual_voices = set(violation['voices'])
                
                if expected_voices == actual_voices:
                    print(f"✅ PASS [{test_id}] {test_name}")
                    print(f"         Detectado correctamente en voces {violation['voices']}")
                    passed += 1
                else:
                    print(f"❌ FAIL [{test_id}] {test_name}")
                    print(f"         Voces esperadas: {expected_voices}")
                    print(f"         Voces detectadas: {actual_voices}")
                    failed += 1
            else:
                print(f"❌ FAIL [{test_id}] {test_name}")
                print(f"         Esperado: ERROR, Obtenido: OK")
                failed += 1
        
        elif expected == "OK" or expected == "OK_FOR_DF":
            if violation:
                print(f"❌ FAIL [{test_id}] {test_name}")
                print(f"         Esperado: OK, Obtenido: ERROR en {violation['voices']}")
                failed += 1
            else:
                print(f"✅ PASS [{test_id}] {test_name}")
                if test.get('notes'):
                    print(f"         {test['notes']}")
                passed += 1
        
        print()
    
    print("=" * 80)
    print(f"RESULTADOS: {passed}/{len(tests)} tests pasados")
    print("=" * 80)
    print()
    
    if failed == 0:
        print("✅ Todos los tests pasaron correctamente")
        return 0
    else:
        print(f"❌ {failed} tests fallaron")
        return 1

if __name__ == "__main__":
    exit(run_direct_fifths_tests())
