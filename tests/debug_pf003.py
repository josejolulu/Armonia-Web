"""
Debug específico para test pf_003: Quintas contrarias S-B
"""

import music21

# Test case pf_003
chord1 = {'S': 'G5', 'A': 'E5', 'T': 'C5', 'B': 'C3'}
chord2 = {'S': 'F5', 'A': 'D5', 'T': 'A4', 'B': 'D3'}

print("=" * 80)
print("DEBUG: Test pf_003 - Quintas contrarias S-B")
print("=" * 80)
print()

# Analizar intervalo S-B
print("Par de voces: S-B")
print(f"  Chord1: {chord1['S']} - {chord1['B']}")

p1_s = music21.pitch.Pitch(chord1['S'])
p1_b = music21.pitch.Pitch(chord1['B'])
int1 = music21.interval.Interval(p1_s, p1_b)

print(f"    Intervalo: {int1.name} ({int1.semitones} semitonos)")
print(f"    Simple name: {int1.simpleName}")
print(f"    Direction: {int1.direction}")
print()

print(f"  Chord2: {chord2['S']} - {chord2['B']}")

p2_s = music21.pitch.Pitch(chord2['S'])
p2_b = music21.pitch.Pitch(chord2['B'])
int2 = music21.interval.Interval(p2_s, p2_b)

print(f"    Intervalo: {int2.name} ({int2.semitones} semitonos)")
print(f"    Simple name: {int2.simpleName}")
print(f"    Direction: {int2.direction}")
print()

# Verificar si son quintas
print("Verificación:")
print(f"  ¿Chord1 S-B es quinta? simpleName={int1.simpleName} → {int1.simpleName in ['P5', 'A5']}")
print(f"  ¿Chord2 S-B es quinta? simpleName={int2.simpleName} → {int2.simpleName in ['P5', 'A5']}")
print()

# Tipo de movimiento
dir_s = p2_s.ps - p1_s.ps
dir_b = p2_b.ps - p1_b.ps

print(f"Movimiento:")
print(f"  S: {chord1['S']} → {chord2['S']} (diferencia: {dir_s})")
print(f"  B: {chord1['B']} → {chord2['B']} (diferencia: {dir_b})")

if dir_s == 0 and dir_b == 0:
    motion = 'static'
elif dir_s == 0 or dir_b == 0:
    motion = 'oblique'
elif (dir_s > 0 and dir_b > 0) or (dir_s < 0 and dir_b < 0):
    motion = 'parallel'
else:
    motion = 'contrary'

print(f"  Tipo de movimiento: {motion}")
print()

print("=" * 80)
