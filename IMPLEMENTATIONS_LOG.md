# Registro Histórico de Implementaciones - Armonía Web

> **Propósito:** Registro cronológico de TODAS---

## [2025-12-28] Chord Abstraction Layer - Sistema de Conocimiento de Acordes ✅

**Objetivo:** Crear capa de abstracción centralizada para conocimiento de acordes (vertical/horizontal) y eliminar duplicación de código en reglas armónicas.

### **Fase 1: ChordDefinitions + Chord Class**

**Archivos creados:**

- `chord_knowledge.py` (785 líneas)
- `tests/test_chord_knowledge.py` (293 líneas)

**Componentes implementados:**

1. **ChordDefinitions (líneas 59-461):**
   - Diccionario estático con 14 tipos de acordes
   - 8 diatónicos: major, minor, diminished, dominant_seventh, diminished_seventh, half_diminished, major_seventh, minor_seventh
   - 6 cromáticos: secondary_dominant, secondary_leading_tone_dim, secondary_leading_tone_half_dim, neapolitan_sixth, italian/french/german_augmented_sixth
   - Cada tipo incluye: morphology, figured_bass, factors_in_inversion, syntax, special, category
   - Tipos cromáticos marcados con `detection.method='external'` → detectados en `analizador_tonal.py`

2. **Chord class (líneas 470-605):**
   - Representa acorde SATB con análisis automático
   - `__post_init__`: analiza factores (1,3,5,7) de cada voz usando `VoiceLeadingUtils.get_chord_factor()`
   - Métodos verticales: `get_factor_for_voice()`, `get_voices_with_factor()`, `has_factor()`, `is_complete()`, `get_doubled_factors()`, `get_missing_factors()`
   - Métodos de referencia: `get_definition()`, `get_figured_bass()`

3. **Progression class (líneas 610-650):**
   - Analiza movimientos horizontales de factores
   - Métodos: `get_factor_movement()`, `get_voices_with_movement()`, `get_all_factor_movements()`

**Fix crítico aplicado:**

- `harmonic_rules.py` líneas 594-647: `VoiceLeadingUtils.get_chord_factor()`
- Cambio: De `iv.simpleName` a pitch class arithmetic `(p_note.pitchClass - p_root.pitchClass) % 12`
- Razón: Método anterior fallaba con intervalos descendentes (ej: C4→E3)
- Ahora funciona en cualquier octava y dirección

**Tests:** 6/6 pasando

- ChordDefinitions completo
- Acorde Mayor (factores, completitud)
- V7 (sensible=3ª, séptima)
- V7 primera inversión (bajo=3ª)
- Progresión V7→I (movimientos de factores)
- Acorde incompleto (factores faltantes detectados)

**Documentación:**

- `chord_knowledge_analysis.md` - Análisis de gaps arquitectónicos
- `chord_table_analysis.md` - Análisis de PDF "Tabla de acordes e inversiones"
- `harmonic_vocabulary_complete.md` - Taxonomía completa del vocabulario armónico
- `chord_abstraction_phase1_walkthrough.md` - Walkthrough de Fase 1

---

### **Fase 2: Integración con Reglas Existentes**

**Archivos modificados:**

- `harmonic_rules.py` (líneas 648-706, 1547-1630, 1401-1519)
- `tests/test_leading_tone_integration.py` (NUEVO - 74 líneas)

**Cambios implementados:**

1. **Helper de conversión (líneas 648-706):**

   ```python
   def _dict_to_chord_safe(chord_dict: Dict) -> Optional[Chord]:
       """Convierte Dict SATB → Chord con fallback seguro."""
   ```

   - Retorna `None` si falta `root` o no hay voces
   - Permite fallback a método legacy si conversión falla

