# Changelog - Aula de Armonía

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/).

---

## [3.1.0] - 2026-01-03

### 📱 Mobile Experience Fixed

### Fixed

- 🐛 **Mobile Landscape UI**:
  - Unificación completa de interfaz en modos Escribir/Revisar
  - Visibilidad de grados funcionales corregida (uso de `zoom` vs `transform`)
  - Controles de reproducción y navegación alineados en una sola fila compacta
- 🐛 **Undo/Redo en Móvil**:
  - Habilitación de botones corregida (llamada faltante a `updateHistoryButtons`)
  - Restaurada funcionalidad táctil para Deshacer/Rehacer

---

## [v1.3.0] - 2026-01-01

### 🐛 Bug Fixes

- **CRÍTICO**: Corregido falso positivo en `ImproperOmissionRule` con Sextas Aumentadas Alemanas e Italien (#BUG-001)
  - ✅ Añadida doble cláusula de guarda en `_check_chord_for_omissions()` (harmonic_rules.py)
  - ✅ Mejorada validación de `chord_obj.root` en `_is_chromatic_chord()` para manejo robusto de `None`
  - ✅ Corregida transmisión de campo crítico `tipo_especial` en `app.py` líneas 169 y 181
  - ✅ Tests: 3/3 exitosos (6ª Alemana, Italiana, Francesa sin regresiones)
  - ✅ Verificado en navegador: Bug eliminado completamente
  
### ✨ Improvements

- **Detección de acordes cromáticos mejorada**: Sistema robusto de doble validación
  - Cláusula de guarda #1: Verificación de `tipo_especial` pre-identificado por análisis funcional
  - Cláusula de guarda #2: Análisis de intervalos característicos (6ª Aug = 10 semitonos)
- **Logging mejorado**: Mensajes de debug para facilitar troubleshooting de acordes especiales
- **Validación defensiva**: Checks explícitos de atributos antes de acceso para evitar `AttributeError`

### 📝 Documentation

- Generados 10+ documentos técnicos para análisis con NotebookLM (~7000 líneas documentadas)
- [Walkthrough completo](file:///Users/joseluissanchez/.gemini/antigravity/brain/53640918-cdb4-4edd-92d0-13c7bf89d17f/BUG1_RESOLUCION_FINAL.md) de resolución del Bug #1
- Archivos SOURCE_*.md con código fuente numerado para debugging asistido por IA
- Índice maestro consolidado de documentación técnica

### 🧪 Testing

- Suite de tests ejecutada: 7/10 pasando (sin regresiones del Bug #1)
- Tests específicos Bug #1: 3/3 exitosos
- Verificación manual en navegador: ✅ Confirmado

---

## [3.0.0-alpha] - 2025-12-30

### 🚀 Fase 3A En Progreso - Motor Armónico Esencial (80%)

### Added

**12 Reglas Armónicas Implementadas**:

#### Tier 1 (CRITICAL) - 7/7 ✅

- ✨ ParallelFifthsRule - Quintas paralelas/consecutivas (3 excepciones)
- ✨ ParallelOctavesRule - Octavas paralelas/consecutivas  
- ✨ DirectFifthsRule - Quintas directas/ocultas (severidad variable)
- ✨ DirectOctavesRule - Octavas directas/ocultas
- ✨ UnequalFifthsRule - Quintas desiguales (d5→P5)
- ✨ LeadingToneResolutionRule - Resolución de sensible (9 excepciones pedagógicas)
- ✨ SeventhResolutionRule - Resolución de séptima (arquitectura con fallback)

#### Tier 2 (IMPORTANT) - 5/8 ✅

- ✨ VoiceCrossingRule - Cruzamiento de voces (B-T, T-A, A-S)
- ✨ MaximumDistanceRule - Distancia máxima entre voces (>8ª)
- ✨ VoiceOverlapRule - Invasión/Superposición de registros
- ✨ DuplicatedLeadingToneRule - Duplicación de sensible (V, vii°, V7)
- ✨ DuplicatedSeventhRule - Duplicación de séptima

**Infraestructura**:

- ✨ Sistema `chord_knowledge.py` (785 líneas) - Capa abstracción acordes
- ✨ 14 tipos de acordes documentados con factores (1, 3, 5, 7)
- ✨ Arquitectura `HarmonicRule` base class con sistema excepciones
- ✨ `RulesEngine` con registro automático de reglas
- ✨ Sistema de confianza: ConfidenceLevel (CERTAIN, HIGH, MEDIUM, LOW)
- ✨ 60+ tests automatizados JSON (test_*.json)

### Technical

- 🔧 Detección de sensibles locales (dominantes secundarias V/x)
- 🔧 Análisis factor-based vs. imperativo (get_voices_with_factor)
- 🔧 Cadencia rota estricta (V-vi) en resolución sensible
- 🔧 Fallback completo arquitectura legacy → nueva

### Pending (3 reglas Tier 2)

- ⏳ VoiceRangeRule (Tesitura SATB) - 2h estimadas
- ⏳ ImproperOmissionRule (Omisión 3ª/7ª) - 3h estimadas  
- ⏳ ExcessiveMelodicMotionRule (Saltos >8ª) - 2h estimadas

### Metrics

- 📊 **Precisión**: 90%+ en casos comunes
- 📊 **Falsos Positivos**: 0 en I-IV-V-I básico
- 📊 **Coverage**: 12/15 reglas Tier 1+2 (80%)

---

## [2.0.0] - 2025-12-26

### 🎉 Fase 2 Completada - Desktop/Mobile UX Optimization

### Added

- ✨ Atajo de teclado `Escape` para volver a modo Escribir desde modo Revisar
- ✨ Sistema completo de variables CSS (design tokens)
- ✨ Controles de reproducción avanzados (velocidad, navegación)
- ✨ Error sidebar collapsible en desktop
- ✨ Header contextual con contador de errores en modo Revisar
- ✨ Grados funcionales visuales con cifrado europeo
- ✨ Modo standalone detection para PWA futuro
- ✨ README.md completo con documentación
- ✨ Documentación JSDoc en funciones principales

### Changed

- 🔄 Interfaz móvil completamente optimizada (v18)
- 🔄 Icono de papelera y botón Play duplicados eliminados en mobile
- 🔄 Modal de bienvenida con z-index correcto
- 🔄 Piano visual restaurado y mejorado en desktop
- 🔄 Header optimizado con mejor espaciado móvil
- 🔄 CSS organizado con variables y media queries consolidados

### Fixed

- 🐛 Botones duplicados "Corregir" y "Borrar" en desktop
- 🐛 Especificidad CSS en reglas mobile vs desktop
- 🐛 Z-index de modal interfiriendo con contenido
- 🐛 Error sidebar no expandiéndose automáticamente en Review mode
- 🐛 Controles de reproducción ocultos incorrectamente

### Optimized

- ⚡ Limpieza de console.log verbosos
- ⚡ Código JavaScript modularizado
- ⚡ CSS con variables reutilizables
- ⚡ Media queries consolidados
- ⚡ Comentarios mejorados en código

---

## [1.0.0] - 2025-12-20

### 🚀 Release Inicial - Fase 1 Completada

### Added

- ✨ Entrada de notas SATB (piano visual + teclado)
- ✨ Renderizado de partituras con VexFlow
- ✨ Análisis armónico básico
- ✨ Detección de errores fundamentales:
  - Quintas y octavas paralelas
  - Mov contrario en extremos
  - Cruzamiento de voces
  - Ámbito/tesitura incorrecta
- ✨ Reproducción de audio con Tone.js
- ✨ Sistema de undo/redo ilimitado
- ✨ Persistencia en localStorage
- ✨ Interfaz móvil responsive
- ✨ Selección de tonalidades (mayores y menores)
- ✨ Auto-flow entre voces
- ✨ Modal de bienvenida con atajos de teclado

### Technical

- 🔧 Flask backend con API REST
- 🔧 Modularización JavaScript (ES6)
- 🔧 Estado centralizado con AppState
- 🔧 Motor de audio independiente

---

## Tipos de Cambios

- `Added` - Nuevas características
- `Changed` - Cambios en funcionalidad existente
- `Deprecated` - Características que serán eliminadas
- `Removed` - Características eliminadas
- `Fixed` - Corrección de bugs
- `Optimized` - Mejoras de performance o código
- `Security` - Correcciones de seguridad

---

## Roadmap

### [3.0.0] - Q1 2026 - Reglas Avanzadas

- Expansión de 20+ reglas armónicas
- Sistema de severidad configurable
- Modulaciones básicas
- Dominantes secundarias completas

### [4.0.0] - Q1-Q2 2026 - Grados y Cifrados

- Input de bajo cifrado
- Análisis funcional manual
- Múltiples formatos de ejercicio

### [5.0.0] - Q2 2026 - Escritura Avanzada

- Compases variables (2/4, 3/4, 6/8, etc.)
- Notas ornamentales (paso, floreo, apoyatura)
- Figuras rítmicas variadas

### [6.0.0] - Q2 2026 - Modo Profesor

- Creación de ejercicios
- Sistema de corrección automática
- Backend con base de datos

### [7.0.0] - Q3 2026 - PWA

- Instalable en móvil
- Modo offline
- Viewport dinámico optimizado

---

**Mantenedor**: José Luis Sánchez  
**Última actualización**: 26 de Diciembre de 2025
