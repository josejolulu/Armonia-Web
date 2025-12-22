/* =============================================
   AULA DE ARMONÍA - Lógica de aplicación
   Versión: 1.0
   ============================================= */

// ===== ENCAPSULACIÓN EN OBJETO GLOBAL MEJORADO =====
const AudioStudio = {
    // Estado central
    state: {
        partitura: [],
        cursorIndex: 0,
        vozActiva: 'B',
        octavaBase: 3,
        modoAlteracion: 'n',
        errorSeleccionado: null,
        erroresGlobales: [],
        history: [],
        historyIndex: -1,
        validationDebounceTimer: null,
        lastAnalysisTime: 0,
        inputMode: 'piano',
        appMode: 'write'
    },
    
    // Configuración
    config: {
        NUM_COMPASES: 4,
        TIEMPOS: 4,
        STORAGE_KEY: 'armonia_partitura',
        HISTORY_MAX: 20,
        VALIDATION_DEBOUNCE: 1000
    },
    
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
    
    // Inicialización
    init() {
        this.config.TOTAL = this.config.NUM_COMPASES * this.config.TIEMPOS;
        this.initializePartitura();
        this.loadFromStorage();
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
        console.log('✅ AudioStudio inicializado');
    },

    // ===== MODO DE APP (ESCRITURA/CORRECCIÓN) =====
    setAppMode(mode) {
        this.state.appMode = mode;
        document.body.classList.remove('mode-write', 'mode-review');
        document.body.classList.add('mode-' + mode);
        // Toggle buttons
        document.getElementById('btn-mode-write').classList.toggle('active', mode === 'write');
        document.getElementById('btn-mode-review').classList.toggle('active', mode === 'review');
        // Si entra en review, ejecuta análisis
        if (mode === 'review') {
            this.analyzePartiture();
        } else {
            // Oculta panel de resultados en modo escritura
            document.getElementById('panel-resultados').style.display = 'none';
            this.tooltipManager.hide();
        }
        this.renderPartiture();
    },
    
    // Inicializa array vacío de partitura
    initializePartitura() {
        this.state.partitura = [];
        for(let i = 0; i < this.config.TOTAL; i++) {
            this.state.partitura.push({ 'S': null, 'A': null, 'T': null, 'B': null });
        }
        this.state.history = [JSON.parse(JSON.stringify(this.state.partitura))];
        this.state.historyIndex = 0;
    },
    
    // ===== PERSISTENCIA CON LOCALSTORAGE =====
    saveToStorage() {
        try {
            localStorage.setItem(this.config.STORAGE_KEY, JSON.stringify(this.state.partitura));
        } catch (e) {
            console.warn('LocalStorage no disponible:', e);
        }
    },
    
    loadFromStorage() {
        try {
            const saved = localStorage.getItem(this.config.STORAGE_KEY);
            if (saved) {
                this.state.partitura = JSON.parse(saved);
                this.state.history = [JSON.parse(JSON.stringify(this.state.partitura))];
                this.state.historyIndex = 0;
                console.log('✅ Partitura recuperada de almacenamiento');
            }
        } catch (e) {
            console.warn('Error al cargar partitura:', e);
        }
    },
    
    checkFirstVisit() {
        const hasVisited = localStorage.getItem('armonia_visited');
        if (!hasVisited) {
            document.getElementById('modal-welcome').classList.add('active');
            localStorage.setItem('armonia_visited', 'true');
        }
    },
    
    closeWelcome() {
        document.getElementById('modal-welcome').classList.remove('active');
    },
    
    // ===== UNDO/REDO =====
    pushToHistory() {
        // Remover redo si estamos en medio del historial
        if (this.state.historyIndex < this.state.history.length - 1) {
            this.state.history = this.state.history.slice(0, this.state.historyIndex + 1);
        }
        // Agregar nuevo estado
        this.state.history.push(JSON.parse(JSON.stringify(this.state.partitura)));
        // Limitar tamaño del historial
        if (this.state.history.length > this.config.HISTORY_MAX) {
            this.state.history.shift();
        } else {
            this.state.historyIndex++;
        }
        this.updateHistoryButtons();
    },
    
    undo() {
        if (this.state.historyIndex > 0) {
            this.state.historyIndex--;
            this.state.partitura = JSON.parse(JSON.stringify(this.state.history[this.state.historyIndex]));
            this.state.errorSeleccionado = null;
            this.saveToStorage();
            this.renderPartiture();
            this.updateHistoryButtons();
        }
    },
    
    redo() {
        if (this.state.historyIndex < this.state.history.length - 1) {
            this.state.historyIndex++;
            this.state.partitura = JSON.parse(JSON.stringify(this.state.history[this.state.historyIndex]));
            this.state.errorSeleccionado = null;
            this.saveToStorage();
            this.renderPartiture();
            this.updateHistoryButtons();
        }
    },
    
    updateHistoryButtons() {
        document.getElementById('btn-undo').disabled = this.state.historyIndex <= 0;
        document.getElementById('btn-redo').disabled = this.state.historyIndex >= this.state.history.length - 1;
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
        if(e.target.tagName === 'INPUT') return;
        
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
        const noteMap = { 'a':'A', 'b':'B', 'c':'C', 'd':'D', 'e':'E', 'f':'F', 'g':'G' };
        
        if (noteMap[key]) {
            this.animateKey(noteMap[key]);
            this.playWhiteKey(noteMap[key]);
        }
        if(e.key === '1') this.selectVoice('B');
        if(e.key === '2') this.selectVoice('T');
        if(e.key === '3') this.selectVoice('A');
        if(e.key === '4') this.selectVoice('S');
        if(e.key === 'ArrowLeft') this.moveCursor(-1);
        if(e.key === 'ArrowRight') this.moveCursor(1);
        if(e.key === 'Backspace' || e.key === 'Delete') this.addNote(null);
        if(e.key === 'Enter') this.analyzePartiture();
    },
    
    animateKey(note) {
        let el = document.getElementById(`key-${note}`);
        if(!el) el = document.getElementById(`key-${note}#`);
        if(el) {
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
        if(this.state.cursorIndex < 0) this.state.cursorIndex = 0;
        if(this.state.cursorIndex >= this.config.TOTAL) this.state.cursorIndex = this.config.TOTAL - 1;
        
        this.state.errorSeleccionado = null;
        this.tooltipManager.hide();
        this.updateUI();
        this.renderPartiture();
        document.getElementById('panel-resultados').style.display = 'none';
    },
    
    selectVoice(voice) {
        this.state.vozActiva = voice;
        
        ['S','A','T','B'].forEach(v => {
            document.getElementById(`btn-${v}`).classList.toggle('voz-activa', v === voice);
        });
        
        const octavaMap = { 'S': 5, 'A': 4, 'T': 3, 'B': 3 };
        this.state.octavaBase = octavaMap[voice];
        document.getElementById('display-octava').innerText = this.state.octavaBase;
    },
    
    updateUI() {
        const compas = Math.floor(this.state.cursorIndex / 4) + 1;
        const tiempo = (this.state.cursorIndex % 4) + 1;
        document.getElementById('indicador-posicion').innerText = `C.${compas} - T.${tiempo}`;
    },
    
    // ===== ENTRADA DE NOTAS =====
    addNote(note) {
        this.state.partitura[this.state.cursorIndex][this.state.vozActiva] = note;
        this.saveToStorage();
        this.pushToHistory();
        
        const autoFlow = document.getElementById('chk-autoflow').checked;
        if(autoFlow && note !== null) {
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
        document.getElementById('panel-resultados').style.display = 'none';
        this.scheduleValidation();
    },
    
    changeOctave(delta) {
        this.state.octavaBase += delta;
        if(this.state.octavaBase < 1) this.state.octavaBase = 1;
        if(this.state.octavaBase > 7) this.state.octavaBase = 7;
        document.getElementById('display-octava').innerText = this.state.octavaBase;
        const mo = document.getElementById('mobile-octava');
        if (mo) mo.innerText = this.state.octavaBase;
    },
    
    playWhiteKey(note) {
        this.addNote(note + this.state.octavaBase);
    },
    
    playHighC() {
        this.addNote('C' + (this.state.octavaBase + 1));
    },
    
    playBlackKey(note) {
        if (this.state.modoAlteracion === 'n') {
            this.addNote(note + this.state.octavaBase);
        } else {
            this.addNote(note + this.state.modoAlteracion + this.state.octavaBase);
        }
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
        if(confirm("¿Borrar todo?")) {
            this.state.partitura.forEach(p => {
                p.S = null; p.A = null; p.T = null; p.B = null;
            });
            this.state.cursorIndex = 0;
            this.state.errorSeleccionado = null;
            document.getElementById('panel-resultados').style.display = 'none';
            this.updateUI();
            this.renderPartiture();
            this.pushToHistory();
            this.saveToStorage();
        }
    },
    
    // ===== ANÁLISIS CON VALIDACIÓN EN TIEMPO REAL =====
    async analyzePartiture(silent = false) {
        const panel = document.getElementById('panel-resultados');
        const resumen = document.getElementById('resumen-errores');
        const lista = document.getElementById('lista-errores');
        const btn = document.getElementById('btn-corregir');
        
        if (!silent) {
            btn.innerText = "Analizando...";
            btn.disabled = true;
            lista.innerHTML = "";
            panel.style.display = 'block';
        }
        
        try {
            const res = await fetch('/analizar_partitura', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ partitura: this.state.partitura })
            });
            
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            
            const data = await res.json();
            
            if (!Array.isArray(data.errores) || typeof data.mensaje !== 'string') {
                throw new Error("Respuesta del servidor inválida");
            }
            
            this.state.erroresGlobales = data.errores;
            
            if (!silent) {
                this.displayResults(data);
            } else {
                // Actualizar indicador visual sin mostrar panel
                this.updateErrorIndicator(data.errores.length);
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
                btn.innerText = "🔍 Corregir";
                btn.disabled = false;
            }
        }
    },
    
    updateErrorIndicator(errorCount) {
        const btn = document.getElementById('btn-corregir');
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
            // Hay errores: cambiar a modo review automáticamente
            if (this.state.appMode !== 'review') {
                document.body.classList.remove('mode-write');
                document.body.classList.add('mode-review');
                document.getElementById('btn-mode-write').classList.remove('active');
                document.getElementById('btn-mode-review').classList.add('active');
                this.state.appMode = 'review';
            }
            panel.style.display = 'block';
        }
    },
    
    highlightError(index) {
        this.state.errorSeleccionado = this.state.erroresGlobales[index];
        this.state.cursorIndex = this.state.errorSeleccionado.tiempo_index;
        this.renderPartiture();
        
        const sc = document.querySelector('.scroll-partitura');
        const measureIndex = Math.floor(this.state.cursorIndex / 4);
        const scrollPosition = (measureIndex - 1) * 300;
        if(scrollPosition > 0) sc.scrollLeft = scrollPosition;
        
        document.querySelectorAll('.item-error').forEach((el, i) => {
            el.classList.toggle('seleccionado', i === index);
        });
    },
    
    // ===== RENDERIZADO =====
    renderPartiture() {
        try {
            document.getElementById('lienzo-partitura').innerHTML = '';
            
            const VF = Vex.Flow;
            const vf = new VF.Factory({
                renderer: {
                    elementId: 'lienzo-partitura',
                    width: this.config.NUM_COMPASES * 270 + 50,
                    height: 280
                }
            });
            const score = vf.EasyScore();
            
            let xPos = 0;
            let yPos = 30;
            
            for (let c = 0; c < this.config.NUM_COMPASES; c++) {
                const inicio = c * this.config.TIEMPOS;
                const fin = inicio + this.config.TIEMPOS;
                const slice = this.state.partitura.slice(inicio, fin);
                
                const strS = this.generateVoiceString(slice, 'S');
                const strA = this.generateVoiceString(slice, 'A');
                const strT = this.generateVoiceString(slice, 'T');
                const strB = this.generateVoiceString(slice, 'B');
                
                const ns = score.notes(strS, { stem: 'up' });
                const na = score.notes(strA, { stem: 'down' });
                const nt = score.notes(strT, { stem: 'up', clef: 'bass' });
                const nb = score.notes(strB, { stem: 'down', clef: 'bass' });
                
                this.applyCursorStyle(ns, inicio, 'S');
                this.applyCursorStyle(na, inicio);
                this.applyCursorStyle(nt, inicio);
                this.applyCursorStyle(nb, inicio);
                
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
                    st.addClef('treble').addTimeSignature('4/4');
                    sb.addClef('bass').addTimeSignature('4/4');
                    sys.addConnector('brace');
                    sys.addConnector('singleLeft');
                } else {
                    sys.addConnector('singleLeft');
                }
                if (c === this.config.NUM_COMPASES - 1) sys.addConnector('boldDoubleRight');
                
                vf.draw();
                xPos += ancho;
            }
        } catch (e) {
            console.error('Error renderizando:', e);
        }
    },
    
    generateVoiceString(slice, voice) {
        return slice.map((t) => {
            let n = t[voice];
            if(n) return `${n}/q`;
            let silence = (voice==='S')?'a5':(voice==='A')?'f4':(voice==='T')?'a3':'e2';
            if(voice==='T' && t['B'] && (t['B'].includes('3')||t['B'].includes('4'))) silence='c4';
            return `${silence}/q/r`;
        }).join(', ');
    },
    
    applyCursorStyle(noteList, offset, voice) {
        noteList.forEach((n, i) => {
            if ((offset + i) === this.state.cursorIndex) {
                n.setStyle({ fillStyle: "#546de5", strokeStyle: "#546de5" });
                if (voice === 'S') {
                    const VF = Vex.Flow;
                    if(VF.Annotation) {
                        n.addModifier(new VF.Annotation("▼").setFont("Arial",20,3).setVerticalJustification(1));
                    }
                }
            }
        });
    },
    
    applyErrorStyle(noteList, offset, voice, xOffset) {
        noteList.forEach((n, i) => {
            const idxReal = offset + i;
            if (this.state.errorSeleccionado.voces.includes(voice)) {
                if (idxReal === this.state.errorSeleccionado.tiempo_index || 
                    idxReal === this.state.errorSeleccionado.tiempo_index + 1) {
                    n.setStyle({ fillStyle: "#ff0000", strokeStyle: "#ff0000" });
                    if (idxReal === this.state.errorSeleccionado.tiempo_index && 
                        voice === this.state.errorSeleccionado.voces[0]) {
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
    }
};

// Inicialización cuando carga la página
window.addEventListener('load', () => {
    AudioStudio.init();
});

// Wrapper functions para compatibilidad con HTML onclick
function moverCursor(d) { AudioStudio.moveCursor(d); }
function seleccionarVoz(v) { AudioStudio.selectVoice(v); }
function cambiarOctava(d) { AudioStudio.changeOctave(d); }
function tocarBlanca(n) { AudioStudio.playWhiteKey(n); }
function tocarDoAgudo() { AudioStudio.playHighC(); }
function tocarNegra(n, next) { AudioStudio.playBlackKey(n); }
function analizarPartitura() { AudioStudio.analyzePartiture(); }
function borrarTodo() { AudioStudio.clearAll(); }
