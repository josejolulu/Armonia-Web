"""
================================================================================
TESTS - Chord Knowledge System
================================================================================

Tests para validar ChordDefinitions, Chord, y Progression.

Autor: Aula de Armonía
Fecha: 2025-12-28
================================================================================
"""

import sys
sys.path.insert(0, '..')

from chord_knowledge import Chord, Progression, CHORD_DEFINITIONS
import json


def test_chord_definitions():
    """Verifica que ChordDefinitions contiene todos los tipos básicos."""
    print("\n" + "="*60)
    print("TEST 1: ChordDefinitions")
    print("="*60)
    
    required_types = [
        'major', 'minor', 'diminished',
        'dominant_seventh', 'diminished_seventh',
        'half_diminished', 'major_seventh', 'minor_seventh'
    ]
    
    for chord_type in required_types:
        assert chord_type in CHORD_DEFINITIONS, f"Missing {chord_type}"
        definition = CHORD_DEFINITIONS[chord_type]
        assert 'morphology' in definition
        assert 'figured_bass' in definition
        assert 'category' in definition
        print(f"  ✓ {chord_type}: {definition['name']}")
    
    print(f"\n✅ ChordDefinitions completo: {len(CHORD_DEFINITIONS)} tipos")


def test_chord_major_triad():
    """Test acorde Mayor en estado fundamental."""
    print("\n" + "="*60)
    print("TEST 2: Acorde Mayor (I en Do)")
    print("="*60)
    
    # I en Do Mayor: C-E-G (C3, E3, G4, C5)
    chord = Chord(
        voices={'B': 'C3', 'T': 'E3', 'A': 'G4', 'S': 'C5'},
        root='C',
        quality='major',
        key='C major',
        inversion=0
    )
    
    print(f"\nChord: {chord}")
    print(f"Voices: {chord.voices}")
    print(f"Factors: {chord.voice_factors}")
    
    # Verificar factores
    assert chord.get_factor_for_voice('B') == '1', "Bajo debe ser fundamental"
    assert chord.get_factor_for_voice('T') == '3', "Tenor debe ser tercera"
    assert chord.get_factor_for_voice('A') == '5', "Alto debe ser quinta"
    assert chord.get_factor_for_voice('S') == '1', "Soprano debe ser fundamental"
    
    # Verificar consultas
    assert chord.has_factor('1')
    assert chord.has_factor('3')
    assert chord.has_factor('5')
    assert not chord.has_factor('7'), "No debe tener séptima"
    
    # Verificar completitud
    assert chord.is_complete(), "Debe estar completo (1-3-5)"
    
    # Verificar duplicaciones
    doubled = chord.get_doubled_factors()
    assert '1' in doubled, "Fundamental debe estar duplicada"
    
    # Verificar Missing factors
    missing = chord.get_missing_factors()
    assert len(missing) == 0, "No debe faltar ningún factor"
    
    # Verificar cifrado
    cifrado = chord.get_figured_bass()
    assert cifrado == '5/3', f"Cifrado debe ser 5/3, got {cifrado}"
    
    print("\n✅ Acorde Mayor: Todos los tests pasados")


def test_chord_dominant_seventh():
    """Test acorde V7 en Do Mayor."""
    print("\n" + "="*60)
    print("TEST 3: V7 en Do Mayor (G-B-D-F)")
    print("="*60)
    
    # V7 en Do: G-B-D-F (estado fundamental)
    chord = Chord(
        voices={'B': 'G2', 'T': 'B3', 'A': 'D4', 'S': 'F4'},
        root='G',
        quality='dominant-seventh',
        key='C major',
        inversion=0
    )
    
    print(f"\nChord: {chord}")
    print(f"Factors: {chord.voice_factors}")
    
    # Verificar factores
    assert chord.get_factor_for_voice('B') == '1', "Bajo = fundamental"
    assert chord.get_factor_for_voice('T') == '3', "Tenor = tercera (sensible)"
    assert chord.get_factor_for_voice('A') == '5', "Alto = quinta"
    assert chord.get_factor_for_voice('S') == '7', "Soprano = séptima"
    
    # Verificar séptima
    assert chord.has_seventh, "Debe tener séptima"
    assert chord.has_factor('7')
    
    # Verificar voces con séptima
    voices_with_7th = chord.get_voices_with_factor('7')
    assert voices_with_7th == ['S'], f"Solo Soprano debe tener 7ª, got {voices_with_7th}"
    
    # Verificar sensible (3ª del V)
    voices_with_3rd = chord.get_voices_with_factor('3')
    assert voices_with_3rd == ['T'], "Solo Tenor debe tener sensible (3ª)"
    
    # Verificar información especial
    definition = chord.get_definition()
    assert definition is not None
    assert definition['special']['leading_tone_factor'] == '3'
    assert definition['special']['resolution_factor'] == '7'
    
    # Verificar cifrado
    cifrado = chord.get_figured_bass()
    assert cifrado == '7/+', f"Cifrado debe ser 7/+, got {cifrado}"
    
    print("\n✅ V7: Todos los tests pasados")


