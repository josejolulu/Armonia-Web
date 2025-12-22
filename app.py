from flask import Flask, render_template, request, jsonify
import music21
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def pagina_inicio():
    return render_template('index.html')

# --- UTILIDADES ---
def obtener_nota_music21(nota_str):
    """Convierte string de nota a objeto music21.Pitch con validación"""
    if not nota_str:
        return None
    if not isinstance(nota_str, str):
        raise ValueError(f"Nota debe ser string, recibió: {type(nota_str)}")
    
    try:
        nota_normalizada = nota_str.replace('b', '-')
        return music21.pitch.Pitch(nota_normalizada)
    except Exception as e:
        raise ValueError(f"Nota inválida '{nota_str}': {str(e)}")

def crear_error(compas, tiempo_global, voces_implicadas, mensaje):
    """Crea objeto de error estructurado"""
    if not isinstance(voces_implicadas, list) or not voces_implicadas:
        voces_implicadas = []
    
    t_compas = (tiempo_global % 4) + 1
    return {
        'id': f"err-{tiempo_global}",
        'mensaje': f"Compás {compas}, T{t_compas}: {mensaje}",
        'mensaje_corto': mensaje,
        'tiempo_index': tiempo_global,
        'voces': voces_implicadas
    }

# --- MOTOR DE ANÁLISIS ---
def analizar_par_acordes(n_compas, n_tiempo, notas_actual, notas_siguiente, idx_tiempo_actual):
    """Analiza dos acordes consecutivos aplicando todas las reglas de armonía"""
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
        
        # A. VERTICAL (Cruces y Disposición)
        for i in range(3):
            v_inf, v_sup = voces_ordenadas[i], voces_ordenadas[i+1]
            if acorde_act[v_inf].ps > acorde_act[v_sup].ps:
                errores.append(crear_error(n_compas, idx_tiempo_actual, [v_inf, v_sup], 
                    f"Cruce: {nombres[v_inf]} sobre {nombres[v_sup]}"))
        
        # Verificar disposición (espacios máximos entre voces)
        if abs(acorde_act['A'].ps - acorde_act['T'].ps) > 12:
            errores.append(crear_error(n_compas, idx_tiempo_actual, ['T', 'A'], 
                "Disposición > 8ª (Tenor-Contralto)"))
        if abs(acorde_act['S'].ps - acorde_act['A'].ps) > 12:
            errores.append(crear_error(n_compas, idx_tiempo_actual, ['A', 'S'], 
                "Disposición > 8ª (Contralto-Soprano)"))
        
        # B. HORIZONTAL (Requiere segundo acorde)
        if any(n is None for n in acorde_sig.values()):
            return errores
        
        # Detectar quintas y octavas paralelas/directas
        _analizar_quintas_octavas(acorde_act, acorde_sig, voces_ordenadas, 
                                   nombres, n_compas, idx_tiempo_actual, errores)
        
        # Analizar resolución de séptimas
        _analizar_septimas(acorde_act, acorde_sig, voces_ordenadas, nombres, 
                          n_compas, idx_tiempo_actual, errores)
        
        # Detectar invasiones (cruces de voces entre acordes)
        for i in range(3):
            v_inf, v_sup = voces_ordenadas[i], voces_ordenadas[i+1]
            if acorde_sig[v_sup].ps < acorde_act[v_inf].ps:
                errores.append(crear_error(n_compas, idx_tiempo_actual, [v_inf, v_sup], 
                    f"Invasión: {nombres[v_sup]} baja más que {nombres[v_inf]}"))
            if acorde_sig[v_inf].ps > acorde_act[v_sup].ps:
                errores.append(crear_error(n_compas, idx_tiempo_actual, [v_inf, v_sup], 
                    f"Invasión: {nombres[v_inf]} sube más que {nombres[v_sup]}"))
    
    except Exception as e:
        logger.warning(f"Error analizando compás {n_compas}: {str(e)}")
    
    return errores


