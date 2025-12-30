"""
Test runner para validar fix de leading tone en iii7
"""

import json
import sys
sys.path.insert(0, '..')

from harmonic_rules import RulesEngine

def test_leading_tone_iii7_fix():
    """Valida que iii7 NO genera error de sensible"""
    
    with open('test_leading_tone_iii7_fix.json', 'r') as f:
        test_cases = json.load(f)
    
    print("\n" + "="*70)
    print("LEADING TONE iii7 FIX TEST")
    print("="*70 + "\n")
    
    for test in test_cases:
        print(f"Test {test['id']}: {test['name']}")
        print(f"  {test['description']}")
        print(f"  Notas: {test['notes']}\n")
        
        # Crear engine
        engine = RulesEngine(key='C', mode='major')
        
        # Solo leading_tone_resolution
        for rule in engine.rules:
            if rule.name != 'leading_tone_resolution':
                engine.disable_rule(rule.name)
        
        # Validar
        errors = engine.validate_progression(test['chord1'], test['chord2'])
        lt_errors = [e for e in errors if e['rule'] == 'leading_tone_resolution']
        
        if test['expected'] == 'OK':
            if len(lt_errors) == 0:
                print(f"  ✅ PASADO - iii7 NO genera error de sensible (FIX CORRECTO)")
                print(f"  ✅ Validación: Si (B) en iii7 correctamente NO tratado como sensible activa")
                return True
            else:
                print(f"  ❌ FALLIDO - iii7 sigue generando error:")
                print(f"     {lt_errors[0]['full_msg']}")
                return False
    
    return False

if __name__ == "__main__":
    success = test_leading_tone_iii7_fix()
    sys.exit(0 if success else 1)
