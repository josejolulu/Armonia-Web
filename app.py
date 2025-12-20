from flask import Flask, render_template, request, jsonify
import music21

app = Flask(__name__)

@app.route('/')
def pagina_inicio():
    return render_template('index.html')

# =========================================================
# 🛠️ UTILIDADES
# =========================================================

def obtener_nota(nota_str):
    """Convierte string a objeto Pitch de forma segura"""
    if not nota_str: return None
    try:
        # Limpieza crucial: music21 usa '-' para bemol, no 'b'
        return music21.pitch.Pitch(nota_str.replace('b', '-'))
    except:
        return None

def fmt_err(compas, tiempo, mensaje):
    """Formato estándar de error"""
    return {
        'id': f"err-c{compas}-t{tiempo}-{mensaje[:3]}",
        'mensaje': f"Compás {compas}, T{tiempo}: {mensaje}",
        'mensaje_corto': mensaje,
        'tiempo_index': (compas - 1) * 4 + (tiempo - 1),
        'voces': [] # Se rellenará en cada regla
    }

# =========================================================
# ⚖️ LOS 5 JUECES (Funciones Independientes)
# =========================================================

def juez_vertical(acorde, compas, tiempo, idx_global):
    """Revisa Cruces y Disposición en un solo acorde"""
    errores = []
    voces = ['B', 'T', 'A', 'S']
    nombres = {'B':'Bajo', 'T':'Tenor', 'A':'Contralto', 'S':'Soprano'}
    
    # 1. CRUCES (Voz inferior supera a superior)
    for i in range(3):
        v_inf, v_sup = voces[i], voces[i+1]
        n_inf, n_sup = acorde[v_inf], acorde[v_sup]
        
        if n_inf and n_sup:
            if n_inf.ps > n_sup.ps:
                err = fmt_err(compas, tiempo, f"Cruce: {nombres[v_inf]} sobre {nombres[v_sup]}")
                err['voces'] = [v_inf, v_sup]
                errores.append(err)

    # 2. DISPOSICIÓN (Huecos > 8va)
    # Tenor-Alto
    if acorde['T'] and acorde['A']:
        if (acorde['A'].ps - acorde['T'].ps) > 12:
            err = fmt_err(compas, tiempo, "Disposición > 8ª (Tenor-Contralto)")
            err['voces'] = ['T', 'A']
            errores.append(err)
            
    # Alto-Soprano
    if acorde['A'] and acorde['S']:
        if (acorde['S'].ps - acorde['A'].ps) > 12:
            err = fmt_err(compas, tiempo, "Disposición > 8ª (Contralto-Soprano)")
            err['voces'] = ['A', 'S']
            errores.append(err)

    return errores

