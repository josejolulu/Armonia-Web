/* =============================================
   AULA DE ARMONÍA - Lógica de aplicación
   Versión: 1.1 (Modularización Híbrida + Audio)
   ============================================= */

import AudioEngine from './modules/audio.js';
import AppState from './modules/state.js';

// ===== ENCAPSULACIÓN EN OBJETO GLOBAL MEJORADO =====
const AudioStudio = {
    // Referencia corta para uso interno
    state: AppState.data,
    config: AppState.config,

    // Manager de tooltips con ciclo de vida
    tooltipManager: {
        timerId: null,
        show(message, duration = 4000) {
            this.hide();
            const tooltip = document.getElementById('tooltip-error');
            tooltip.textContent = message;
            tooltip.classList.add('tooltip-visible');
            this.timerId = setTimeout(() => this.hide(), duration);
        },
        hide() {
            if (this.timerId) {
                clearTimeout(this.timerId);
                this.timerId = null;
            }
            const tooltip = document.getElementById('tooltip-error');
            if (tooltip) tooltip.classList.remove('tooltip-visible');
        }
    },

    /**
     * Inicializa la aplicación: estado, eventos, UI, y carga datos guardados
     * @returns {void}
     */
    init() {
        // Inicializar Estado Central
        AppState.init();

        this.selectVoice('B');
        this.renderPartiture();
        this.attachEventListeners();
        this.checkFirstVisit();
        // Detección de orientación
        window.addEventListener('orientationchange', () => this.handleOrientationChange());
        // Modo por defecto en móvil: Botones
        if (window.matchMedia && window.matchMedia('(max-width: 600px)').matches) {
            this.setInputMode('buttons');
        } else {
            this.setInputMode('piano');
        }
        // Sincroniza visualmente la alteración por defecto (becuadro)
        this.setAlteracion(this.state.modoAlteracion);
        // Inicializa modo escritura
        this.setAppMode('write');
        // Configura cierre de dropdown de tonalidad
        this._setupTonalityDropdownClose();

        // BUG #7: Configurar touch listeners para piano móvil
        this.setupPianoTouchListeners();

        // AUTO-SCROLL: Configurar touch listeners para detectar scroll manual
        this.setupScrollTouchListeners();

        // Analizar inicialmente para mostrar grados si hay notas recuperadas
        setTimeout(() => this.analyzePartiture(true), 500);

        console.log('✅ AudioStudio inicializado');
    },

    /**
     * Cambia el modo de la aplicación entre Escribir y Revisar
     * @param {string} mode - 'write' o 'review'
     * @returns {void}
     */
    setAppMode(mode) {
        console.log(`[setAppMode] Cambiando a: ${mode}`);

        this.state.appMode = mode;

        // TAREA 3: Usar dataset para que CSS maneje visibilidad
        document.body.dataset.mode = mode;

        document.body.classList.remove('mode-write', 'mode-review');
        document.body.classList.add('mode-' + mode);

        // Toggle header buttons
        document.getElementById('btn-mode-write').classList.toggle('active', mode === 'write');
        document.getElementById('btn-mode-review').classList.toggle('active', mode === 'review');

        // Toggle mobile buttons (si existen)
        const mobileWriteBtn = document.getElementById('btn-mode-write-mobile');
        const mobileReviewBtn = document.getElementById('btn-mode-review-mobile');
        if (mobileWriteBtn) mobileWriteBtn.classList.toggle('active', mode === 'write');
        if (mobileReviewBtn) mobileReviewBtn.classList.toggle('active', mode === 'review');

        // Si entra en review, ejecuta análisis (que re-renderiza al final)
        if (mode === 'review') {
            this.analyzePartiture();

            // Expand sidebar on desktop
            const sidebar = document.getElementById('error-sidebar');
            if (sidebar && window.innerWidth > 480) {
                sidebar.classList.remove('manually-collapsed');
            }
        } else {
            // Oculta panel de resultados en modo escritura
            document.getElementById('panel-resultados').style.display = 'none';
            this.tooltipManager.hide();

            // Collapse sidebar on desktop (optional, but clean)
            const sidebar = document.getElementById('error-sidebar');
            if (sidebar && window.innerWidth > 480) {
                sidebar.classList.add('manually-collapsed');
            }

            // Forzar repaint usando requestAnimationFrame
            requestAnimationFrame(() => this.renderPartiture());
        }

        console.log(`[setAppMode] Completado: ${mode}, body.dataset.mode=${document.body.dataset.mode}`);
    },

    // ===== TONALIDAD =====
    setTonalidad(value) {
        // value viene en formato "C-major" o "A-minor"
        const [tonica, modo] = value.split('-');
        AppState.setTonalidad(tonica, modo);
        // Tonalidad actualizada silenciosamente
        // Re-renderiza la partitura con la nueva armadura
        this.renderPartiture();
        // Si está en modo revisión, re-analiza
        if (this.state.appMode === 'review') {
            this.analyzePartiture();
        }
    },

    getTonalidad() {
        return this.state.tonalidad;
    },

    // Convierte tonalidad al formato VexFlow (ej: "C", "Am", "F#m")
    getKeySignature() {
        const { tonica, modo } = this.state.tonalidad;
        // VexFlow usa: C, G, D, A, E, B, F#, C#, F, Bb, Eb, Ab, Db, Gb, Cb
        // Para menores: Am, Em, Bm, etc.
        if (modo === 'minor') {
            return tonica + 'm';
        }
        return tonica;
    },

    // Toggle del dropdown de tonalidad
    toggleTonalityDropdown() {
        const dropdown = document.getElementById('tonality-dropdown');
        dropdown.classList.toggle('open');
    },

    // Selecciona una tonalidad desde el dropdown
    selectTonality(value, label) {
        // Actualiza el label del trigger
        document.getElementById('tonality-label').textContent = label;
        // Quita clase active de todos
        document.querySelectorAll('.ton-major, .ton-minor').forEach(el => el.classList.remove('active'));
        // Añade active al seleccionado
        event.target.classList.add('active');
        // Cierra el dropdown
        document.getElementById('tonality-dropdown').classList.remove('open');
        // Aplica la tonalidad
        this.setTonalidad(value);
    },

    // Cierra dropdown al hacer clic fuera
    _setupTonalityDropdownClose() {
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('tonality-dropdown');
            if (dropdown && !dropdown.contains(e.target)) {
                dropdown.classList.remove('open');
            }
        });
    },

    // (InitializePartitura movido a AppState.init)

    // (Persistencia movida a AppState)

    checkFirstVisit() {
        const hasVisited = localStorage.getItem('armonia_visited');
        if (!hasVisited) {
            document.getElementById('modal-welcome').classList.add('active');
            localStorage.setItem('armonia_visited', 'true');
        }
    },

    closeWelcome() {
        document.getElementById('modal-welcome').classList.remove('active');
        // Inicializar motor de audio con gesto de usuario
        AudioEngine.init();
    },

    // ===== UNDO/REDO (Delegado a AppState) =====
    undo() {
        if (AppState.undo()) {
            this.state.errorSeleccionado = null;
            this.renderPartiture();
            this.updateHistoryButtons();
        }
    },

    redo() {
        if (AppState.redo()) {
            this.state.errorSeleccionado = null;
            this.renderPartiture();
            this.updateHistoryButtons();
        }
    },

    updateHistoryButtons() {
        document.getElementById('btn-undo').disabled = !AppState.canUndo();
        document.getElementById('btn-redo').disabled = !AppState.canRedo();
    },

    // ===== DETECCIÓN DE ORIENTACIÓN =====
    handleOrientationChange() {
        setTimeout(() => {
            this.renderPartiture();
            const sc = document.querySelector('.scroll-partitura');
            if (sc) sc.scrollLeft = 0;
        }, 100);
    },

    // ===== VALIDACIÓN EN TIEMPO REAL =====
    scheduleValidation() {
        clearTimeout(this.state.validationDebounceTimer);
        this.state.validationDebounceTimer = setTimeout(() => {
            this.analyzePartiture(true); // true = silencioso
        }, this.config.VALIDATION_DEBOUNCE);
    },

    // ===== GESTIÓN DE EVENTOS =====
    attachEventListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    },

    handleKeyboard(e) {
        if (e.target.tagName === 'INPUT') return;

        // AUDIO CONTEXT: Inicializar Tone.js en primera interacción
        if (typeof Tone !== 'undefined' && Tone.context.state === 'suspended') {
            Tone.start().then(() => console.log('[AUDIO] Tone.js context started'));
        }

        // Undo/Redo
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'z') {
                e.preventDefault();
                if (e.shiftKey) this.redo();
                else this.undo();
                return;
            }
            if (e.shiftKey && e.key === 'A') {
                e.preventDefault();
                this.clearAll();
                return;
            }
        }

        const key = e.key.toLowerCase();
        const noteMap = { 'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F', 'g': 'G' };

        if (noteMap[key]) {
            this.animateKey(noteMap[key]);
            this.playWhiteKey(noteMap[key]);
        }
        if (e.key === '1') this.selectVoice('B');
        if (e.key === '2') this.selectVoice('T');
        if (e.key === '3') this.selectVoice('A');
        if (e.key === '4') this.selectVoice('S');
        if (e.key === 'ArrowLeft') this.moveCursor(-1);
        if (e.key === 'ArrowRight') this.moveCursor(1);
        if (e.key === 'Backspace' || e.key === 'Delete') this.addNote(null);

        // ENTER: Cambiar a modo Review y analizar
        if (e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();
            if (document.activeElement) document.activeElement.blur();

            requestAnimationFrame(() => {
                this.setAppMode('review');
            });
        }

        // ESCAPE: Cambiar a modo Write
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            if (document.activeElement) document.activeElement.blur();

            requestAnimationFrame(() => {
                this.setAppMode('write');
            });
        }

        // ESPACIO: Toggle playback
        if (e.code === 'Space') {
            e.preventDefault();
            e.stopPropagation();
            this.togglePlayback();
        }

        // P: Pause
        if (e.code === 'KeyP' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            this.pauseScore();
        }
    },

    animateKey(note) {
        let el = document.getElementById(`key-${note}`);
        if (!el) el = document.getElementById(`key-${note}#`);
        if (el) {
            el.classList.add('active-key');
            setTimeout(() => el.classList.remove('active-key'), 150);
        }
    },

    setAlteracion(alt) {
        this.state.modoAlteracion = alt;
        // Sincroniza radios del header
        const radios = document.querySelectorAll('input[name="alt"]');
        radios.forEach(r => { r.checked = (r.value === alt); });
        // Sincroniza botones móviles
        const btnSharp = document.getElementById('btn-alt-sharp');
        const btnFlat = document.getElementById('btn-alt-flat');
        const btnNat = document.getElementById('btn-alt-natural');
        [btnSharp, btnFlat, btnNat].forEach(b => { if (b) b.classList.remove('active'); });
        const map = { '#': btnSharp, 'b': btnFlat, 'n': btnNat };
        if (map[alt]) map[alt].classList.add('active');
    },

    // ===== NAVEGACIÓN Y SELECCIÓN =====
    moveCursor(delta) {
        this.state.cursorIndex += delta;
        if (this.state.cursorIndex < 0) this.state.cursorIndex = 0;
        if (this.state.cursorIndex >= this.config.TOTAL) this.state.cursorIndex = this.config.TOTAL - 1;

        this.state.errorSeleccionado = null;
        this.tooltipManager.hide();
        this.updateUI();
        this.renderPartiture();

        // AUTO-SCROLL: Desplazar para mantener visible el compás actual
        this.scrollToCurrentPosition({ smooth: true });

        document.getElementById('panel-resultados').style.display = 'none';
    },

    selectVoice(voice) {
        this.state.vozActiva = voice;

        ['S', 'A', 'T', 'B'].forEach(v => {
            document.getElementById(`btn-${v}`).classList.toggle('voz-activa', v === voice);
        });

        // Cambiar octava según voz
        const octavaMap = { 'S': 5, 'A': 4, 'T': 3, 'B': 3 };
        this.state.octavaBase = octavaMap[voice];

        // BUG #7 FIX: Actualizar AMBOS displays de octava (desktop y móvil)
        const displayOctava = document.getElementById('display-octava');
        const mobileOctava = document.getElementById('mobile-octava');

        if (displayOctava) displayOctava.innerText = this.state.octavaBase;
        if (mobileOctava) mobileOctava.innerText = this.state.octavaBase;
    },

    updateUI() {
        const compas = Math.floor(this.state.cursorIndex / 4) + 1;
        const tiempo = (this.state.cursorIndex % 4) + 1;
        document.getElementById('indicador-posicion').innerText = `C.${compas} - T.${tiempo}`;
    },

    // ===== ENTRADA DE NOTAS =====
    // ===== ENTRADA DE NOTAS =====
    addNote(note) {
        AppState.updateNote(this.state.cursorIndex, this.state.vozActiva, note);
        // La actualización del historial y localStorage la maneja AppState

        // TAREA 2 (Bug #6): Reset de alteración después de añadir nota
        // Resetear a natural por defecto para la siguiente nota
        if (note !== null) {
            try {
                this.state.modoAlteracion = 'n';  // Reset to natural

                // Deseleccionar visualmente los botones de alteración
                const btnSos = document.getElementById('btn-alt-sostenido');
                const btnBem = document.getElementById('btn-alt-bemol');
                const btnNat = document.getElementById('btn-alt-natural');

                if (btnSos) btnSos.classList.remove('active');
                if (btnBem) btnBem.classList.remove('active');
                if (btnNat) btnNat.classList.add('active');
            } catch (e) {
                console.warn('Error resetting alteración:', e);
                // Continuar sin romper la ejecución
            }
        }

        const autoFlow = document.getElementById('chk-autoflow').checked;
        if (autoFlow && note !== null) {
            const voiceOrder = ['B', 'T', 'A', 'S'];
            const currentIdx = voiceOrder.indexOf(this.state.vozActiva);

            if (currentIdx < voiceOrder.length - 1) {
                this.selectVoice(voiceOrder[currentIdx + 1]);
            } else {
                this.selectVoice('B');
                this.moveCursor(1);
            }
        }

        this.renderPartiture();

        // AUTO-SCROLL: Desplazar para mantener visible el compás actual
        this.scrollToCurrentPosition({ smooth: true });

        document.getElementById('panel-resultados').style.display = 'none';
        this.scheduleValidation();
    },

    // (changeOctave, playWhiteKey, playHighC, playBlackKey, inputNote, setInputMode... sin cambios)
    changeOctave(delta) {
        this.state.octavaBase += delta;
        if (this.state.octavaBase < 1) this.state.octavaBase = 1;
        if (this.state.octavaBase > 7) this.state.octavaBase = 7;
        document.getElementById('display-octava').innerText = this.state.octavaBase;
        const mo = document.getElementById('mobile-octava');
        if (mo) mo.innerText = this.state.octavaBase;
    },

    // BUG #7: Detector de octava unificado para click y touch
    detectOctaveFromEvent(event, element) {
        // Obtener coordenadas independiente de tipo de evento
        const clientY = event.type && event.type.includes('touch')
            ? event.touches[0].clientY
            : event.clientY;

        const rect = element.getBoundingClientRect();
        const relativeY = clientY - rect.top;
        const height = rect.height;

        // Dividir en 3 zonas: alta (octava +1), media (0), baja (octava -1)
        if (relativeY < height * 0.33) {
            return this.state.octavaBase + 1;  // Zona superior = octava arriba
        } else if (relativeY > height * 0.67) {
            return Math.max(1, this.state.octavaBase - 1);  // Zona inferior = octava abajo
        } else {
            return this.state.octavaBase;  // Zona media = octava actual
        }
    },

    // BUG #7: Setup de listeners touch para piano (móvil)
    setupPianoTouchListeners() {
        // Teclas blancas
        const whiteNotes = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
        whiteNotes.forEach(note => {
            const key = document.getElementById(`key-${note}`);
            if (key) {
                key.addEventListener('touchstart', (e) => {
                    e.preventDefault();  // Prevenir double-tap zoom
                    const octave = this.detectOctaveFromEvent(e, key);
                    const savedOctave = this.state.octavaBase;
                    this.state.octavaBase = octave;
                    this.playWhiteKey(note);
                    this.state.octavaBase = savedOctave;  // Restaurar
                }, { passive: false });
            }
        });

        // Do agudo (Do+)
        const highCKey = document.querySelector('[onclick*="tocarDoAgudo"]');
        if (highCKey) {
            highCKey.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.playHighC();
            }, { passive: false });
        }

        // Teclas negras
        const blackNotes = [
            { id: 'key-C#', note: 'C', next: 'D' },
            { id: 'key-D#', note: 'D', next: 'E' },
            { id: 'key-F#', note: 'F', next: 'G' },
            { id: 'key-G#', note: 'G', next: 'A' },
            { id: 'key-A#', note: 'A', next: 'B' }
        ];
        blackNotes.forEach(({ id, note, next }) => {
            const key = document.getElementById(id);
            if (key) {
                key.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    const octave = this.detectOctaveFromEvent(e, key);
                    const savedOctave = this.state.octavaBase;
                    this.state.octavaBase = octave;
                    this.playBlackKey(note, next);
                    this.state.octavaBase = savedOctave;  // Restaurar
                }, { passive: false });
            }
        });

        console.log('[BUG#7] Piano touch listeners configurados');
    },

    playWhiteKey(note) {
        let n = note;
        let oct = this.state.octavaBase;

        // Lógica de enarmonía para teclas "fantasmas"
        if (this.state.modoAlteracion === '#') {
            if (note === 'F') {
                n = 'E#';
            } else if (note === 'C') {
                n = 'B#';
                oct -= 1;
            }
        } else if (this.state.modoAlteracion === 'b') {
            if (note === 'E') {
                n = 'Fb';
            } else if (note === 'B') {
                n = 'Cb';
                oct += 1;
            }
        }

        // Sonar nota
        AudioEngine.playNote(note + oct); // Usamos nota real (ej: C4) para audio
        this.addNote(n + oct);            // Usamos nota enarmónica (ej: B#3) para partitura
    },

    playHighC() {
        let n = 'C';
        let oct = this.state.octavaBase + 1;

        // Sonar nota
        AudioEngine.playNote('C' + oct);

        if (this.state.modoAlteracion === '#') {
            // Do agudo en modo sostenido -> Si# de la octava base
            n = 'B#';
            oct -= 1;
        }

        this.addNote(n + oct);
    },

    playBlackKey(note, nextNote) {
        let noteToPlay = '';

        if (this.state.modoAlteracion === 'b') {
            // Modo bemol: usar la nota siguiente + bemol (ej: Db)
            this.addNote(nextNote + 'b' + this.state.octavaBase);
            noteToPlay = nextNote + 'b' + this.state.octavaBase;
        } else if (this.state.modoAlteracion === '#') {
            // Modo sostenido: usar la nota actual + sostenido (ej: C#)
            this.addNote(note + '#' + this.state.octavaBase);
            noteToPlay = note + '#' + this.state.octavaBase;
        } else {
            // Modo natural (o sin selección): por defecto usar sostenido para teclas negras
            this.addNote(note + '#' + this.state.octavaBase);
            noteToPlay = note + '#' + this.state.octavaBase;
        }

        // Sonar nota
        if (noteToPlay) AudioEngine.playNote(noteToPlay);
    },

    // Entrada por botones (móvil)
    inputNote(letter) {
        if (this.state.modoAlteracion === 'n') {
            this.addNote(letter + this.state.octavaBase);
        } else {
            this.addNote(letter + this.state.modoAlteracion + this.state.octavaBase);
        }
    },

    setInputMode(mode) {
        // En móvil, fuerza modo botones
        if (window.matchMedia && window.matchMedia('(max-width: 768px)').matches) {
            mode = 'buttons';
        }
        this.state.inputMode = mode;
        const grid = document.getElementById('mobile-input-grid');
        const piano = document.querySelector('.piano-container');
        const select = document.getElementById('input-mode');
        if (select) select.value = mode;
        if (grid && piano) {
            if (mode === 'buttons') {
                grid.style.display = 'block';
                piano.style.display = 'none';
            } else {
                grid.style.display = 'none';
                piano.style.display = 'block';
            }
        }
        // Sincroniza octava en móvil
        const mo = document.getElementById('mobile-octava');
        if (mo) mo.innerText = this.state.octavaBase;
    },

    clearAll() {
        if (confirm("¿Borrar todo?")) {
            AppState.clearAll();

            // Actualizar UI
            document.getElementById('panel-resultados').style.display = 'none';
            this.updateUI();
            this.renderPartiture();
            this.updateHistoryButtons();
        }
    },

    /**
     * Analiza la partitura actual y detecta errores armónicos
     * @param {boolean} silent - Si true, no muestra UI de resultados (para validación en tiempo real)
     * @returns {Promise<void>}
     */
    async analyzePartiture(silent = false) {
        const panel = document.getElementById('panel-resultados');
        const resumen = document.getElementById('resumen-errores');
        const lista = document.getElementById('lista-errores');
        const btn = document.getElementById('btn-corregir'); // May be null (removed in mobile redesign)

        if (!silent) {
            if (btn) {
                btn.innerText = "Analizando...";
                btn.disabled = true;
            }
            lista.innerHTML = "";
            panel.style.display = 'block';
        }

        try {
            const res = await fetch('/analizar_partitura', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    partitura: this.state.partitura,
                    tonalidad: this.state.tonalidad
                })
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();

            if (!Array.isArray(data.errores) || typeof data.mensaje !== 'string') {
                throw new Error("Respuesta del servidor inválida");
            }

            this.state.erroresGlobales = data.errores;
            // Almacenar análisis funcional para renderizado de grados
            this.state.analisisFuncional = data.analisis_funcional || [];

            if (!silent) {
                this.displayResults(data);
                // FASE 2.1: Re-renderizar partitura para mostrar grados
                // (renderPartiture llama a renderGrados con las posiciones reales)
                this.renderPartiture();
            } else {
                // Actualizar indicador visual sin mostrar panel
                this.updateErrorIndicator(data.errores.length);
                // Re-renderizar para mostrar grados actualizados en tiempo real
                this.renderPartiture();
            }

        } catch (error) {
            console.error('Error:', error);
            if (!silent) {
                resumen.innerHTML = "❌ Error de conexión";
                resumen.style.color = "#ff0000";
                resumen.style.background = "#ffebee";
            }
        } finally {
            if (!silent) {
                if (btn) {
                    btn.innerText = "✅ Corregir";
                    btn.disabled = false;
                }
            }
        }
    },

    updateErrorIndicator(errorCount) {
        const btn = document.getElementById('btn-corregir');
        if (!btn) return; // Button doesn't exist in current UI

        if (errorCount > 0) {
            btn.classList.add('has-errors');
            btn.style.opacity = '0.9';
        } else {
            btn.classList.remove('has-errors');
            btn.style.opacity = '1';
        }
    },

    displayResults(data) {
        const resumen = document.getElementById('resumen-errores');
        const lista = document.getElementById('lista-errores');
        const panel = document.getElementById('panel-resultados');

        if (this.state.erroresGlobales.length === 0) {
            resumen.innerHTML = `✅ ${data.mensaje}`;
            resumen.style.color = "var(--success)";
            resumen.style.background = "#e8f9f0";
            // Sin errores: mostrar panel brevemente y volver a escribir
            panel.style.display = 'block';

            // Update sidebar
            this.updateErrorSidebar([]);
        } else {
            resumen.innerHTML = `⚠️ Se han encontrado ${this.state.erroresGlobales.length} errores`;
            resumen.style.color = "var(--danger)";
            resumen.style.background = "#ffebee";

            this.state.erroresGlobales.forEach((err, idx) => {
                const div = document.createElement('div');
                div.className = 'item-error';
                div.innerText = err.mensaje;
                div.onclick = () => this.highlightError(idx);
                lista.appendChild(div);
            });

            // Update sidebar
            this.updateErrorSidebar(this.state.erroresGlobales);

            // Always switch to review mode when analyzing (desktop-only logic usually)
            if (this.state.appMode !== 'review') {
                this.setAppMode('review');
            }
            panel.style.display = 'block';
        }
    },

    // ===== FASE 2.1: RENDERIZADO DE GRADOS =====
    // Sistema híbrido: HTML superpuesto sobre VexFlow para permitir interactividad futura
    // Las posiciones X se obtienen directamente de las notas VexFlow después del render

    renderGrados(notasBajoConIndice = []) {
        const container = document.getElementById('grados-container');
        if (!container) return;

        container.innerHTML = '';

        // Solo renderizar si hay análisis disponible
        if (this.state.analisisFuncional.length === 0) return;

        // Crear mapa de análisis por tiempo
        const analisisMap = {};
        this.state.analisisFuncional.forEach(a => {
            if (a) {
                analisisMap[a.tiempo_index] = a;
            }
        });

        // Usar posiciones X reales de las notas VexFlow
        notasBajoConIndice.forEach(({ nota, tiempoIndex }) => {
            const analisis = analisisMap[tiempoIndex];
            if (!analisis) return;

            let xNota;
            try {
                // Intentar obtener X absoluta. 
                xNota = nota.getAbsoluteX();

                // Si da 0 o undefined, algo falla en VexFlow
                if (!xNota || isNaN(xNota)) {
                    // Intento alternativo: tickContext
                    if (nota.getTickContext()) {
                        xNota = nota.getTickContext().getX();
                    }
                }

                // Ajuste de centrado
                const width = (nota.getGlyphWidth ? nota.getGlyphWidth() : 10);
                xNota = xNota + (width / 2);

            } catch (e) {
                console.error(`Error obteniendo coordenadas T${tiempoIndex}:`, e);
                return;
            }

            // Crear elemento del grado
            const gradoEl = document.createElement('span');
            gradoEl.className = `grado-item funcion-${analisis.funcion || 'T'}`;
            gradoEl.style.left = `${xNota}px`;

            // Formatear texto del grado
            gradoEl.innerHTML = this._formatearHTMLGrado(analisis);

            container.appendChild(gradoEl);
        });
    },

    // Formatea el grado como HTML con cifrado europeo correcto
    _formatearHTMLGrado(analisis) {
        const grado = analisis.grado || '';
        const cifrado = analisis.cifrado_europeo || '';
        const inversion = analisis.inversion;
        const tieneSeptima = analisis.tiene_septima;
        const tieneNovena = analisis.tiene_novena;
        const tipoEspecial = analisis.tipo_especial;

        // Acordes especiales: Napolitana, sextas aumentadas
        if (tipoEspecial === 'N') {
            const sup = cifrado ? `<span class="cifrado-sup">${cifrado}</span>` : '';
            return `<span class="grado-base">${grado}</span>${sup}`;
        }

        if (tipoEspecial && tipoEspecial.startsWith('+6')) {
            // +6it, +6fr, +6al
            return `<span class="grado-base">${grado}</span>`;
        }

        if (tipoEspecial === 'prestamo_menor') {
            const sup = cifrado ? `<span class="cifrado-sup">${cifrado}</span>` : '';
            return `<span class="grado-base">${grado}</span>${sup}`;
        }

        // Dominantes secundarias: V/V, V7/V, V+6/vi, etc.
        if (grado && grado.includes('/')) {
            const [base, objetivo] = grado.split('/');

            // Si hay cifrado, procesarlo (puede ser apilado con coma)
            if (cifrado) {
                // Si contiene coma, es apilado (ej: "6,5t")
                if (cifrado.includes(',')) {
                    const partes = cifrado.split(',');
                    let stackHTML = '<span class="cifrado-stack">';
                    partes.forEach(p => {
                        if (p.endsWith('t')) {
                            stackHTML += `<span class="tachado">${p.slice(0, -1)}</span>`;
                        } else if (p === '+') {
                            stackHTML += `<span>+</span>`;
                        } else {
                            stackHTML += `<span>${p}</span>`;
                        }
                    });
                    stackHTML += '</span>';
                    return `<span class="grado-base">${base}</span>${stackHTML}<span class="secundaria">/${objetivo}</span>`;
                }

                // Cifrado simple (ej: "7", "+")
                if (cifrado.endsWith('t')) {
                    return `<span class="grado-base">${base}</span><span class="cifrado-sup tachado">${cifrado.slice(0, -1)}</span><span class="secundaria">/${objetivo}</span>`;
                }
                return `<span class="grado-base">${base}</span><span class="cifrado-sup">${cifrado}</span><span class="secundaria">/${objetivo}</span>`;
            }

            return `<span class="grado-base">${base}</span><span class="secundaria">/${objetivo}</span>`;
        }

        // Acordes normales (V7, etc.)
        if (cifrado) {
            // Si contiene coma, es apilado (ej: "6,5t")
            if (cifrado.includes(',')) {
                const partes = cifrado.split(',');
                let stackHTML = '<span class="cifrado-stack">';
                partes.forEach(p => {
                    if (p.endsWith('t')) {
                        stackHTML += `<span class="tachado">${p.slice(0, -1)}</span>`;
                    } else if (p === '+') {
                        stackHTML += `<span>+</span>`;
                    } else {
                        stackHTML += `<span>${p}</span>`;
                    }
                });
                stackHTML += '</span>';
                return `<span class="grado-base">${grado}</span>${stackHTML}`;
            }

            // Cifrado simple
            if (cifrado.endsWith('t')) {
                return `<span class="grado-base">${grado}</span><span class="cifrado-sup tachado">${cifrado.slice(0, -1)}</span>`;
            }
            return `<span class="grado-base">${grado}</span><span class="cifrado-sup">${cifrado}</span>`;
        }

        return grado;
    },

    // Versión texto plano para Annotations (backup)
    _formatearTextoGrado(analisis) {
        const grado = analisis.grado || '';
        const inversion = analisis.inversion;

        // Caso especial: V7 en estado fundamental → "V⁷₊" (usando superscript unicode)
        if (grado === 'V' && analisis.tiene_septima && inversion === 0) {
            return 'V⁷₊';
        }

        return analisis.texto_completo || '';
    },

    // Limpiar grados al cambiar a modo escritura
    clearGrados() {
        const container = document.getElementById('grados-container');
        if (container) container.innerHTML = '';
    },

    // ===== AUTO-SCROLL HORIZONTAL =====
    /**
     * Desplaza el contenedor de scroll para que el compás actual sea visible.
     * Calcula la posición basada en cursorIndex y config.
     * 
     * @param {Object} options - Opciones de scroll
     * @param {boolean} options.smooth - Usar transición suave (default: true)
     * @param {boolean} options.center - Centrar el compás en pantalla (default: false)
     */
    scrollToCurrentPosition(options = {}) {
        const { smooth = true, center = false } = options;

        const scrollContainer = document.querySelector('.scroll-partitura');
        if (!scrollContainer) return;

        // Detectar si hay touch activo (evitar interferencia con scroll manual)
        if (this.state.touchActive) return;

        const measureIndex = Math.floor(this.state.cursorIndex / 4);
        const measureWidth = 270; // Ancho de cada compás en VexFlow (this.config)
        const containerWidth = scrollContainer.clientWidth;

        let targetScroll;

        if (center) {
            // Centrar el compás en la pantalla
            targetScroll = (measureIndex * measureWidth) - (containerWidth / 2) + (measureWidth / 2);
        } else {
            // Mostrar el compás con margen (un compás de anticipación)
            targetScroll = Math.max(0, (measureIndex - 1) * measureWidth);
        }

        // Limitar scroll al máximo posible
        const maxScroll = scrollContainer.scrollWidth - containerWidth;
        targetScroll = Math.min(targetScroll, maxScroll);

        if (smooth) {
            scrollContainer.scrollTo({
                left: targetScroll,
                behavior: 'smooth'
            });
        } else {
            scrollContainer.scrollLeft = targetScroll;
        }
    },

    /**
     * Marca que hay un touch activo (para evitar auto-scroll durante scroll manual)
     */
    setTouchActive(active) {
        this.state.touchActive = active;

        // Debounce: volver a habilitar auto-scroll tras 300ms sin touch
        if (!active) {
            clearTimeout(this.state.touchDebounceTimer);
            this.state.touchDebounceTimer = setTimeout(() => {
                this.state.touchActive = false;
            }, 300);
        }
    },

    /**
     * Configura listeners de touch/scroll en el contenedor de la partitura
     * para detectar scroll manual del usuario y pausar el auto-scroll
     */
    setupScrollTouchListeners() {
        const scrollContainer = document.querySelector('.scroll-partitura');
        if (!scrollContainer) {
            console.warn('[AUTO-SCROLL] Contenedor .scroll-partitura no encontrado');
            return;
        }

        // Touch start: marcar que hay touch activo
        scrollContainer.addEventListener('touchstart', () => {
            this.setTouchActive(true);
        }, { passive: true });

        // Touch end: desmarcar después de debounce
        scrollContainer.addEventListener('touchend', () => {
            this.setTouchActive(false);
        }, { passive: true });

        // También detectar scroll por mouse (wheel)
        scrollContainer.addEventListener('wheel', () => {
            this.setTouchActive(true);
            // Reset después de 500ms de inactividad
            clearTimeout(this.state.touchDebounceTimer);
            this.state.touchDebounceTimer = setTimeout(() => {
                this.state.touchActive = false;
            }, 500);
        }, { passive: true });

        console.log('[AUTO-SCROLL] Touch listeners configurados');
    },

    highlightError(index) {
        this.state.errorSeleccionado = this.state.erroresGlobales[index];
        this.state.cursorIndex = this.state.errorSeleccionado.tiempo_index;
        this.renderPartiture();

        const sc = document.querySelector('.scroll-partitura');
        const measureIndex = Math.floor(this.state.cursorIndex / 4);
        const scrollPosition = (measureIndex - 1) * 300;
        if (scrollPosition > 0) sc.scrollLeft = scrollPosition;

        document.querySelectorAll('.item-error').forEach((el, i) => {
            el.classList.toggle('seleccionado', i === index);
        });
    },

    /**
     * Renderiza la partitura completa usando VexFlow
     * Genera el pentagrama, claves, notas y grados funcionales
     * @returns {void}
     */
    renderPartiture() {
        try {
            document.getElementById('lienzo-partitura').innerHTML = '';

            const VF = VexFlow;
            const vf = new VF.Factory({
                renderer: {
                    elementId: 'lienzo-partitura',
                    width: this.config.NUM_COMPASES * 270 + 50,
                    height: 320
                }
            });
            const score = vf.EasyScore();

            let xPos = 0;
            let yPos = 30;

            // Almacenar notas del bajo para obtener posiciones X después del render
            const notasBajoConIndice = [];

            // TAREA 1 (Bug #6): Helpers para tracking de alteraciones
            const getAccidentalFromNote = (noteStr) => {
                if (!noteStr) return null;
                if (noteStr.includes('#')) return '#';
                if (noteStr.includes('b')) return 'b';
                if (noteStr.includes('n')) return 'n';
                return null;  // Natural sin marca explícita
            };

            const getNoteBaseName = (noteStr) => {
                if (!noteStr) return '';
                return noteStr[0].toUpperCase();  // 'C', 'D', 'E', etc
            };

            for (let c = 0; c < this.config.NUM_COMPASES; c++) {
                const inicio = c * this.config.TIEMPOS;
                const fin = inicio + this.config.TIEMPOS;
                const slice = this.state.partitura.slice(inicio, fin);

                // TAREA 1 (Bug #6): Inicializar tracker de alteraciones por compás
                const measureAccidentals = {};

                const strS = this.generateVoiceString(slice, 'S');
                const strA = this.generateVoiceString(slice, 'A');
                const strT = this.generateVoiceString(slice, 'T');
                const strB = this.generateVoiceString(slice, 'B');

                const ns = score.notes(strS, { stem: 'up' });
                const na = score.notes(strA, { stem: 'down' });
                const nt = score.notes(strT, { stem: 'up', clef: 'bass' });
                const nb = score.notes(strB, { stem: 'down', clef: 'bass' });

                // TAREA 1 (Bug #6): Aplicar becuadros automáticos
                // CRITICAL FIX: Solo añadir modificador para BECUADROS
                // VexFlow ya renderiza # y b desde el string "F#4/q", no necesitan addModifier
                const applyAccidentals = (staveNotes, voiceData, voice) => {
                    staveNotes.forEach((staveNote, idx) => {
                        const originalNote = voiceData[idx];
                        if (!originalNote || originalNote === null) return;

                        const noteBaseName = getNoteBaseName(originalNote);
                        const currentAccidental = getAccidentalFromNote(originalNote);
                        const previousAccidental = measureAccidentals[noteBaseName];

                        // Decidir si mostrar BECUADRO (solo becuadros, no # ni b)
                        let shouldShowNatural = false;

                        if (currentAccidental === null || currentAccidental === 'n') {
                            // Nota es natural
                            if (previousAccidental && (previousAccidental === '#' || previousAccidental === 'b')) {
                                // Había alteración previa, mostrar becuadro
                                shouldShowNatural = true;
                            }
                            measureAccidentals[noteBaseName] = null;  // Actualizar tracker
                        } else {
                            // Nota tiene alteración (# o b)
                            // VexFlow ya la renderiza desde el string, solo actualizar tracker
                            measureAccidentals[noteBaseName] = currentAccidental;
                        }

                        // Aplicar SOLO becuadro si es necesario
                        // NO añadir modificador para # o b (ya están en el string)
                        if (shouldShowNatural && staveNote.keys && staveNote.keys.length > 0) {
                            try {
                                const VF = VexFlow;
                                staveNote.addModifier(new VF.Accidental('n'), 0);
                            } catch (e) {
                                console.warn(`Error añadiendo becuadro a ${voice}:`, e);
                            }
                        }
                    });
                };

                // Aplicar a cada voz
                const voicesData = {
                    'S': slice.map(t => t.S),
                    'A': slice.map(t => t.A),
                    'T': slice.map(t => t.T),
                    'B': slice.map(t => t.B)
                };

                applyAccidentals(ns, voicesData.S, 'S');
                applyAccidentals(na, voicesData.A, 'A');
                applyAccidentals(nt, voicesData.T, 'T');
                applyAccidentals(nb, voicesData.B, 'B');

                // Guardar referencia a notas del bajo con su índice de tiempo
                nb.forEach((nota, idx) => {
                    notasBajoConIndice.push({ nota, tiempoIndex: inicio + idx });
                });

                this.applyCursorStyle(ns, inicio, 'S');
                this.applyCursorStyle(na, inicio);
                this.applyCursorStyle(nt, inicio);
                this.applyCursorStyle(nb, inicio);

                // Los grados se renderizan por separado en HTML (ver renderGrados)

                if (this.state.errorSeleccionado) {
                    const c_error = Math.floor(this.state.errorSeleccionado.tiempo_index / 4);
                    if (c === c_error || c === c_error + 1) {
                        this.applyErrorStyle(ns, inicio, 'S', xPos);
                        this.applyErrorStyle(na, inicio, 'A', xPos);
                        this.applyErrorStyle(nt, inicio, 'T', xPos);
                        this.applyErrorStyle(nb, inicio, 'B', xPos);
                    }
                }

                const ancho = (c === 0) ? 320 : 270;
                const sys = vf.System({ x: xPos, y: yPos, width: ancho });

                const st = sys.addStave({ voices: [score.voice(ns), score.voice(na)] });
                const sb = sys.addStave({ voices: [score.voice(nt), score.voice(nb)] });

                if (c === 0) {
                    st.addClef('treble').addKeySignature(this.getKeySignature()).addTimeSignature('4/4');
                    sb.addClef('bass').addKeySignature(this.getKeySignature()).addTimeSignature('4/4');
                    sys.addConnector('brace');
                    sys.addConnector('singleLeft');
                } else {
                    sys.addConnector('singleLeft');
                }
                if (c === this.config.NUM_COMPASES - 1) sys.addConnector('boldDoubleRight');

                vf.draw();
                xPos += ancho;
            }

            // FASE 2.1: Renderizar grados con posiciones X reales de VexFlow
            this.renderGrados(notasBajoConIndice);

            // AUTO-FOCUS: Reclamar foco para que teclado funcione desde el inicio
            document.body.focus();

        } catch (e) {
            console.error('Error renderizando:', e);
        }
    },

    generateVoiceString(slice, voice) {
        return slice.map((t) => {
            let n = t[voice];
            if (n) return `${n}/q`;
            let silence = (voice === 'S') ? 'a5' : (voice === 'A') ? 'f4' : (voice === 'T') ? 'a3' : 'e2';
            if (voice === 'T' && t['B'] && (t['B'].includes('3') || t['B'].includes('4'))) silence = 'c4';
            return `${silence}/q/r`;
        }).join(', ');
    },

    applyCursorStyle(noteList, offset, voice) {
        noteList.forEach((n, i) => {
            if ((offset + i) === this.state.cursorIndex) {
                n.setStyle({ fillStyle: "#546de5", strokeStyle: "#546de5" });
                if (voice === 'S') {
                    const VF = VexFlow;
                    if (VF.Annotation) {
                        n.addModifier(new VF.Annotation("▼").setFont("Arial", 20, 3).setVerticalJustification(1));
                    }
                }
            }
        });
    },

    applyErrorStyle(noteList, offset, voice, xOffset) {
        noteList.forEach((n, i) => {
            const idxReal = offset + i;

            // CRITICAL FIX: Manejar el caso voices=['?'] (factor omitido)
            // Cuando no sabemos qué voz específica tiene el error, mostrarlo en todas
            const isVoiceAffected =
                this.state.errorSeleccionado.voces.includes(voice) ||
                (this.state.errorSeleccionado.voces.includes('?') &&
                    (idxReal === this.state.errorSeleccionado.tiempo_index ||
                        idxReal === this.state.errorSeleccionado.tiempo_index + 1));

            if (isVoiceAffected) {
                if (idxReal === this.state.errorSeleccionado.tiempo_index ||
                    idxReal === this.state.errorSeleccionado.tiempo_index + 1) {
                    n.setStyle({ fillStyle: "#ff0000", strokeStyle: "#ff0000" });
                    if (idxReal === this.state.errorSeleccionado.tiempo_index &&
                        (voice === this.state.errorSeleccionado.voces[0] ||
                            this.state.errorSeleccionado.voces[0] === '?')) {
                        this.showTooltip(i, xOffset);
                    }
                }
            }
        });
    },

    showTooltip(localIndex, xOffsetCompas) {
        // Tooltip fijo en la parte superior central del stage
        // Ya no calcula posición dinámica - se define en CSS
        this.tooltipManager.show(this.state.errorSeleccionado.mensaje_corto);
    },

    // ===== CONTROLES DE REPRODUCCIÓN (Fase 2.3) =====
    playScore() {
        const bpm = parseInt(document.getElementById('bpm-input').value) || 120;

        // Callback de progreso para auto-scroll sincronizado
        const onProgress = (timeIndex) => {
            if (timeIndex === -1) {
                // Fin de reproducción
                console.log('[PLAYBACK] Fin de reproducción');
                return;
            }

            // Actualizar cursor visual al tiempo actual
            this.state.cursorIndex = timeIndex;
            this.updateUI();
            this.renderPartiture();

            // Auto-scroll sin smooth para seguir el tempo (inmediato)
            this.scrollToCurrentPosition({ smooth: false, center: true });
        };

        AudioEngine.playScore(this.state.partitura, bpm, onProgress);
    },

    pauseScore() {
        AudioEngine.pause();
    },

    stopScore() {
        AudioEngine.stop();
    },

    setBpm(val) {
        let bpm = parseInt(val);
        if (bpm < 40) bpm = 40;
        if (bpm > 240) bpm = 240;

        document.getElementById('bpm-input').value = bpm;
        AudioEngine.setBpm(bpm);
    },

    togglePlayback() {
        if (AudioEngine.isPlaying) {
            this.stopScore();
        } else {
            this.playScore();
        }
    }
};

