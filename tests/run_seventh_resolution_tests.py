import json
import logging
from harmonic_rules import SeventhResolutionRule

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def run_tests():
    print("==================================================")
    print("EJECUTANDO TESTS: Resolución de Séptima")
    print("==================================================")
    
    try:
        with open('tests/test_seventh_resolution.json', 'r') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("ERROR: No se encontró tests/test_seventh_resolution.json")
        return

    rule = SeventhResolutionRule()
    passed = 0
    total = len(test_cases)
    
    for tc in test_cases:
        print(f"\nTest {tc['id']}: {tc['name']}")
        print(f"Desc: {tc.get('description', '')}")
        
        violation = rule._detect_violation(tc['chord1'], tc['chord2'])
        
        expected = tc['expected']
        result_status = "ERROR" if violation else "OK"
        
        if result_status == expected:
            print("✅ PASS")
            passed += 1
        else:
            print(f"❌ FAIL (Esperado: {expected}, Obtenido: {result_status})")
            if violation:
                print(f"   Detalle: {violation}")

    print("\n==================================================")
    print(f"RESULTADO FINAL: {passed}/{total} tests pasaron")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
