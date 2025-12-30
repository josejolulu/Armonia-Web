# Proyecto: Armonía-Web

Sistema de análisis y validación de armonía tonal en 4 voces (SATB)

## Stack Técnico

- **Backend:** Python 3.14 + Flask
- **Frontend:** JavaScript vanilla + VexFlow (notación musical)
- **Librería musical:** music21
- **Tests:** pytest + JSON test cases

## Arquitectura Clave

### Archivos principales

- `harmonic_rules.py`: Motor de validación (12 reglas activas)
- `analizador_tonal.py`: Análisis funcional (grados, inversiones)
- `chord_knowledge.py`: Sistema de conocimiento de acordes
- `app.py`: Backend Flask (endpoints + orquestación)

### Estructura de Reglas

```python
class HarmonicRule:
    - name: Identificador único
    - tier: CRITICAL (1) / IMPORTANT (2) / ADVANCED (3)
    - color: Hex para UI
    - short_msg / full_msg: Mensajes pedagógicos
    
    _detect_violation(chord1, chord2) -> Dict|None
    _calculate_confidence(chord1, chord2, context) -> int (0-100)
```

## Convenciones de Código

### 1. Reglas basadas en factores

- **SIEMPRE** usar `VoiceLeadingUtils.get_chord_factor(note, root)`
- Retorna: '1', '3', '5', '7', '9', '?' (desconocido)
- Evita lógica ad-hoc por tipo de acorde

### 2. Patterns probados

- Check `chord1` primero, luego `chord2` (evitar early return bug)
- Fallback: `root = Pitch(chord.get('B')).name` si no hay `chord.get('root')`
- Confidence: `return 100` (no usar enums inexistentes)

### 3. Tests

- Ubicación: `tests/test_[nombre_regla].json`
- Formato: Array de casos con `should_have_error: true/false`
- Runner: Script Python inline con sys.path.insert(0, '.')

### 4. Tiers y Prioridades

- **Tier 1 (CRITICAL):** Errores graves (paralelas, resoluciones, duplicaciones)
- **Tier 2 (IMPORTANT):** Voces (crossing, overlap, distance)
- **Tier 3 (ADVANCED):** Refinamientos avanzados

## Estado Actual del Proyecto

### Reglas Implementadas (12 total)

**Tier 1:**

1. ParallelFifthsRule
2. ParallelOctavesRule
3. DirectFifthsRule
4. DirectOctavesRule
5. UnequalFifthsRule
6. LeadingToneResolutionRule
7. SeventhResolutionRule
8. VoiceCrossingRule (tier 1 por criticidad)
9. DuplicatedLeadingToneRule ✅ RECIENTE
10. DuplicatedSeventhRule ✅ RECIENTE

**Tier 2:**
11. MaximumDistanceRule
12. VoiceOverlapRule

### Próximas en Roadmap

- ChordCompletenessRule
- TessituraRule

## Decisiones Arquitectónicas Importantes

### Factor-Based Architecture

**Principio:** Las reglas deben usar el conocimiento universal de factores del acorde, no casos específicos.

**Ejemplo:**

```python
# ❌ MAL: Lógica específica
if chord_degree == 'V':
    leading_tone = get_seventh_degree_of_key(key)
    
# ✅ BIEN: Basado en factores
factor = VoiceLeadingUtils.get_chord_factor(note, root)
if factor == '3':  # 3ª mayor de dominante = sensible
```

### Bug Arquitectónico Conocido

**Problema:** Motor valida PARES (chord1 → chord2), último acorde nunca se analiza solo.
**Impact:** Reglas de acorde individual no aplican al último acorde.
**Status:** Documentado, pospuesto (bajo impacto real).

## Metodología Pedagógica

### Fuentes de Referencia

- **Europa:** Conservatorios (España, Francia: Bitsch/Dubois, Alemania: Diether de la Motte)
- **USA:** Piston, Kostka-Payne

### Terminología

- Grados romanos: I, ii, iii, IV, V, vi, vii°
- Dominantes secundarias: V/V, V/ii, etc.
- Inversiones: 0 (fund), 1 (1ª), 2 (2ª), 3 (3ª)

## Debugging Tips

### Logs Clave

- `[APP DEBUG]`: Flujo de datos en app.py (ELIMINAR en producción)
- `logger.info()`: Información normal
- `logger.warning()`: Casos edge

### Reproducción Local

```python
from harmonic_rules import RulesEngine, [NombreRegla]
engine = RulesEngine('C', 'major')
chord1 = {'S': 'B4', 'A': 'D4', 'T': 'B3', 'B': 'G2', 'degree': 'V'}
chord2 = {'S': 'C4', 'A': 'E3', 'T': 'C3', 'B': 'C2'}
errors = engine.validate_progression(chord1, chord2)
```

## Comandos Útiles

```bash
# Ejecutar tests
python3 -m pytest tests/ -v

# Import check
python3 -c "from harmonic_rules import RulesEngine; print('✅ OK')"

# Contar reglas
python3 -c "from harmonic_rules import RulesEngine; e=RulesEngine('C','major'); print(len(e.rules))"

# Servidor desarrollo
python3 app.py
```

## Notas Importantes

1. **Servidor auto-reload:** Flask en modo debug recarga automáticamente
2. **Browser cache:** F5 fuerza recarga
3. **Análisis funcional:** Provee `degree`, `grado_num`, `inversion` (NO provee `root`/`fundamental`)
4. **Fallback crítico:** Siempre verificar que `root` no sea `None` antes de usar

---

**Última actualización:** 2025-12-29  
**Estado:** Producción - Sistema estable con 12 reglas activas