// Inicialización y Exposición Global (Necesario para type="module")
window.AudioStudio = AudioStudio;

// Inicialización cuando el DOM esté listo
window.addEventListener('DOMContentLoaded', () => {
    AudioStudio.init();

    // AUTO-FOCUS: Reclamar foco global para que el teclado funcione desde el inicio
    document.body.tabIndex = -1;  // Permitir que body reciba foco
    document.body.focus();

    console.log('[INIT] Foco global establecido en body');
});

// Phase 2: Desktop UX Enhancements - New functions
const AudioStudioExtensions = {
    // Sidebar toggle
    toggleErrorSidebar() {
        const sidebar = document.getElementById('error-sidebar');
        if (sidebar) {
            sidebar.classList.toggle('manually-collapsed');
        }
    },

    // Update sidebar error list
    updateErrorSidebar(errores) {
        const list = document.getElementById('sidebar-error-list');
        const badge = document.getElementById('sidebar-error-count');
        const headerBadgeText = document.getElementById('header-error-text');

        if (!list || !badge) return;

        list.innerHTML = '';
        badge.textContent = errores.length;

        // Update header badge if it exists
        if (headerBadgeText) {
            headerBadgeText.textContent = `${errores.length} error${errores.length !== 1 ? 'es' : ''}`;
        }

        if (errores.length === 0) {
            list.innerHTML = '<div class="no-errors-sidebar">No se han detectado errores</div>';
            return;
        }

        errores.forEach((err, idx) => {
            const item = document.createElement('div');
            item.className = 'error-item-sidebar';
            const errorColor = err.color || '#FF0000';

            // Calcular si el color de fondo es claro u oscuro
            // Extraer RGB del color hexadecimal
            const r = parseInt(errorColor.slice(1, 3), 16);
            const g = parseInt(errorColor.slice(3, 5), 16);
            const b = parseInt(errorColor.slice(5, 7), 16);

            // Calcular luminosidad (0-255, donde >128 es claro)
            const luminosity = (0.299 * r + 0.587 * g + 0.114 * b);

            // Texto negro si fondo claro, blanco si fondo oscuro
            const textColor = luminosity > 128 ? '#000000' : '#FFFFFF';

            item.innerHTML = `
                <div class="error-number" style="background-color: ${errorColor}; color: ${textColor};">${idx + 1}</div>
                <div class="error-text">${err.mensaje}</div>
            `;
            item.onclick = () => AudioStudio.highlightError(idx);
            list.appendChild(item);
        });
    },

    // Playback navigation
    prevCompas() {
        const currentIndex = AudioStudio.state.cursorIndex;
        const tiempos = AudioStudio.config.TIEMPOS;
        const newIndex = Math.max(0, Math.floor(currentIndex / tiempos) * tiempos - tiempos);
        AudioStudio.moveCursor(newIndex - currentIndex);
    },

    nextCompas() {
        const currentIndex = AudioStudio.state.cursorIndex;
        const tiempos = AudioStudio.config.TIEMPOS;
        const numCompases = AudioStudio.config.NUM_COMPASES;
        const maxIndex = numCompases * tiempos - 1;
        const nextCompasStart = (Math.floor(currentIndex / tiempos) + 1) * tiempos;
        const newIndex = Math.min(maxIndex, nextCompasStart);
        AudioStudio.moveCursor(newIndex - currentIndex);
    },

    // Loop mode toggle
    toggleLoop() {
        AudioStudio.state.loopMode = !AudioStudio.state.loopMode;
        const btn = document.getElementById('btn-loop');
        if (btn) {
            btn.classList.toggle('active');
        }
    },

    // Playback speed
    setPlaybackSpeed(speed) {
        const speedValue = parseFloat(speed);
        AudioStudio.playbackSpeed = speedValue;
        // Note: Actual implementation depends on audio engine
        // Velocidad de reproducc ión actualizada
    }
};

// Merge extensions into AudioStudio
Object.assign(AudioStudio, AudioStudioExtensions);

// Wrapper functions EXPLICITAMENTE globales para HTML onclick
window.moverCursor = (d) => AudioStudio.moveCursor(d);
window.seleccionarVoz = (v) => AudioStudio.selectVoice(v);
window.cambiarOctava = (d) => AudioStudio.changeOctave(d);
window.tocarBlanca = (n) => AudioStudio.playWhiteKey(n);
window.tocarDoAgudo = () => AudioStudio.playHighC();
window.tocarNegra = (n, next) => AudioStudio.playBlackKey(n, next);
window.analizarPartitura = () => AudioStudio.analyzePartiture();
window.borrarTodo = () => AudioStudio.clearAll();
window.reproducirPartitura = () => AudioStudio.playScore();
window.pausarPartitura = () => AudioStudio.pauseScore();
window.detenerPartitura = () => AudioStudio.stopScore();
