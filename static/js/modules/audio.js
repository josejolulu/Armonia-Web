/* module: audio.js
   Módulo aislado para la generación de sonido con Tone.js
*/

const AudioEngine = {
    synth: null,
    isReady: false,
    isPlaying: false,
    sequence: null,


    // Inicialización segura (idempotente)
    async init() {
        if (this.isReady) return;

        try {
            await Tone.start();
            if (Tone.context.state !== 'running') {
                await Tone.context.resume();
            }

            // Sintetizador polifónico suave con reverb
            this.synth = new Tone.PolySynth(Tone.Synth, {
                oscillator: {
                    type: "triangle" // Sonido suave tipo órgano/flauta
                },
                envelope: {
                    attack: 0.05,
                    decay: 0.1,
                    sustain: 0.3,
                    release: 1
                }
            }).toDestination();

            // Bajar volumen general para no saturar
            this.synth.volume.value = -10;

            this.isReady = true;
            console.log('🔊 AudioEngine inicializado');
        } catch (e) {
            console.error('Error inicializando AudioEngine:', e);
        }
    },

    // Reproduce una nota (ej: "C4", "F#3")
    async playNote(note, duration = "8n") {
        // Auto-inicializar si es la primera interacción
        if (!this.isReady) await this.init();

        if (!this.synth) return;

        try {
            // Tone.js espera "C4", VexFlow a veces usa "C/4". Aseguramos formato.
            const cleanNote = note.replace('/', '');
            this.synth.triggerAttackRelease(cleanNote, duration);
        } catch (e) {
            console.warn(`Error reproduciendo nota ${note}:`, e);
        }
    },

    // Reproduce un acorde (array de notas)
    async playChord(notes, duration = "4n") {
        if (!this.isReady) await this.init();
        if (!this.synth) return;
        this.synth.triggerAttackRelease(notes, duration);
    },

    // Reproducción de Partitura Completa (con Transport)
    // @param {Array} partitura - Array de tiempos con notas
    // @param {number} bpm - Tempo en beats por minuto
    // @param {Function} onProgress - Callback llamado en cada tiempo (recibe index)
    async playScore(partitura, bpm = 120, onProgress = null) {
        if (!this.isReady) await this.init();
        await Tone.start();

        // Detener previo
        this.stop();

        Tone.Transport.bpm.value = bpm;

        // Mapear eventos con índice para el callback
        const events = partitura.map((tiempo, index) => {
            const notas = [];
            if (tiempo.S) notas.push(tiempo.S.replace('/', ''));
            if (tiempo.A) notas.push(tiempo.A.replace('/', ''));
            if (tiempo.T) notas.push(tiempo.T.replace('/', ''));
            if (tiempo.B) notas.push(tiempo.B.replace('/', ''));
            return { time: `0:${index}`, notes: notas, index: index };
        });

        // Crear Part con callback de progreso
        this.sequence = new Tone.Part((time, value) => {
            if (this.synth) this.synth.triggerAttackRelease(value.notes, "4n", time);

            // Llamar callback de progreso en el hilo principal (via Draw)
            if (onProgress && typeof onProgress === 'function') {
                Tone.Draw.schedule(() => {
                    onProgress(value.index);
                }, time);
            }
        }, events).start(0);

        this.sequence.loop = false;

        // Auto-stop al final
        Tone.Transport.scheduleOnce(() => {
            this.stop();
            // Notificar fin de reproducción
            if (onProgress) {
                Tone.Draw.schedule(() => {
                    onProgress(-1); // -1 indica fin
                }, Tone.now());
            }
        }, `0:${partitura.length}`);

        Tone.Transport.start();
        this.isPlaying = true;
    },

    pause() {
        if (!this.isReady) return;

        if (Tone.Transport.state === 'started') {
            Tone.Transport.pause();
            this.isPlaying = false;
            // Liberar notas colgadas
            if (this.synth) this.synth.releaseAll();
        } else if (Tone.Transport.state === 'paused') {
            Tone.Transport.start();
            this.isPlaying = true;
        }
    },

    stop() {
        if (!this.isReady) return;

        try {
            Tone.Transport.stop();
            Tone.Transport.cancel(); // Cancelar eventos futuros

            if (this.sequence) {
                this.sequence.dispose();
                this.sequence = null;
            }

            if (this.synth) this.synth.releaseAll();
            this.isPlaying = false;
        } catch (e) {
            console.error("Error al detener audio:", e);
        }
    }
};

export default AudioEngine;