2. **SeventhResolutionRule refactorizada (líneas 1547-1630):**
   - Estructura de 3 métodos:
     - `_detect_violation()`: Dispatcher con fallback
     - `_detect_violation_chord()`: Método nuevo usando `Chord`
     - `_detect_violation_legacy()`: Código original SIN CAMBIOS
   - Simplificación clave:

     ```python
     # ANTES (10 líneas loop manual)
     for voice, note1 in chord1.items():
         if voice not in ['S','A','T','B']: continue
         factor = VoiceLeadingUtils.get_chord_factor(note1, root1)
         if factor != '7': continue
     
     # DESPUÉS (1 línea)
     voices_with_7th = chord1_obj.get_voices_with_factor('7')
     ```

   - Reducción: -9 líneas en lógica principal

3. **LeadingToneResolutionRule refactorizada (líneas 1401-1519):**
   - Solo modifica detección sensible local (líneas 1442-1449):

     ```python
     # ANTES: Cálculo manual M3 (9 líneas)
     p_root = music21.pitch.Pitch(root1)
     p_note = music21.pitch.Pitch(note1)
     diff = (p_note.pitchClass - p_root.pitchClass) % 12
     if diff == 4:  # M3 = 4 semitonos
     
     # DESPUÉS (3 líneas)
     factor = chord1_obj.get_factor_for_voice(voice_name)
     if factor == '3':  # Es la 3ª
     ```

   - Mantiene sensible tonal INTACTA
   - Mantiene 9 excepciones pedagógicas INTACTAS
   - Estructura: 3 métodos con fallback completo

**Tests:** 10/10 pasando (100%)

- Chord Knowledge Suite: 6/6
- SeventhResolution: 2/2 (resolución correcta + error detectado)
- LeadingToneResolution: 2/2 (sensible resuelve + error detectado)

**Beneficios logrados:**

- Código declarativo vs. imperativo
- -19 líneas netas en lógica principal
- Cero regresiones (fallback completo)
- Patrón establecido para nuevas reglas

**Documentación:**

- `phase2_integration_plan.md` - Plan detallado con análisis de riesgos
- `phase2_seventh_rule_walkthrough.md` - Walkthrough SeventhResolutionRule
- `phase2_complete_walkthrough.md` - Walkthrough completo Fase 2

---

### **Fase 3: Expansión de Vocabulario Armónico**

**Archivos modificados:**

- `chord_knowledge.py` - Expandido de 532 a 785 líneas

**Approach:** Documentación-only (detection='external')

- NO reimplementar detectores existentes
- SÍ documentar tipos cromáticos en ChordDefinitions
- Detectores en `analizador_tonal.py` preservados intactos

**Tipos cromáticos añadidos a ChordDefinitions:**

1. **Dominantes Secundarias (3 tipos):**
   - `secondary_dominant`: V/x (triada o V7)
   - `secondary_leading_tone_dim`: vii°/x o vii°7/x
   - `secondary_leading_tone_half_dim`: viiø7/x
   - Detector externo: `DetectorFunciones.detectar_dominante_secundaria()`

2. **Napolitana (1 tipo):**
   - `neapolitan_sixth`: N6 (♭II6)
   - Detector externo: `DetectorAcordesEspeciales.detectar_napolitana()`

