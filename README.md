# 🎹 Aula de Armonía

Aplicación web interactiva para el aprendizaje y práctica de armonía tonal

Versión: 3.0 (Phase 3A - Complete)  
Última actualización: 30 Diciembre 2025

---

## 📖 Descripción

Aula de Armonía es una herramienta educativa que permite a estudiantes de música escribir acordes de 4 voces (SATB) y recibir análisis automático de reglas de armonía tonal. La aplicación proporciona feedback inmediato sobre errores armónicos, visualización de grados funcionales y reproducción audio de las progresiones.

### Características Principales

✅ **Entrada de Notas**

- Piano visual interactivo (desktop)
- Teclado alfanumérico (A-G)
- Botones táctiles (mobile)
- Soporte para alteraciones (♯, ♭, ♮)

✅ **Análisis Armónico**

- Detección de errores fundamentales
- Grados funcionales romanos
- Cifrado barroco europeo
- Identificación de dominantes secundarias
- Acordes especiales (Napolitana, sextas aumentadas)

✅ **Interfaz Adaptativa**

- Desktop optimizado (piano + panel errores)
- Mobile optimizado (botones táctiles)
- Modo dual: Escribir / Revisar
- Dark mode compatible

✅ **Reproducción Audio**

- Motor de síntesis con Tone.js
- Controles avanzados (play, pause, stop)
- Selector de velocidad (50%, 75%, 100%)
- Control de volumen

✅ **Productividad**

- Undo/Redo ilimitado
- Persistencia automática (localStorage)
- Atajos de teclado extensivos
- Auto-flow entre voces

---

## 🚀 Inicio Rápido

### Requisitos

- Python 3.8+
- Navegador moderno (Chrome, Firefox, Safari, Edge)

### Instalación

```bash
# 1. Clonar repositorio
cd Armonia-Web\ antigravity

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar servidor
python app.py
```

### Acceso

Abrir navegador en: **<http://localhost:5001>**

---

## 📁 Estructura del Proyecto

```
Armonia-Web antigravity/
├── app.py                    # Servidor Flask + API de análisis
├── requirements.txt          # Dependencias Python
├── README.md                 # Este archivo
├── templates/
│   └── index.html           # HTML principal
├── static/
│   ├── css/
│   │   └── styles.css        # Estilos (2395 líneas, v2.0)
│   ├── js/
│   │   ├── app.js            # Lógica principal (1044 líneas)
│   │   └── modules/
│   │       ├── audio.js      # Motor de audio (Tone.js)
│   │       └── state.js      # Gestión de estado
│   └── favicon.svg           # Icono de la app
└── .gitignore
```

### Arquitectura

**Frontend**:

- Vanilla JavaScript (ES6 modules)
- VexFlow para notación musical
- Tone.js para síntesis de audio
- CSS Variables para theming

**Backend**:

- Flask (Python)
- Análisis armónico algorítmico
- API REST JSON

---

## 🎯 Uso

### Modos de Operación

#### Modo Escribir

1. Seleccionar voz (SATB)
2. Escribir notas con piano o teclado
3. Navegar con flechas ← →
4. Presionar **Enter** para analizar

#### Modo Revisar

1. Ver análisis de errores
2. Click en errores para resaltar
3. Reproducir partitura
4. Presionar **Esc** para volver a escribir

### Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| `1` `2` `3` `4` | Seleccionar voz (Bajo, Tenor, Alto, Soprano) |
| `A-G` | Notas musicales |
| `←` `→` | Navegar entre tiempos |
| `Backspace` | Borrar nota |
| `Enter` | Analizar y pasar a modo Revisar |
| `Escape` | Volver a modo Escribir |
| `Ctrl/Cmd + Z` | Deshacer |
| `Ctrl/Cmd + Shift + Z` | Rehacer |

### Tonalidades Soportadas

**Mayores**: C, G, D, A, E, B, F♯, C♯, F, B♭, E♭, A♭, D♭, G♭, C♭  
**Menores**: a, e, b, f♯, c♯, g♯, d♯, a♯, d, g, c, f, b♭, e♭, a♭

---

## 🔧 Tecnologías Utilizadas

### Frontend

- **HTML5** - Estructura semántica
- **CSS3** - Design system con variables
- **JavaScript (ES6+)** - Lógica modular
- **VexFlow** - Renderizado de partituras
- **Tone.js** - Síntesis de audio

### Backend

- **Flask** - Framework web
- **Python 3.8+** - Análisis armónico

### Herramientas

- **Git** - Control de versiones
- **VS Code** - Editor recomendado
- **Chrome DevTools** - Debugging

---

## 🧪 Testing

### Manual Testing

```bash
# Desktop
# - Chrome (últimas 2 versiones)
# - Safari (últimas 2 versiones)
# - Firefox (últimas 2 versiones)

# Mobile
# - iOS Safari (iOS 14+)
# - Chrome Android (últimas 2 versiones)
```

### Verificación Rápida

1. Escribir un acorde de 4 voces
2. Presionar Enter → debe mostrar análisis
3. Presionar Esc → debe volver a escritura
4. Ctrl+Z → debe deshacer
5. Reproducir → debe sonar el acorde

---

## 🗺️ Roadmap

### ✅ Fase 1-2: Fundamentos y UX (Completada)

- Interfaz desktop/mobile
- Análisis básico armónico
- Sistema de errores
- Reproducción audio

### 🔜 Fase 3: Reglas Avanzadas (Q1 2026)

- 20+ reglas armónicas
- Dominantes secundarias completas
- Modulaciones básicas
- Sistema de severidad configurable

### 📅 Fase 4: Grados y Cifrados (Q1-Q2 2026)

- Input de bajo cifrado
- Análisis funcional manual
- Múltiples formatos de ejercicio

### 📅 Fase 5: Escritura Avanzada (Q2 2026)

- Compases: 2/4, 3/4, 6/8, etc.
- Notas ornamentales (paso, floreo, apoyatura)
- Figuras rítmicas variadas

### 📅 Fase 6: Modo Profesor (Q2 2026)

- Creación de ejercicios
- Sistema de corrección
- Backend de gestión

### 📅 Fase 7: PWA (Q3 2026)

- Instalable en móvil
- Modo offline
- Optimización viewport

---

## 📝 Decisiones de Diseño

### Por qué Vanilla JS?

- Control total del código
- Sin dependencias innecesarias
- Performance óptimo
- Facilita debugging

### Por qué VexFlow?

- Estándar de facto para notación web
- Renderizado SVG de alta calidad
- Compatible con MusicXML
- Activamente mantenido

### Por qué Flask?

- Lightweight y flexible
- Fácil integración Python
- Perfect para APIs simples
- Rápido desarrollo

---

## 🤝 Contribución

Este es un proyecto educativo privado. Para consultas:

- Email: [contacto]
- Issues: [GitHub issues URL cuando se publique]

---

## 📄 Licencia

Copyright © 2025 José Luis Sánchez  
Todos los derechos reservados

---

## 🙏 Agradecimientos

- **VexFlow** - Notación musical
- **Tone.js** - Síntesis de audio
- **Flask** - Framework backend

---

## 📞 Soporte

Para reportar bugs o sugerir características:

1. Verificar que no esté ya reportado
2. Describir pasos para reproducir
3. Incluir navegador y versión
4. Screenshots si es posible

---

**Última actualización**: Diciembre 2025  
**Mantenedor**: José Luis Sánchez
