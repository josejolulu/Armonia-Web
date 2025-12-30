# 📐 Plan de Implementación Técnica - Armonía Web

> **Status:** NO ACTIVE PLAN  
> **Last Update:** 30 Diciembre 2025, 11:02

---

## Current State

**Sistema estable - 12 reglas activas, 100% tests pasando** ✅

### Verificación Completada (30 Dic 2025)

**Total reglas implementadas**: 12/15 (80% Tier 1+2)

- **Tier 1 (CRITICAL)**: 7/7 (100%) ✅
- **Tier 2 (IMPORTANT)**: 5/8 (62.5%) ✅

### Reglas Tier 1 - Completadas (7/7)

1. ✅ ParallelFifthsRule
2. ✅ ParallelOctavesRule
3. ✅ DirectFifthsRule
4. ✅ DirectOctavesRule
5. ✅ UnequalFifthsRule
6. ✅ LeadingToneResolutionRule
7. ✅ SeventhResolutionRule

### Reglas Tier 2 - Implementadas (5/8)

1. ✅ **VoiceCrossingRule** - Cruzamiento de voces (líneas 1648-1727)
2. ✅ **MaximumDistanceRule** - Distancia excesiva entre voces (líneas 1734-1821)
3. ✅ **VoiceOverlapRule** - Invasión/Superposición (líneas 1828-1918)
4. ✅ **DuplicatedLeadingToneRule** - Duplicación de sensible (líneas 1925-2050)
5. ✅ **DuplicatedSeventhRule** - Duplicación de séptima (líneas 2057-2167)

### Reglas Tier 2 - Pendientes (3/8)

1. ⏳ **ExcessiveMelodicMotionRule** - Saltos melódicos > 8ª
2. ⏳ **TritonResolutionRule** - Resolución del tritono en V7
3. ⏳ **ImproperOmissionRule** - Omisión de factores críticos (3ª, 7ª)

---

## Next Steps

Cuando estés listo para continuar, las próximas implementaciones del roadmap son:

### Prioridad Alta

1. **ExcessiveMelodicMotionRule** - Detectar saltos melódicos mayores a 8ª
   - Estimado: 2 horas
   - Tests: 6+ casos

2. **ImproperOmissionRule** - Verificar que acordes no omitan factores críticos (3ª, 7ª)
   - Estimado: 2-3 horas
   - Usa `chord_knowledge.get_missing_factors()`
   - Tests: 5+ casos

### Prioridad Media

1. **TritonResolutionRule** - Verificar resolución del tritono en V7 (3ª-7ª por movimiento contrario)
   - Estimado: 3-4 horas
   - Requiere helper `get_tritone_notes(chord)`
   - Tests: 5+ casos

---

## Análisis del Problema

*(Cuando se inicie una nueva implementación, documentar aquí el análisis del problema)*

---

## Cambios Propuestos

*(Cuando se inicie una nueva implementación, documentar aquí los archivos a modificar)*

1. **Archivo a modificar:** `harmonic_rules.py`
   - *Detalle del cambio:* ...
2. **Tests a crear:** `tests/test_nueva_regla.json`

---

## Estrategia de Verificación

- **Comando de test:** `pytest tests/` o `/run_tests`
- **Validación manual:** Navegador en `http://localhost:5001`
- **Workflow:** `/validate_rule` (si aplicable)

---

## Pending Issues

- [ ] **Bug arquitectónico:** Último acorde no se analiza solo (documentado, pospuesto)
- [ ] **Campo `root` ausente:** No viene de `analizador_tonal` (usar fallback del bajo)
- [ ] **Excepción P5→d5:** Método `_second_fifth_is_diminished()` en `ParallelFifthsRule` retorna siempre `False` (TODO línea 731-740)

---

**Para nueva implementación:** Actualizar este plan con detalles específicos de la regla a implementar.

**Ver también:**

- [reglas_implementadas.md](file:///Users/joseluissanchez/.gemini/antigravity/brain/53640918-cdb4-4edd-92d0-13c7bf89d17f/reglas_implementadas.md) - Lista detallada de las 12 reglas verificadas
- [roadmap_fase3.md](file:///Users/joseluissanchez/.gemini/antigravity/brain/53640918-cdb4-4edd-92d0-13c7bf89d17f/roadmap_fase3.md) - Hoja de ruta completa de la FASE 3
- [IMPLEMENTATIONS_LOG.md](file:///Users/joseluissanchez/Documents/Proyectos/Armonia-Web%20antigravity/IMPLEMENTATIONS_LOG.md) - Registro histórico de implementaciones
- [ARCHITECTURE.md](file:///Users/joseluissanchez/Documents/Proyectos/Armonia-Web%20antigravity/ARCHITECTURE.md) - Arquitectura del sistema