3. **Sextas Aumentadas (3 tipos):**
   - `italian_augmented_sixth`: +6it (♭6-1-#4)
   - `french_augmented_sixth`: +6fr (♭6-1-2-#4)
   - `german_augmented_sixth`: +6al (♭6-1-♭3-#4)
   - Detector externo: `DetectorAcordesEspeciales.detectar_sexta_aumentada()`

**Comentarios explicativos añadidos (líneas 25-49):**

```python
# =============================================================================
# NOTAS SOBRE DETECCIÓN DE ACORDES CROMÁTICOS
# =============================================================================
# Separación intencional:
# - ChordDefinitions: Conocimiento teórico
# - analizador_tonal.py: Detección práctica
# Futuro: Crear adapter Dict SATB → music21.chord.Chord si se necesita
```

**Tests de regresión:** 10/10 pasando

- Chord Knowledge Suite: 6/6 ✓
- Reglas refactorizadas: 4/4 ✓
- analizador_tonal.py: Import OK (no roto) ✓

**Documentación:**

- `phase3_expansion_plan.md` - Análisis arquitectónico y opciones evaluadas
- `phase3_complete_walkthrough.md` - Walkthrough completo Fase 3

---

### **Resumen del Proyecto Completo**

**Métricas finales:**

- Archivos creados: 2 (chord_knowledge.py, test_chord_knowledge.py)
- Archivos modificados: 2 (harmonic_rules.py, test_leading_tone_integration.py)
- Líneas código nuevo: ~900
- Tipos de acordes: 14 (8 diatónicos + 6 cromáticos documentados)
- Reglas refactorizadas: 2 (SeventhResolution, LeadingToneResolution)
- Tests totales: 10/10 pasando (100%)
- Artifacts generados: 10 documentos de análisis/plan/walkthrough

**Impacto arquitectónico:**

- ✅ Conocimiento centralizado de acordes
- ✅ Eliminación de código duplicado en reglas
- ✅ Base para detección avanzada (dominantes secundarias)
- ✅ Código declarativo y mantenible
- ✅ Zero regresiones (fallback completo)
- ✅ Patrón establecido para futuras reglas

**Estado:** ✅ COMPLETADO - Listo para usar en nuevas reglas

---

## Próximas Implementaciones Planificadas para evitar duplicaciones y regresiones  
>
> **Formato:** Cada entrada documenta QUÉ se implement, DÓNDE está el código, y POR QUÉ se hizo así.

---

## 📅 2025-12-28: Fix Crítico - Inyección de Context['key']

**Archivo:** `harmonic_rules.py` (líneas 276-283)  
**Clase:** `HarmonicRule.validate()`  
**Problema:** El frontend envía `key` en `context`, NO en `chord1/chord2`. Las reglas que dependen de tonalidad (como `LeadingToneResolutionRule`) fallaban en producción.

**Solución Implementada:**

```python
# Antes de validar, inyectar key de context en chords
if 'key' in context:
    if 'key' not in chord1:
        chord1 = {**chord1, 'key': context['key']}
    if 'key' not in chord2:
        chord2 = {**chord2, 'key': context['key']}
```

**Impact:** CRÍTICO - Sin este código, Regla #6 y futuras reglas dependientes de tonalidad NO funcionan.

**Tests:** `tests/test_repro_real.json` - Caso de reproducción real del error en navegador.

---

## 📅 2025-12-28: Fix Crítico - Manejo de Grados Desconocidos ('?')

**Archivo:** `harmonic_rules.py` (líneas 1400-1403)  
**Regla:** `LeadingToneResolutionRule._detect_violation()`  
**Problema:** Cuando `chord2` no tiene `'root'`, `get_degree_from_chord()` retorna `'?'`. La lógica de excepciones permitía incorrectamente el error cuando grado = `'?'`.

**Solución Implementada:**

```python
if chord2_degree == '?':
    # Asumimos que podría ser tónica (strict interpretation)
    # NO permitir excepción
    pass
else:
    # Lógica de excepciones normal
    ...
```

**Razón:** Cuando no sabemos el grado, es más seguro asumir que PODRÍA ser tónica y exigir resolución estricta.

**Tests:** Verificado en producción con V7+ -> I.

---

## 📅 2025-12-27: Regla #7 - Resolución de Séptima de Dominante

**Archivo:** `harmonic_rules.py` (líneas 1437-1503)  
**Clase:** `SeventhResolutionRule`  
**Implementa:** La séptima de un acorde (especialmente dominante) debe resolver descendiendo por grado conjunto.

**Lógica de Detección:**

1. Identificar séptima usando `get_chord_factor(note, root)` → `'7'`
2. Verificar movimiento: debe ser `-1` o `-2` semitonos (descenso por grado)
3. Excepción: Cambio de disposición del mismo acorde (permitido)

**Excepciones:**

- **Cambio de disposición:** Permitido (línea 1466)
- Resolución diferida: TODO - no implementada en Fase 1

**Color:** `#FF0000` (Rojo - Error grave)  
**Tests:** `tests/test_seventh_resolution.json` - 5 casos  
**Helper añadido:** `VoiceLeadingUtils.get_chord_factor()` (líneas 595-619)

---

## 📅 2025-12-27: Regla #6 - Resolución de Sensible (Leading Tone)

**Archivo:** `harmonic_rules.py` (líneas 1284-1431)  
**Clase:** `LeadingToneResolutionRule`  
**Implementa:** La sensible en función dominante (V, VII) debe resolver a tónica.

**Detección en 2 niveles:**

### **1. Sensible Tonal (Grado 7):**

```python
info = VoiceLeadingUtils.get_scale_degree_info(note1, key)
if info['is_leading_tone']:  # Grado 7 de la escala
    is_sensible_candidate = True
```

### **2. Sensible Local (Dominantes Secundarias):**

```python
# Criterios:
# - Movimiento raíz: P4 o P5 (V->I local)
# - note1 es M3 de root1 (3ª mayor = sensible)

if interval_roots.simpleName in ['P4', 'P5']:  
    diff = (p_note.pitchClass - p_root.pitchClass) % 12
    if diff == 4:  # M3 = 4 semitonos
        is_sensible_candidate = True
        is_local_sensible = True
```

**Excepciones Pedagógicas:**

1. **Voz interior** (A/T) puede bajar 3ª a 5ª del acorde final (líneas 1417-1423)
2. **V-VII pair:** Misma función, permitido (línea 1414)
3. **Filtro iii (III):** Sensible es 5ª del acorde, no resuelve (líneas 1371-1374)
4. **Cadencia rota estricta:** V-vi OBLIGA resolución (líneas 1407-1408)
5. **Acorde destino sin función tónica:** Permite NO resolución si dest ≠ I/i/vi y NO es sensible local (líneas 1410-1411)

**Color:** `#CD853F` (Peru - Marrón claro)  
**Tests:** `tests/test_leading_tone.json` - 5 casos base + tests secundarias

**Limitación conocida:** Sensibles locales requieren campo `'root'` en chords. Si falta, detección falla.

---

## 📅 2025-12-26: Regla #5 - Quintas Desiguales (d5→P5)

**Archivo:** `harmonic_rules.py` (líneas 1149-1277)  
**Clase:** `UnequalFifthsRule`  
**Implementa:** Prohibir paso de quinta disminuida a quinta justa cuando el bajo está involucrado.

**Lógica:**

1. Solo verifica pares que incluyen Bajo: `('B', 'S')`, `('B', 'A')`, `('B', 'T')`
2. Intervalo inicial debe ser `d5` (línea 1204)
3. Intervalo final debe ser `P5` (línea 1209)
4. Excepción: 10as paralelas B-S (líneas 1214, 1226-1265)

**Excepción 10as paralelas:**

- Si B-S forman 10ª mayor/menor en AMBOS acordes
- Y se mueven en movimiento paralelo
- Entonces permitir d5→P5 en otras voces

**Color:** `#FFA500` (Naranja)  
**Severity:** HIGH (90%)  
**Tests:** Integrado en suite de quintas

---

## 📅 2025-12-25: Regla #4 - Octavas Directas (Ocultas)

**Archivo:** `harmonic_rules.py` (líneas 1005-1142)  
**Clase:** `DirectOctavesRule`  
**Implementa:** Detecta octavas directas (llegar a P8 por movimiento directo).

**Lógica (similar a quintas directas):**

1. Intervalo final = P8 o P1
2. Intervalo inicial ≠ P8/P1 (si no, son paralelas)
3. Movimiento = `'parallel'` (directo)
4. NO cumple excepciones

**Excepciones:**

- **B-S (MÁS ESTRICTA):** Soprano +1 semitono Y Bajo +5 semitonos (4ª justa)
  - Ejemplo: Sensible→Tónica en soprano, dominante→tónica en bajo (V-I)
  - Líneas 1093-1106
- **Otras voces:** Una hace 2ª, NO ambas (líneas 1108-1112)

**Severidad:**

- B-S: CERTAIN (100%)
- Con Bajo: HIGH (90%)
- Sin Bajo (T/A-S): MEDIUM-HIGH (80%)
- Voces internas: MEDIUM (70%)

**Color:** `#FFFF00` (Amarillo)

---

## 📅 2025-12-25: Regla #3 - Quintas Directas (Ocultas)

**Archivo:** `harmonic_rules.py` (líneas 853-998)  
**Clase:** `DirectFifthsRule`  
**Implementa:** Detecta quintas directas (llegar a P5 por movimiento directo con voz superior saltando).

**Lógica de Detección:**

1. Intervalo final = P5 (quinta justa)
2. Intervalo inicial ≠ P5 (si no, son paralelas)
3. Si intervalo inicial es d5, prioridad a `UnequalFifthsRule` (evita duplicación)
4. Movimiento = `'parallel'` (directo)
5. Verificar excepciones

**Excepciones:**

- **Partes extremas (B-S):** Soprano hace 2ª Y Bajo hace 3ª, 4ª o 5ª (3-7 semitonos) → Permitido (líneas 946-957)
- **Partes intermedias:** UNA voz hace grado conjunto (pero NO ambas) → Permitido (líneas 960-963)

**Severidad:**

- B-S: CERTAIN (100%) - más audible
- Con Bajo: HIGH (90%)
- T/A con S: MEDIUM-HIGH (80%)
- Voces internas: MEDIUM (70%)

**Color:** `#FFFF00` (Amarillo - menos grave que paralelas)

---

## 📅 2025-12-24: Regla #2 - Octavas Paralelas/Consecutivas

**Archivo:** `harmonic_rules.py` (líneas 758-846)  
**Clase:** `ParallelOctavesRule`  
**Implementa:** Detecta octavas paralelas y consecutivas.

**Lógica:** Idéntica a `ParallelFifthsRule` pero con `is_octave()`:

1. Verificar si ambos intervalos son P8 o P1 (líneas 811-812)
2. Verificar si movimiento es `'parallel'` o `'contrary'`
3. Si sí, reportar error

**Excepciones:** Ninguna implementada por ahora (más estricto que quintas).

**Color:** `#FF0000` (Rojo)  
**Severity:** CERTAIN (100%)  
**TODO:** Consultar si existen excepciones pedagógicas.

---

## 📅 2025-12-23: Regla #1 - Quintas Paralelas/Consecutivas

**Archivo:** `harmonic_rules.py` (líneas 626-751)  
**Clase:** `ParallelFifthsRule`  
**Implementa:** Detecta quintas paralelas y contrarias (movimiento contrario).

**Mejora Clave:** Usa `interval.simpleName` de music21 (NO solo semitonos) para evitar falsos positivos:

```python
is_fifth_1 = VoiceLeadingUtils.is_fifth(note1_v1, note1_v2)  # P5 o A5
is_fifth_2 = VoiceLeadingUtils.is_fifth(note2_v1, note2_v2)
```

**Excepciones Implementadas:**

1. **Par V-VII:** Misma función dominante (líneas 657-661)
2. **Cambio de disposición:** Mismo acorde, diferente voicing (líneas 664-668)
3. **Segunda quinta disminuida:** P5→d5 permitido (líneas 671-675, TODO implementar lógica)

**Mensajes Diferenciados:**

- Movimiento `'parallel'` → "Quintas paralelas"
- Movimiento `'contrary'` → "Quintas consecutivas"
- Lógica en `HarmonicRule.validate()` líneas 306-316

**Color:** `#FF0000` (Rojo)  
**Severity:** CERTAIN (100%)

---

## 📅 2025-12-20: Utilidades de Conducción de Voces

**Archivo:** `harmonic_rules.py` (líneas 359-619)  
**Clase:** `VoiceLeadingUtils` (estática)  
**Implementa:** 11 métodos helper para análisis de voces.

### **Métodos de Intervalos:**

- `get_interval_object(note1, note2)` → `music21.interval.Interval`
- `get_interval(note1, note2)` → Semitonos (con signo)
- `is_perfect_fifth(note1, note2)` → bool (usa simpleName)
- `is_augmented_fifth(note1, note2)` → bool
- `is_diminished_fifth(note1, note2)` → bool
- `is_fifth(note1, note2)` → bool (P5 o A5)
- `is_octave(note1, note2)` → bool (P8 o P1)

### **Métodos de Movimiento:**

- `is_leap(note1, note2, threshold=2)` → bool (salto > threshold semitonos)
- `get_motion_type(v1_n1, v1_n2, v2_n1, v2_n2)` → `'parallel'/'contrary'/'oblique'/'static'`

### **Métodos de Análisis Tonal:**

- `get_scale_degree_info(note, key)` → `{'degree': int, 'semitones_from_tonic': int, 'is_leading_tone': bool}`
- `get_degree_from_chord(chord, key)` → `'I'/'ii'/'iii'/'IV'/'V'/'vi'/'vii°'` o `'?'`
- `get_chord_factor(note, root)` → `'1'/'3'/'5'/'7'` o `'?'`

**Decisión de Diseño:** Todos los métodos son `@staticmethod` para usarse sin instanciar.

---

## 📅 2025-12-20: Analizador de Contexto

**Archivo:** `harmonic_rules.py` (líneas 56-177)  
**Clase:** `ContextAnalyzer` (estática)  
**Implementa:** Detecta excepciones contextuales.

### **Métodos Implementados:**

**1. `is_voicing_change(chord1, chord2)`** (líneas 68-109)

- Detecta si dos acordes son el mismo con diferente disposición
- Criterios: Mismo root, quality, inversión; diferente distribución de voces

**2. `is_V_VII_pair(chord1, chord2, key)`** (líneas 112-145)

- Detecta pares V-VII o VII-V
- Verifica: `degree_num` en `{5, 7}` y `function == 'D'` en ambos

**3. `detect_modulation(context)`** (líneas 148-160)

- TODO: No implementado en Fase 1
- Retorna `None` siempre

**4. `is_in_pattern(context)`** (líneas 163-177)

- TODO: Detección de progresiones secuenciales
- Retorna `False` siempre

---

## 📅 2025-12-18: Clase Base Harmonic Rule

**Archivo:** `harmonic_rules.py` (líneas 184-352)  
**Clase:** `HarmonicRule` (abstracta)  
**Implementa:** Infraestructura base para todas las reglas.

### **Métodos Públicos:**

**1. `__init__(name, tier, color, short_msg, full_msg)`** (líneas 203-227)

- Inicializa metadatos de la regla
- `self.exceptions = []` → Lista de excepciones
- `self.enabled = True` → Estado de habilitación

**2. `add_exception(name, check, description)`** (líneas 229-247)

- Añade excepción con función `check(chord1, chord2, context) -> bool`
- Si check retorna `True`, la excepción aplica (NO es error)

**3. `validate(chord1, chord2, context)`** (líneas 249-328)

- **Orquestador principal:**
  1. Verifica si regla está habilitada
  2. Inyecta `context['key']` en chords (FIX CRÍTICO líneas 276-283)
  3. Llama `_detect_violation()`
  4. Verifica TODAS las excepciones
  5. Calcula confianza
  6. Retorna error formateado o `None`

**Mensaje diferenciado:** Líneas 306-316 cambian "paralelas" por "consecutivas" si `motion_type == 'contrary'`.

### **Métodos Abstractos:**

**1. `_detect_violation(chord1, chord2)`** (líneas 330-340)

- DEBE ser implementado por cada regla específica
- Retorna: `None` o `{'chord_index': int, 'voices': List[str]}`

**2. `_calculate_confidence(chord1, chord2, context)`** (líneas 342-352)

- Por defecto retorna `CERTAIN` (100%)
- Puede sobrescribirse para ajustar según contexto

---

## 📅 2025-12-18: Motor de Reglas (RulesEngine)

**Archivo:** `harmonic_rules.py` (líneas 1510-1709)  
**Clase:** `RulesEngine`  
**Implementa:** Coordinador de todas las reglas.

### **Métodos Clave:**

**1. `__init__(key, mode)`** (líneas 1526-1541)

- Inicializa motor con tonalidad
- Registra reglas Tier 1 por defecto vía `_register_default_rules()`

**2. `_register_default_rules()`** (líneas 1543-1564)

- Registra automáticamente las 7 reglas Tier 1:
  1. ParallelFifthsRule
  2. ParallelOctavesRule
  3. DirectFifthsRule
  4. DirectOctavesRule
  5. UnequalFifthsRule
  6. LeadingToneResolutionRule
  7. SeventhResolutionRule

**3. `validate_progression(chord1, chord2, context)`** (líneas 1576-1609)

- Añade `key` al context si no está (línea 1596)
- Ejecuta TODAS las reglas habilitadas
- Retorna lista de errores encontrados

**4. `format_errors_for_app(errors, compas, tiempo_index)`** (líneas 1646-1709)

- Formatea errores para app.py:
  - Ordena voces de grave a agudo (B → T → A → S) usando `voice_order` (líneas 1683-1688)
  - Construye mensaje legible: `"Compás 1, T2: Quintas paralelas (Bajo-Tenor)"`
  - Añade metadata: confidence, color, rule name

**5. `enable_rule(name)` / `disable_rule(name)`** (líneas 1611-1627)

- Habilitar/deshabilitar reglas específicas

**6. `get_active_rules(tier=None)`** (líneas 1629-1644)

- Filtrar reglas activas por tier

---

## 📅 2025-12-18: Enumeraciones y Configuración

**Archivo:** `harmonic_rules.py` (líneas 37-49)

### **1. ConfidenceLevel** (Enum)

```python
CERTAIN = 100    # Regla clara, sin ambigüedad
HIGH = 80        # Muy probable error
MEDIUM = 60      # Dudoso
LOW = 40         # Caso edge, sugerencia
```

### **2. RuleTier** (Enum)

```python
CRITICAL = 1      # Tier 1: Errores graves (paralelas, resoluciones)
IMPORTANT = 2     # Tier 2: Errores notables (saltos, unísono)
ADVANCED = 3      # Tier 3: Refinamientos (modulaciones, acordes especiales)
```

**Uso:** Todas las reglas actuales son `RuleTier.CRITICAL`.

---

## 🛠️ Helpers y Funciones de Soporte

### **`VoiceLeadingUtils.get_scale_degree_info(note, key)`** (líneas 557-579)

**Lógica interna:**

```python
# Mapa de semitonos → grados
degree_map = {
    0:1,  # Tónica
    1:2, 2:2,  # Supertónica (alterada o no)
    3:3, 4:3,  # Mediante
    5:4, 6:4,  # Subdominante
    7:5,  # Dominante
    8:6, 9:6,  # Submediante
    10:7, 11:7  # Sensible/Subtónica
}

is_leading = (semitones == 11)  # 11 semitonos de tónica = sensible
```

**Propósito:** Usado por `LeadingToneResolutionRule` para detectar sensibles tonales.

---

### **`VoiceLeadingUtils.get_degree_from_chord(chord, key)`** (líneas 582-592)

**Lógica interna:**

```python
if not chord.get('root'): return '?'  # Sin root, no puede determinar
deg = get_scale_degree_info(chord['root'] + '4', key)['degree']

# Mapas de grados romanos según modo
major = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
minor = ['i', 'ii°', 'III', 'iv', 'V', 'VI', 'vii°']

return lst[deg-1] if 1 <= deg <= 7 else '?'
```

**Limitación conocida:** Si `chord['root']` está ausente, retorna `'?'`.

---

### **`VoiceLeadingUtils.get_chord_factor(note, root)`** (líneas 595-619)

**Propósito:** Identificar si una nota es fundamental (1), tercera (3), quinta (5) o séptima (7) del acorde.

**Lógica:**

```python
iv = get_interval_object(root, note)
simple = iv.simpleName  # ej: 'P1', 'M3', 'P5', 'm7'

if simple == 'P1': return '1'
if simple in ['M3', 'm3', 'd3']: return '3'
if simple in ['P5', 'd5', 'A5']: return '5'
if simple in ['m7', 'M7', 'd7']: return '7'
return '?'
```

**Uso:** `SeventhResolutionRule` lo usa para identificar qué voz tiene la séptima.

---

## 🚧 Limitaciones y TODOs Conocidos

### **1. Campo `'root'` Ausente en Producción**

**Afecta:**

- `LeadingToneResolutionRule` → Sensibles locales no se detectan
- `get_degree_from_chord()` → Retorna `'?'`
- `ContextAnalyzer.is_voicing_change()` → Retorna `False`

**Solución pendiente:** Investigar dónde se debe calcular el `root`:

- ¿Frontend?
- ¿`analizador_tonal.py`?
- ¿`app.py` antes de llamar al motor?

### **2. Excepción de Descenso Cromático (V/V → V7)**

**Status:** NO implementada

**Descripción:** La sensible de un dominante secundario puede bajar cromáticamente si resuelve en la versión 7ª del acorde destino.

**Ejemplo:** A7 (V/V) → G7 (V7)

- Sensible local: C# (3ª de A7)
- Puede bajar a C♮ (7ª de G7)

**Implementación futura:** Añadir en `LeadingToneResolutionRule` después de línea 1423.

### **3. Excepciones pendientes en ParallelFifthsRule**

**Línea 731-740:** Método `_second_fifth_is_diminished()` retorna siempre `False`.

**TODO:** Implementar lógica real para detectar P5→d5 (actualmente solo está registrado como excepción).

### **4. Detección de Modulación y Patrones**

**`ContextAnalyzer.detect_modulation()`** (línea 159): Retorna `None`  
**`ContextAnalyzer.is_in_pattern()`** (línea 177): Retorna `False`

**TODO:** Implementar en Fase 3 (Tier 3 - Advanced).

---

## 🧪 Test Coverage

| Regla | Test File | Casos | Status |
|-------|-----------|-------|--------|
| Quintas Paralelas | `test_parallel_fifths.json` | 8+ | ✅ Completo |
| Octavas Paralelas | Integrado en suite | 5+ | ✅ Completo |
| Quintas Directas | `test_direct_fifths.json` | 6+ | ✅ Completo |
| Octavas Directas | `test_direct_octaves.json` | 6+ | ✅ Completo |
| Quintas Desiguales | Integrado | 4+ | ✅ Completo |
| **Sensible** | `test_leading_tone.json` | **5** | ✅ Base |
| **Sensible** | `test_repro_real.json` | **1** | ✅ Repro |
| **Sensible Secundaria** | `test_lt_sec_tests.json` | **3** | ⚠️ Parcial (requiere `root`) |
| Séptima | `test_seventh_resolution.json` | 5 | ✅ Completo |

---

**Fin del documento IMPLEMENTATIONS_LOG.md**
