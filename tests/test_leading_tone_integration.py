"""
Test de integración para LeadingToneResolutionRule refactorizada
"""

import sys
sys.path.insert(0, '..')

from harmonic_rules import RulesEngine

def test_leading_tone_resolution():
    """Test sensible tonal que resuelve correctamente."""
    engine = RulesEngine(key='C', mode='major')
    
    # V en Do: G-B-D-G (Tenor tiene sensible B)
    chord1 = {
        'S': 'G4', 'A': 'D4', 'T': 'B3', 'B': 'G2',
        'root': 'G', 'quality': 'major', 'key': 'C major', 'inversion': 0
    }
    
    # I en Do: C-E-G-C (sensible B → C, +1 semitono)
    chord2 = {
        'S': 'C5', 'A': 'E4', 'T': 'C4', 'B': 'C3',
        'root': 'C', 'quality': 'major', 'key': 'C major', 'inversion': 0
    }
    
    errors = engine.validate_progression(chord1, chord2)
    lt_errors = [e for e in errors if e['rule'] == 'leading_tone_resolution']
    
    assert len(lt_errors) == 0, f"Esperaba 0 errores, obtuvo {len(lt_errors)}"
    print("✅ TEST 1: Sensible resuelve correctamente (B → C)")


def test_leading_tone_no_resolution():
    """Test sensible tonal que NO resuelve (error esperado)."""
    engine = RulesEngine(key='C', mode='major')
    
    # V en Do: G-B-D-G
    chord1 = {
        'S': 'G4', 'A': 'D4', 'T': 'B3', 'B': 'G2',
        'root': 'G', 'quality': 'major', 'key': 'C major', 'inversion': 0
    }
    
    # I mal: Sensible B → D (salta, no resuelve)
    chord2_bad = {
        'S': 'E5', 'A': 'C4', 'T': 'D4', 'B': 'C3',
        'root': 'C', 'quality': 'major', 'key': 'C major', 'inversion': 0
    }
    
    errors = engine.validate_progression(chord1, chord2_bad)
    lt_errors = [e for e in errors if e['rule'] == 'leading_tone_resolution']
    
    assert len(lt_errors) > 0, "Debería detectar error"
    assert 'T' in lt_errors[0]['voices'], f"Error debería estar en Tenor, obtuvo {lt_errors[0]['voices']}"
    print(f"✅ TEST 2: Sensible NO resuelve (B → D), error detectado en {lt_errors[0]['voices']}")


if __name__ == "__main__":
    try:
        test_leading_tone_resolution()
        test_leading_tone_no_resolution()
        print("\n✅ TODOS LOS TESTS DE LEADING TONE PASADOS")
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        raise
