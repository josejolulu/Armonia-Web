"""
Debug script para analizar intervalos exactos en test cases fallidos
"""

import music21

# Test case pf_004 y pf_005 (son idénticos)
chord1 = {'S': 'G4', 'A': 'E4', 'T': 'C4', 'B': 'C3'}
chord2 = {'S': 'F4', 'A': 'C4', 'T': 'A3', 'B': 'F3'}

voice_pairs = [('S', 'A'), ('S', 'T'), ('S', 'B'), ('A', 'T'), ('A', 'B'), ('T', 'B')]

print("=" * 80)
print("DEBUG: Intervalos Calculados en Test pf_004/pf_005")
print("=" * 80)
print()

for v1, v2 in voice_pairs:
    # Chord 1
    p1_1 = music21.pitch.Pitch(chord1[v1])
    p1_2 = music21.pitch.Pitch(chord1[v2])
    int1 = music21.interval.Interval(p1_1, p1_2)
    
    # Chord 2
    p2_1 = music21.pitch.Pitch(chord2[v1])
    p2_2 = music21.pitch.Pitch(chord2[v2])
    int2 = music21.interval.Interval(p2_1, p2_2)
    
    print(f"Par de voces: {v1}-{v2}")
    print(f"  Chord1: {chord1[v1]} - {chord1[v2]}")
    print(f"    Intervalo: {int1.name} ({int1.semitones} semitonos)")
    print(f"    Dirección: {int1.direction}")
    
    print(f"  Chord2: {chord2[v1]} - {chord2[v2]}")
    print(f"    Intervalo: {int2.name} ({int2.semitones} semitonos)")
    print(f"    Dirección: {int2.direction}")
    
    # Verificar si son quintas
    def is_fifth(semitones):
        normalized = abs(semitones) % 12
        return normalized == 7 or normalized == 8
    
    is_fifth_1 = is_fifth(int1.semitones)
    is_fifth_2 = is_fifth(int2.semitones)
    
    if is_fifth_1 and is_fifth_2:
        print(f"  ⚠️  AMBOS SON QUINTAS → Posible error detectado")
    
    print()

print("=" * 80)
