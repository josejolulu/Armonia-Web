# Changelog - Aula de Armonía

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/).

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