def juez_horizontal(acorde_act, acorde_sig, compas, tiempo, idx_global):
    """Revisa el enlace entre dos acordes (Paralelas, Directas, Invasión, 7as)"""
    errores = []
    voces = ['B', 'T', 'A', 'S']
    nombres = {'B':'Bajo', 'T':'Tenor', 'A':'Contralto', 'S':'Soprano'}

    # Si falta alguna nota clave en el enlace, saltamos para no dar falsos errores
    # (Aunque lo ideal es analizar lo que haya, por ahora somos estrictos)
    
    # A. QUINTAS Y OCTAVAS (Paralelas y Directas)
    pares = [('B','T'), ('B','A'), ('B','S'), ('T','A'), ('T','S'), ('A','S')]
    
    for v1, v2 in pares:
        n1_a, n2_a = acorde_act[v1], acorde_act[v2]
        n1_b, n2_b = acorde_sig[v1], acorde_sig[v2]

        if not (n1_a and n2_a and n1_b and n2_b): continue

        # Intervalos (siempre low a high)
        i_a = music21.interval.Interval(min(n1_a, n2_a), max(n1_a, n2_a))
        i_b = music21.interval.Interval(min(n1_b, n2_b), max(n1_b, n2_b))

        tipo_a = i_a.semiSimpleName # P5, P8...
        tipo_b = i_b.semiSimpleName

        es_destino_perf = (tipo_b in ['P5', 'P1', 'P8'])
        
        if es_destino_perf:
            # Movimiento de las voces
            mov_v1 = n1_b.ps - n1_a.ps
            mov_v2 = n2_b.ps - n2_a.ps
            
            # Si hay movimiento directo (mismo signo y no oblicuo)
            if mov_v1 != 0 and mov_v2 != 0:
                if (mov_v1 > 0 and mov_v2 > 0) or (mov_v1 < 0 and mov_v2 < 0):
                    
                    nombre_int = "Quintas" if tipo_b == 'P5' else "Octavas"
                    
                    # 1. PARALELAS (Origen igual a destino)
                    if tipo_a == tipo_b:
                        err = fmt_err(compas, tiempo, f"{nombre_int} Paralelas ({nombres[v1]}-{nombres[v2]})")
                        err['voces'] = [v1, v2]
                        errores.append(err)
                    
                    # 2. DIRECTAS (Solo Baj-Sop y Soprano salta)
                    elif v1 == 'B' and v2 == 'S':
                        salto_sop = abs(n2_b.ps - n2_a.ps)
                        if salto_sop > 2:
                            err = fmt_err(compas, tiempo, f"{nombre_int} Directas (Soprano salta)")
                            err['voces'] = ['B', 'S']
                            errores.append(err)

    # B. INVASIÓN DE ÁMBITO (Overlap)
    # Comparamos voces adyacentes
    for i in range(3):
        v_inf, v_sup = voces[i], voces[i+1]
        ni_a, ns_a = acorde_act[v_inf], acorde_act[v_sup]
        ni_b, ns_b = acorde_sig[v_inf], acorde_sig[v_sup]

        if ni_a and ns_a and ni_b and ns_b:
            # Descendente: Sup nueva < Inf vieja
            if ns_b.ps < ni_a.ps:
                err = fmt_err(compas, tiempo, f"Invasión: {nombres[v_sup]} baja más que {nombres[v_inf]}")
                err['voces'] = [v_inf, v_sup]
                errores.append(err)
            # Ascendente: Inf nueva > Sup vieja
            if ni_b.ps > ns_a.ps:
                err = fmt_err(compas, tiempo, f"Invasión: {nombres[v_inf]} sube más que {nombres[v_sup]}")
                err['voces'] = [v_inf, v_sup]
                errores.append(err)

    # C. SÉPTIMAS
    # Crear acorde music21 para análisis armónico
    notas_lista = [n for n in acorde_act.values() if n is not None]
    if len(notas_lista) >= 3:
        c_m21 = music21.chord.Chord(notas_lista)
        if c_m21.seventh:
            nombre_7 = c_m21.seventh.nameWithOctave
            # Buscar quien la tiene
            v_7 = None
            for v, n in acorde_act.items():
                if n and n.nameWithOctave == nombre_7:
                    v_7 = v
                    break
            
            if v_7 and acorde_sig.get(v_7):
                diff = acorde_sig[v_7].ps - acorde_act[v_7].ps
                if diff >= 0:
                    err = fmt_err(compas, tiempo, f"Séptima en {nombres[v_7]} no resuelve")
                    err['voces'] = [v_7]
                    errores.append(err)
                elif diff < -2:
                    err = fmt_err(compas, tiempo, f"Séptima en {nombres[v_7]} salta")
                    err['voces'] = [v_7]
                    errores.append(err)

    return errores

# =========================================================
# 📡 RUTA PRINCIPAL
# =========================================================

@app.route('/analizar_partitura', methods=['POST'])
def analizar_partitura():
    try:
        datos = request.get_json()
        partitura_raw = datos.get('partitura', [])
        
        # 1. DEBUG: Imprimir en terminal lo que llega (¡MIRA AQUÍ!)
        print("\n--- NUEVA PETICIÓN DE ANÁLISIS ---")
        
        errores_total = []
        acordes_procesados = []

        # 2. PRE-PROCESAMIENTO: Convertir todo a objetos Music21 antes de analizar
        for t_dict in partitura_raw:
            acorde_obj = {v: obtener_nota(t_dict.get(v)) for v in ['B','T','A','S']}
            acordes_procesados.append(acorde_obj)

        # 3. EJECUCIÓN DE JUECES
        for i in range(len(acordes_procesados)):
            # Datos de contexto
            compas = (i // 4) + 1
            tiempo = (i % 4) + 1
            acorde_actual = acordes_procesados[i]

            # A. JUEZ VERTICAL (Siempre se ejecuta)
            # Imprimir para debug
            # print(f"Analizando Vertical C{compas}-T{tiempo}: {acorde_actual}")
            errores_total.extend(juez_vertical(acorde_actual, compas, tiempo, i))

            # B. JUEZ HORIZONTAL (Solo si no es el último)
            if i < len(acordes_procesados) - 1:
                acorde_siguiente = acordes_procesados[i+1]
                # print(f"Analizando Horizontal -> C{compas}-T{tiempo+1}")
                errores_total.extend(juez_horizontal(acorde_actual, acorde_siguiente, compas, tiempo, i))

        msg = "✅ Ejercicio Correcto" if not errores_total else f"⚠️ {len(errores_total)} errores encontrados"
        return jsonify({'errores': errores_total, 'mensaje': msg})

    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        return jsonify({'errores': [], 'mensaje': "Error interno en el servidor"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)