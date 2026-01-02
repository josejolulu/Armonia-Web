/* module: state.js
   Gestión centralizada del estado de la aplicación
   Separación de datos y lógica de control.
*/

const AppState = {
    // Configuración Inmutable
    config: {
        NUM_COMPASES: 4,
        TIEMPOS: 4,
        STORAGE_KEY: 'armonia_partitura',
        HISTORY_MAX: 20,
        VALIDATION_DEBOUNCE: 1000
    },

    // Estado Reactivo (Data)
    data: {
        partitura: [],
        cursorIndex: 0,
        vozActiva: 'B',
        octavaBase: 3,
        modoAlteracion: 'n',
        errorSeleccionado: null,
        erroresGlobales: [],
        analisisFuncional: [],
        history: [],
        historyIndex: -1,
        validationDebounceTimer: null,
        lastAnalysisTime: 0,
        inputMode: 'piano',
        appMode: 'write',
        tonalidad: {
            tonica: 'C',
            modo: 'major'
        },
        // Auto-scroll control
        touchActive: false,
        touchDebounceTimer: null,
        // Posiciones X de notas para scroll inteligente
        notePositionsX: []
    },

    // Inicialización del estado
    init() {
        this.config.TOTAL = this.config.NUM_COMPASES * this.config.TIEMPOS;
        this.initializePartitura();
        this.loadFromStorage();
    },

    initializePartitura() {
        this.data.partitura = [];
        for (let i = 0; i < this.config.TOTAL; i++) {
            this.data.partitura.push({ 'S': null, 'A': null, 'T': null, 'B': null });
        }
        this._resetHistory();
    },

    _resetHistory() {
        this.data.history = [JSON.parse(JSON.stringify(this.data.partitura))];
        this.data.historyIndex = 0;
    },

    // ===== PERSISTENCIA =====
    saveToStorage() {
        try {
            localStorage.setItem(this.config.STORAGE_KEY, JSON.stringify(this.data.partitura));
        } catch (e) {
            console.warn('LocalStorage no disponible:', e);
        }
    },

    loadFromStorage() {
        try {
            const saved = localStorage.getItem(this.config.STORAGE_KEY);
            if (saved) {
                this.data.partitura = JSON.parse(saved);
                this._resetHistory();
                console.log('✅ Partitura recuperada de almacenamiento (State)');
            }
        } catch (e) {
            console.warn('Error al cargar partitura:', e);
        }
    },

    // ===== GESTIÓN DE HISTORIAL =====
    pushToHistory() {
        // Cortar historial si estamos en el medio
        if (this.data.historyIndex < this.data.history.length - 1) {
            this.data.history = this.data.history.slice(0, this.data.historyIndex + 1);
        }
        // Añadir nuevo estado
        this.data.history.push(JSON.parse(JSON.stringify(this.data.partitura)));

        // Limitar tamaño
        if (this.data.history.length > this.config.HISTORY_MAX) {
            this.data.history.shift();
        } else {
            this.data.historyIndex++;
        }
    },

    undo() {
        if (this.data.historyIndex > 0) {
            this.data.historyIndex--;
            this.data.partitura = JSON.parse(JSON.stringify(this.data.history[this.data.historyIndex]));
            this.data.errorSeleccionado = null;
            this.saveToStorage();
            return true; // Indica éxito
        }
        return false;
    },

    redo() {
        if (this.data.historyIndex < this.data.history.length - 1) {
            this.data.historyIndex++;
            this.data.partitura = JSON.parse(JSON.stringify(this.data.history[this.data.historyIndex]));
            this.data.errorSeleccionado = null;
            this.saveToStorage();
            return true;
        }
        return false;
    },

    canUndo() {
        return this.data.historyIndex > 0;
    },

    canRedo() {
        return this.data.historyIndex < this.data.history.length - 1;
    },

    // ===== ACCIONES DE ESTADO (Getters/Setters) =====
    updateNote(index, voice, note) {
        if (index >= 0 && index < this.config.TOTAL) {
            this.data.partitura[index][voice] = note;
            this.saveToStorage();
            this.pushToHistory();
        }
    },

    clearAll() {
        this.data.partitura.forEach(p => {
            p.S = null; p.A = null; p.T = null; p.B = null;
        });
        this.data.cursorIndex = 0;
        this.data.errorSeleccionado = null;
        this.pushToHistory();
        this.saveToStorage();
    },

    setTonalidad(tonica, modo) {
        this.data.tonalidad = { tonica, modo };
        // La tonalidad no se guarda en localStorage actualmente, pero podría
    }
};

export default AppState;
