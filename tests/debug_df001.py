"""
Debug DirectFifthsRule - Test df_001 (NUEVOS acordes)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harmonic_rules import DirectFifthsRule, VoiceLeadingUtils

# Test df_001 NUEVOS: B-S directas
chord1 = {
    "S": "E4",
    "A": "G3",
    "T": "C3",
    "B": "C2"
}

chord2 = {
    "S": "D4",
    "A": "B3",
    "T": "G3",
    "B": "G2"
}

print("Test df_001 NUEVOS: Directas B-S")
print("=" * 60)
print(f"Chord1: S={chord1['S']}, B={chord1['B']}")
print(f"Chord2: S={chord2['S']}, B={chord2['B']}")
print()

# D4-G2 debería ser P5
print("Verificando intervalos finales:")
from music21 import interval, note
i = interval.Interval(note.Note("G2"), note.Note("D4"))
print(f"  G2-D4: {i.name} (simple: {i.simpleName})")
print(f"  is_perfect_fifth(G2, D4): {VoiceLeadingUtils.is_perfect_fifth('G2', 'D4')}")
print(f"  is_perfect_fifth(D4, G2): {VoiceLeadingUtils.is_perfect_fifth('D4', 'G2')}")
print()

# Verificar pares
print("Verificando detection logic:")
voice_pairs = [
    ('S', 'A'), ('S', 'T'), ('S', 'B'),
    ('A', 'T'), ('A', 'B'),
    ('T', 'B')
]

for v1, v2 in voice_pairs:
    is_fifth_final = VoiceLeadingUtils.is_perfect_fifth(chord2.get(v1), chord2.get(v2))
    if is_fifth_final:
        print(f"  Par ({v1}, {v2}): llega a P5 ✓")
        
        # Ver movimiento
        motion = VoiceLeadingUtils.get_motion_type(
            chord1[v1], chord2[v1],
            chord1[v2], chord2[v2]
        )
        print(f"    Motion: {motion}")
        
        # Ver salto
        is_leap = VoiceLeadingUtils.is_leap(chord1[v1], chord2[v1], 2)
        print(f"    {v1} salta: {is_leap}")

print()

# Ejecutar regla
rule = DirectFifthsRule()
violation = rule._detect_violation(chord1, chord2)

if violation:
    print(f"✅ ERROR detectado en voces: {violation['voices']}")
else:
    print("❌ NO detectado (esperado ERROR)")
