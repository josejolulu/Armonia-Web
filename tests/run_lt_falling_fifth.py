import json
import logging
from harmonic_rules import LeadingToneResolutionRule

logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_tests():
    print("==================================================")
    print(" EJECUTANDO TESTS: CAÍDA DE 5TA (V7/ii -> ii)")
    print("==================================================")
    
    with open('tests/test_lt_falling_fifth.json', 'r') as f:
        test_cases = json.load(f)

    rule = LeadingToneResolutionRule()
    
    for tc in test_cases:
        print(f"\nTest {tc['id']}: {tc['name']}")
        violation = rule._detect_violation(tc['chord1'], tc['chord2'])
        result_status = "ERROR" if violation else "OK"
        print(f"Resultado: {result_status} (Esperado: {tc['expected']})")
        if violation:
            print(f"Detalle: {violation}")

if __name__ == "__main__":
    run_tests()
