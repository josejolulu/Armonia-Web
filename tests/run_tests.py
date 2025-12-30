"""
Test runner para validar reglas armónicas.

Ejecuta los casos de test definidos en test_cases.json y reporta resultados.
"""

import json
import sys
import os

# Añadir el directorio padre al path para importar harmonic_rules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harmonic_rules import RulesEngine


def run_tests():
    """Ejecuta todos los test cases y reporta resultados"""
    
    # Cargar test cases
    with open('tests/test_cases.json', 'r') as f:
        test_data = json.load(f)
    
    # Inicializar motor
    engine = RulesEngine(key="C", mode="major")
    
    # Estadísticas
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    print("=" * 80)
    print("HARMONIC RULES TEST SUITE - Parallel Fifths")
    print("=" * 80)
    print()
    
    # Ejecutar tests de quintas paralelas
    for test in test_data['test_parallel_fifths']:
        total_tests += 1
        test_id = test['id']
        test_name = test['name']
        expected = test['expected']
        
        chord1 = test['chord1']
        chord2 = test['chord2']
        key = test['key']
        
        # Validar progresión
        context = {'key': key}
        errors = engine.validate_progression(chord1, chord2, context)
        
        # Verificar resultado
        has_errors = len(errors) > 0
        expected_error = (expected == "ERROR")
        
        if has_errors == expected_error:
            # Test pasó
            passed_tests += 1
            status = "✅ PASS"
            
            # Verificar excepciones si aplica
            if 'exception' in test and not has_errors:
                exception_name = test['exception']
                print(f"{status} [{test_id}] {test_name}")
                print(f"         Excepción '{exception_name}' aplicada correctamente")
            elif has_errors:
                # Verificar voces afectadas si están especificadas
                if 'voices_affected' in test:
                    error = errors[0]
                    if set(error['voices']) == set(test['voices_affected']):
                        print(f"{status} [{test_id}] {test_name}")
                        print(f"         Detectado correctamente en voces {error['voices']}")
                    else:
                        print(f"⚠️  WARN [{test_id}] {test_name}")
                        print(f"         Esperado voces {test['voices_affected']}, " 
                              f"detectado {error['voices']}")
                else:
                    print(f"{status} [{test_id}] {test_name}")
                    print(f"         Error detected: {errors[0]['short_msg']}")
            else:
                print(f"{status} [{test_id}] {test_name}")
        else:
            # Test falló
            failed_tests += 1
            status = "❌ FAIL"
            print(f"{status} [{test_id}] {test_name}")
            
            if expected_error and not has_errors:
                print(f"         Esperado: ERROR, Obtenido: OK")
                if 'voices_affected' in test:
                    print(f"         Debería detectar error en voces {test['voices_affected']}")
            elif not expected_error and has_errors:
                print(f"         Esperado: OK, Obtenido: ERROR")
                print(f"         Error detectado: {errors[0]['short_msg']} en {errors[0]['voices']}")
                if 'exception' in test:
                    print(f"         Debería aplicar excepción '{test['exception']}'")
        
        print()
    
    # Resumen final
    print("=" * 80)
    print(f"RESULTADOS: {passed_tests}/{total_tests} tests pasados")
    print("=" * 80)
    print()
    
    if failed_tests > 0:
        print(f"❌ {failed_tests} tests fallaron")
        return 1
    else:
        print("✅ Todos los tests pasaron correctamente")
        return 0


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
