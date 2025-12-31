from flask import Flask, render_template, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# OPTIMIZACIÓN RAM: Lazy Loading de Dependencias Pesadas
# ============================================================================
# music21 consume ~180-220 MB. Cargarla solo cuando se necesita
# reduce el consumo base de memoria, crítico para Render Free (512 MB)
# ============================================================================

_music21_loaded = False
_analizador_loaded = False

def _lazy_load_music21():
    """Carga music21 solo la primera vez que se necesita"""
    global _music21_loaded
    if not _music21_loaded:
        global music21
        import music21 as m21
        music21 = m21
        _music21_loaded = True
        logger.info("music21 cargado (lazy loading)")

def _lazy_load_analizador():
    """Carga módulos de análisis solo cuando se necesitan"""
    global _analizador_loaded
    if not _analizador_loaded:
        global CerebroTonal, crear_cerebro_tonal, RulesEngine
        from analizador_tonal import CerebroTonal, crear_cerebro_tonal
        from harmonic_rules import RulesEngine
        _analizador_loaded = True
        logger.info("Módulos de análisis cargados (lazy loading)")

# Instancia global del Cerebro Tonal (se configura por request)
cerebro_tonal = None

# Motor de reglas armónicas (se configura por request)
harmonic_engine = None

@app.route('/')
def pagina_inicio():
    return render_template('index.html')

# --- UTILIDADES ---
def obtener_nota_music21(nota_str):
    """Convierte string de nota a objeto music21.Pitch con validación"""
    _lazy_load_music21()  # Cargar music21 si aún no está cargado
    
    if not nota_str:
        return None
    if not isinstance(nota_str, str):
        raise ValueError(f"Nota debe ser string, recibió: {type(nota_str)}")
    
    try:
        nota_normalizada = nota_str.replace('b', '-')
        return music21.pitch.Pitch(nota_normalizada)
    except Exception as e:
        raise ValueError(f"Nota inválida '{nota_str}': {str(e)}")

def crear_error(compas, tiempo_global, voces_implicadas, mensaje, color='#FF0000'):
    """Crea objeto de error estructurado"""
    if not isinstance(voces_implicadas, list) or not voces_implicadas:
        voces_implicadas = []
    
    t_compas = (tiempo_global % 4) + 1
    return {
        'id': f"err-{tiempo_global}",
        'mensaje': f"Compás {compas}, T{t_compas}: {mensaje}",
        'mensaje_corto': mensaje,
        'tiempo_index': tiempo_global,
        'voces': voces_implicadas,
        'color': color  # Color del error (RED por defecto para legacy)
    }

# --- MOTOR DE ANÁLISIS ---
def analizar_par_acordes(n_compas, n_tiempo, notas_actual, notas_siguiente, idx_tiempo_actual, analisis_actual=None, analisis_siguiente=None):
    """Analiza dos acordes consecutivos aplicando todas las reglas de armonía
    
    Args:
        analisis_actual: Dict opcional con análisis funcional del acorde actual (desde analizador_tonal)
        analisis_siguiente: Dict opcional con análisis funcional del acorde siguiente
    """
    errores = []
    nombres = {'S': 'Soprano', 'A': 'Contralto', 'T': 'Tenor', 'B': 'Bajo'}
    voces_ordenadas = ['B', 'T', 'A', 'S']
    
    try:
        # 1. Convertir notas a objetos music21
        acorde_act = {v: obtener_nota_music21(notas_actual.get(v)) for v in voces_ordenadas}
        acorde_sig = {v: obtener_nota_music21(notas_siguiente.get(v)) for v in voces_ordenadas}
        
        # Si falta alguna nota en el acorde actual, no analizar
        if any(n is None for n in acorde_act.values()):
            return []
        
        # A. VERTICAL - Ahora manejado por motor (VoiceCrossingRule, MaximumDistanceRule)
        
        
        # B. HORIZONTAL (Requiere segundo acorde)
        if any(n is None for n in acorde_sig.values()):
            return errores
        
        # Detectar consonancias perfectas con motor robusto (incluye excepciones)
        # Motor nuevo detecta: Quintas y Octavas (paralelas/consecutivas)
        _analizar_conduccion_voces(acorde_act, acorde_sig, n_compas, idx_tiempo_actual, errores, analisis_actual, analisis_siguiente)
        
        # NOTA: _analizar_septimas fue ELIMINADO
        # La resolución de séptimas ya está cubierta por SeventhResolutionRule en el motor
        
        # Invasiones ahora manejadas por motor (VoiceOverlapRule)
    
    except Exception as e:
        logger.warning(f"Error analizando compás {n_compas}: {str(e)}")
    
    return errores