def _analizar_quintas_octavas(acorde_act, acorde_sig, voces_ordenadas, nombres, 
                               n_compas, idx_tiempo_actual, errores):
    """Detecta quintas y octavas paralelas/directas"""
    pares = [('B','T'), ('B','A'), ('B','S'), ('T','A'), ('T','S'), ('A','S')]
    
    for v1, v2 in pares:
        n1_a, n2_a = acorde_act[v1], acorde_act[v2]
        n1_b, n2_b = acorde_sig[v1], acorde_sig[v2]
        
        # Determinar intervalos
        low_a, high_a = (n1_a, n2_a) if n1_a.ps < n2_a.ps else (n2_a, n1_a)
        int_a = music21.interval.Interval(low_a, high_a)
        low_b, high_b = (n1_b, n2_b) if n1_b.ps < n2_b.ps else (n2_b, n1_b)
        int_b = music21.interval.Interval(low_b, high_b)
        
        es_quinta = (int_a.semiSimpleName == 'P5' and int_b.semiSimpleName == 'P5')
        es_octava = (int_a.semiSimpleName in ['P1','P8'] and int_b.semiSimpleName in ['P1','P8'])
        
        if es_quinta or es_octava:
            mov_v1 = n1_b.ps - n1_a.ps
            mov_v2 = n2_b.ps - n2_a.ps
            
            # Solo reportar si ambas voces se mueven
            if mov_v1 != 0 and mov_v2 != 0:
                mismo_movimiento = (mov_v1 > 0 and mov_v2 > 0) or (mov_v1 < 0 and mov_v2 < 0)
                
                if mismo_movimiento:
                    tipo = "Quintas" if es_quinta else "Octavas"
                    
                    # Quintas/Octavas paralelas (mismo tipo de intervalo)
                    if int_a.semiSimpleName == int_b.semiSimpleName:
                        errores.append(crear_error(n_compas, idx_tiempo_actual, [v1, v2], 
                            f"{tipo} Paralelas ({nombres[v1]}-{nombres[v2]})"))
                    
                    # Quintas/Octavas directas (solo en voces externas si soprano salta)
                    elif v1 == 'B' and v2 == 'S' and abs(n2_b.ps - n2_a.ps) > 2:
                        errores.append(crear_error(n_compas, idx_tiempo_actual, [v1, v2], 
                            f"{tipo} Directas (Soprano salta)"))


def _analizar_septimas(acorde_act, acorde_sig, voces_ordenadas, nombres, 
                       n_compas, idx_tiempo_actual, errores):
    """Verifica que las séptimas se resuelvan correctamente"""
    try:
        chord_m21 = music21.chord.Chord([acorde_act[v] for v in voces_ordenadas])
        
        if chord_m21.seventh:
            nom_7 = chord_m21.seventh.nameWithOctave
            v_7 = next((v for v in voces_ordenadas if acorde_act[v].nameWithOctave == nom_7), None)
            
            if v_7:
                diff = acorde_sig[v_7].ps - acorde_act[v_7].ps
                
                # Séptima debe bajar 1 o 2 semitonos
                if diff >= 0:
                    errores.append(crear_error(n_compas, idx_tiempo_actual, [v_7], 
                        f"Séptima en {nombres[v_7]} no resuelve"))
                elif diff < -2:
                    errores.append(crear_error(n_compas, idx_tiempo_actual, [v_7], 
                        f"Séptima en {nombres[v_7]} salta"))
    except Exception as e:
        logger.debug(f"No se pudo analizar séptima: {str(e)}")

@app.route('/analizar_partitura', methods=['POST'])
def analizar_partitura():
    """Endpoint para analizar una partitura completa"""
    try:
        # Validación de entrada
        datos = request.get_json()
        if not datos:
            return jsonify({'errores': [], 'mensaje': 'Error: datos vacíos'}), 400
        
        partitura = datos.get('partitura', [])
        
        # Validar formato de partitura
        if not isinstance(partitura, list) or len(partitura) == 0:
            return jsonify({'errores': [], 'mensaje': 'Error: partitura inválida'}), 400
        
        # Validar cada tiempo
        for i, tiempo in enumerate(partitura):
            if not isinstance(tiempo, dict) or not all(k in ['S', 'A', 'T', 'B'] for k in tiempo.keys()):
                return jsonify({'errores': [], 'mensaje': f'Error: tiempo {i} con formato inválido'}), 400
        
        # Analizar pares de acordes consecutivos
        errores = []
        for i in range(len(partitura) - 1):
            if any(partitura[i].values()) and any(partitura[i+1].values()):
                try:
                    errores.extend(analizar_par_acordes(
                        (i//4)+1,           # número de compás
                        (i%4)+1,            # tiempo dentro del compás
                        partitura[i], 
                        partitura[i+1], 
                        i                   # índice global
                    ))
                except Exception as e:
                    logger.error(f"Error analizando compás {(i//4)+1}: {str(e)}")
                    return jsonify({'errores': [], 'mensaje': f'Error: {str(e)}'}), 500
        
        # Analizar último acorde (sin siguiente)
        ult = len(partitura) - 1
        if any(partitura[ult].values()):
            try:
                errores.extend(analizar_par_acordes(
                    (ult//4)+1, 
                    (ult%4)+1, 
                    partitura[ult], 
                    {}, 
                    ult
                ))
            except Exception as e:
                logger.error(f"Error analizando último acorde: {str(e)}")
                return jsonify({'errores': [], 'mensaje': f'Error: {str(e)}'}), 500
        
        # Generar respuesta
        msg = "✅ Ejercicio Correcto" if not errores else f"⚠️ {len(errores)} errores encontrados"
        return jsonify({
            'errores': errores, 
            'mensaje': msg,
            'success': len(errores) == 0
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