def test_chord_v7_first_inversion():
    """Test V7 en 1ª inversión."""
    print("\n" + "="*60)
    print("TEST 4: V7 en 1ª inversión (6/5-)")
    print("="*60)
    
    # V7/6 en Do: sensible en bajo (B-D-F-G)
    chord = Chord(
        voices={'B': 'B2', 'T': 'D3', 'A': 'F4', 'S': 'G4'},
        root='G',
        quality='dominant-seventh',
        key='C major',
        inversion=1
    )
    
    print(f"\nChord: {chord}")
    print(f"Factors: {chord.voice_factors}")
    
    # Verificar bajo es la tercera (sensible)
    assert chord.get_factor_for_voice('B') == '3', "Bajo debe ser tercera (sensible)"
    
    # Verificar cifrado de 1ª inversión
    cifrado = chord.get_figured_bass()
    assert cifrado == '6/5-', f"Cifrado debe ser 6/5-, got {cifrado}"
    
    print("\n✅ V7 Primera Inversión: Tests pasados")


def test_progression_v7_to_i():
    """Test progresión V7 → I."""
    print("\n" + "="*60)
    print("TEST 5: Progresión V7 → I")
    print("="*60)
    
    # V7 en Do
    v7 = Chord(
        voices={'B': 'G2', 'T': 'B3', 'A': 'D4', 'S': 'F4'},
        root='G',
        quality='dominant-seventh',
        key='C major',
        inversion=0
    )
    
    # I en Do
    i = Chord(
        voices={'B': 'C3', 'T': 'C4', 'A': 'E4', 'S': 'C5'},
        root='C',
        quality='major',
        key='C major',
        inversion=0
    )
    
    # Crear progresión
    progression = Progression(v7, i)
    
    print(f"\nProgression: {progression}")
    
    # Verificar movimientos de factores
    movements = progression.get_all_factor_movements()
    print(f"Movements: {movements}")
    
    # Bajo: 1 → 1 (G → C, fundamental → fundamental)
    assert movements['B'] == ('1', '1'), f"Bajo 1→1, got {movements['B']}"
    
    # Tenor: 3 → 1 (B → C, sensible → tónica)
    assert movements['T'] == ('3', '1'), f"Tenor debe hacer 3→1 (sensible→tónica)"
    
    # Alto: 5 → 3 (D → E)
    assert movements['A'] == ('5', '3'), f"Alto 5→3"
    
    # Soprano: 7 → 1 (F → C, séptima → tónica)
    assert movements['S'] == ('7', '1'), f"Soprano debe hacer 7→1"
    
    # Verificar voces con movimiento específico
    voices_7_to_1 = progression.get_voices_with_movement('7', '1')
    assert 'S' in voices_7_to_1, "Soprano debe hacer 7→1"
    
    voices_3_to_1 = progression.get_voices_with_movement('3', '1')
    assert 'T' in voices_3_to_1, "Tenor debe hacer 3→1"
    
    print("\n✅ Progresión V7→I: Movimientos correctos")


def test_incomplete_chord():
    """Test acorde incompleto (sin 5ª)."""
    print("\n" + "="*60)
    print("TEST 6: Acorde V7 sin 5ª")
    print("="*60)
    
    # V7 sin quinta: G-B-F-B (omitir D)
    chord = Chord(
        voices={'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'B4'},
        root='G',
        quality='dominant-seventh',
        key='C major',
        inversion=0
    )
    
    print(f"\nChord: {chord}")
    print(f"Factors: {chord.voice_factors}")
    
    # Verificar factores presentes
    assert chord.has_factor('1')
    assert chord.has_factor('3')
    assert not chord.has_factor('5'), "NO debe tener quinta"
    assert chord.has_factor('7')
    
    # Verificar incompletitud
    assert not chord.is_complete(), "NO debe estar completo (falta 5ª)"
    
    # Verificar factores faltantes
    missing = chord.get_missing_factors()
    assert '5' in missing, f"Debe faltar la 5ª, got {missing}"
    
    # Verificar duplicaciones (3ª duplicada)
    doubled = chord.get_doubled_factors()
    assert '3' in doubled, "Tercera debe estar duplicada"
    
    print(f"Missing factors: {missing}")
    print(f"Doubled factors: {doubled}")
    
    print("\n✅ Acorde incompleto: Detectado correctamente")


def run_all_tests():
    """Ejecuta todos los tests."""
    print("\n" + "="*70)
    print("CHORD KNOWLEDGE TESTS - Suite Completa")
    print("="*70)
    
    try:
        test_chord_definitions()
        test_chord_major_triad()
        test_chord_dominant_seventh()
        test_chord_v7_first_inversion()
        test_progression_v7_to_i()
        test_incomplete_chord()
        
        print("\n" + "="*70)
        print("✅ TODOS LOS TESTS PASADOS")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