def _analizar_conduccion_voces(acorde_act, acorde_sig, n_compas, idx_tiempo_actual, errores, analisis_actual=None, analisis_siguiente=None):
    """
    Detecta errores de conducción usando el motor de reglas armónicas.
    
    Esta función integra el nuevo motor robusto que incluye excepciones
    (V-VII, cambio de disposición, etc.) con el sistema existente.
    
    Args (nuevos):
        analisis_actual: Dict opcional con análisis funcional del acorde actual
        analisis_siguiente: Dict opcional con análisis funcional del acorde siguiente
    
    Args:
        acorde_act: Dict de {voz: music21.Pitch}
        acorde_sig: Dict de {voz: music21.Pitch}
        n_compas: Número de compás
        idx_tiempo_actual: Índice global del tiempo
        errores: Lista donde añadir errores detectados
    """
    global harmonic_engine
    
    if not harmonic_engine:
        logger.warning("Harmonic engine no inicializado, usando detección básica")
        return
    
    try:
        # Convertir acordes de music21.Pitch a formato string para el motor
        chord1 = {v: p.nameWithOctave for v, p in acorde_act.items() if p is not None}
        chord2 = {v: p.nameWithOctave for v, p in acorde_sig.items() if p is not None}
        
        # Verificar que ambos acordes tienen suficientes notas
        if len(chord1) < 2 or len(chord2) < 2:
            return
        
        # Contexto mínimo (tonalidad del motor)
        key_str = f"{harmonic_engine.key} {harmonic_engine.mode}"
        context = {
            'key': key_str
        }
        
        # FASE 2: Enriquecer con análisis funcional (IMPLEMENTADO)
        if analisis_actual:
            chord1.update({
                'root': analisis_actual.get('fundamental'),  # Fundamental del acorde (ej: 'G' en V)
                'degree': analisis_actual.get('grado'),      # Grado romano (ej: 'V', 'I')
                'quality': analisis_actual.get('tipo'),      # Calidad (ej: 'major', 'minor')
                'inversion': analisis_actual.get('inversion'),  # Estado (0, 1, 2)
                'degree_num': analisis_actual.get('grado_num'),  # Número (1-7)
                'key': key_str  # AÑADIDO: Key para LeadingToneResolutionRule
            })
        else:
            # Añadir key incluso si no hay análisis funcional
            chord1['key'] = key_str
        
        if analisis_siguiente:
            chord2.update({
                'root': analisis_siguiente.get('fundamental'),
                'degree': analisis_siguiente.get('grado'),
                'quality': analisis_siguiente.get('tipo'),
                'inversion': analisis_siguiente.get('inversion'),
                'degree_num': analisis_siguiente.get('grado_num'),
                'key': key_str  # AÑADIDO: Key para LeadingToneResolutionRule
            })
        else:
            # Añadir key incluso si no hay análisis funcional
            chord2['key'] = key_str
        
        # Validar con motor de reglas
        detected_errors = harmonic_engine.validate_progression(chord1, chord2, context)
        
        # Formatear y añadir a lista de errores de app.py
        if detected_errors:
            formatted = harmonic_engine.format_errors_for_app(
                detected_errors,
                n_compas,
                idx_tiempo_actual
            )
            errores.extend(formatted)
            logger.debug(f"Motor detectó {len(detected_errors)} errores en compás {n_compas}")
    
    except Exception as e:
        logger.error(f"Error en motor de reglas armónicas: {e}")
        # No propagar el error, continuar con análisis




