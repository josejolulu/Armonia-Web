"""
Nueva función bridge para integrar harmonic_rules con app.py
Reemplaza _analizar_quintas_octavas() progresivamente
"""

def _analizar_conduccion_voces_nuevo(acorde_act, acorde_sig, n_compas, idx_tiempo_actual, errores):
    """
    Detecta errores de conducción usando el motor de reglas armónicas.
    
    Esta función reemplaza parcialmente _analizar_quintas_octavas()
    con el nuevo motor robusto que incluye excepciones.
    
    Args:
        acorde_act: Dict de {voz: music21.Pitch}
        acorde_sig: Dict de {voz: music21.Pitch}
        n_compas: Número de compás
        idx_tiempo_actual: Índice global del tiempo
        errores: Lista donde añadir errores detectados
    """
    global harmonic_engine
    
    if not harmonic_engine:
        logger.warning("Harmonic engine no inicializado")
        return
    
    # Convertir acordes de music21.Pitch a formato string para el motor
    try:
        chord1 = {v: p.nameWithOctave for v, p in acorde_act.items() if p is not None}
        chord2 = {v: p.nameWithOctave for v, p in acorde_sig.items() if p is not None}
        
        # Verificar que ambos acordes tienen suficientes notas
        if len(chord1) < 2 or len(chord2) < 2:
            return
        
        # Contexto mínimo (tonalidad del motor)
        context = {
            'key': f"{harmonic_engine.key} {harmonic_engine.mode}"
        }
        
        # TODO Fase 2: Enriquecer con análisis funcional
        # if analisis_actual and analisis_siguiente:
        #     chord1.update({
        #         'degree_num': analisis_actual.get('grado_num'),
        #         'function': analisis_actual.get('funcion'),
        #         ...
        #     })
        
        # Validar con motor
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


# Añadir esta función a app.py antes de _analizar_quintas_octavas