@app.route('/analizar_partitura', methods=['POST'])
def analizar_partitura():
    """Endpoint para analizar una partitura completa"""
    global cerebro_tonal
    
    # OPTIMIZACIÓN: Cargar módulos pesados solo cuando se necesitan
    _lazy_load_music21()
    _lazy_load_analizador()
    
    try:
        # Validación de entrada
        datos = request.get_json()
        if not datos:
            return jsonify({'errores': [], 'mensaje': 'Error: datos vacíos'}), 400
        
        partitura = datos.get('partitura', [])
        tonalidad = datos.get('tonalidad', {'tonica': 'C', 'modo': 'major'})
        
        # Inicializar/actualizar el Cerebro Tonal con la tonalidad
        cerebro_tonal = crear_cerebro_tonal(tonalidad['tonica'], tonalidad['modo'])
        logger.info(f"Analizando en tonalidad: {tonalidad['tonica']} {tonalidad['modo']}")
        
        # Inicializar motor de reglas armónicas
        global harmonic_engine
        harmonic_engine = RulesEngine(key=tonalidad['tonica'], mode=tonalidad['modo'])
        logger.info(f"Motor de reglas armónicas inicializado")
        
        # Validar formato de partitura
        if not isinstance(partitura, list) or len(partitura) == 0:
            return jsonify({'errores': [], 'mensaje': 'Error: partitura inválida'}), 400
        
        # Validar cada tiempo
        for i, tiempo in enumerate(partitura):
            if not isinstance(tiempo, dict) or not all(k in ['S', 'A', 'T', 'B'] for k in tiempo.keys()):
                return jsonify({'errores': [], 'mensaje': f'Error: tiempo {i} con formato inválido'}), 400
        
        # ===== ANÁLISIS FUNCIONAL (FASE 2.1) =====
        analisis_acordes = []
        for i, tiempo in enumerate(partitura):
            if any(tiempo.values()):
                analisis = cerebro_tonal.analizar_acorde(tiempo)
                analisis['tiempo_index'] = i
                analisis['compas'] = (i // 4) + 1
                analisis['tiempo'] = (i % 4) + 1
                analisis_acordes.append(analisis)
        
        # ===== ANÁLISIS DE CONDUCCIÓN DE VOCES =====
        errores = []
        for i in range(len(partitura) - 1):
            if any(partitura[i].values()) and any(partitura[i+1].values()):
                try:
                    # Buscar análisis funcional correspondientes
                    analisis_act = next((a for a in analisis_acordes if a['tiempo_index'] == i), None)
                    analisis_sig = next((a for a in analisis_acordes if a['tiempo_index'] == i+1), None)
                    
                    errores.extend(analizar_par_acordes(
                        (i//4)+1,           # número de compás
                        (i%4)+1,            # tiempo dentro del compás
                        partitura[i], 
                        partitura[i+1], 
                        i,                   # índice global
                        analisis_act,        # análisis funcional actual
                        analisis_sig         # análisis funcional siguiente
                    ))
                except Exception as e:
                    logger.error(f"Error analizando compás {(i//4)+1}: {str(e)}")
                    return jsonify({'errores': [], 'mensaje': f'Error: {str(e)}'}), 500
        
        # Analizar último acorde (sin siguiente)
        ult = len(partitura) - 1
        if any(partitura[ult].values()):
            try:
                analisis_ult = next((a for a in analisis_acordes if a['tiempo_index'] == ult), None)
                
                errores.extend(analizar_par_acordes(
                    (ult//4)+1, 
                    (ult%4)+1, 
                    partitura[ult], 
                    {}, 
                    ult,
                    analisis_ult,  # análisis funcional del último acorde
                    None           # no hay siguiente
                ))
            except Exception as e:
                logger.error(f"Error analizando último acorde: {str(e)}")
                return jsonify({'errores': [], 'mensaje': f'Error: {str(e)}'}), 500
        
        # Generar respuesta con análisis funcional
        msg = "✅ Ejercicio Correcto" if not errores else f"⚠️ {len(errores)} errores encontrados"
        
        logger.info(f"Enviando respuesta con {len(analisis_acordes)} grados analizados")
        
        return jsonify({
            'errores': errores, 
            'mensaje': msg,
            'success': len(errores) == 0,
            'analisis_funcional': analisis_acordes,
            'tonalidad': tonalidad
        }), 200
        
    except Exception as e:
        logger.error(f"Error en /analizar_partitura: {str(e)}")
        return jsonify({
            'errores': [], 
            'mensaje': f'Error de servidor: {str(e)}'
        }), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Ruta no encontrada'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Error del servidor: {str(e)}")
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)