"""
================================================================================
CEREBRO TONAL - Motor de Análisis Armónico para Aula de Armonía
================================================================================

Este módulo actúa como traductor entre music21 (terminología anglosajona) y
la terminología pedagógica europea usada en conservatorios.

Arquitectura:
    music21 (análisis bruto) → CerebroTonal → Cifrado Europeo

Componentes:
    - ContextoTonal: Mantiene el estado de tonalidad activa
    - TraductorCifrado: Convierte cifrado anglosajón a europeo
    - DetectorFunciones: Identifica dominantes secundarias, etc.
    - DetectorCadencias: Detecta cadencias (PAC, HC, DC, etc.)
    - DetectorAcordesEspeciales: Napolitana, +6 italiana/francesa/alemana

Autor: Aula de Armonía
Versión: 2.0
================================================================================
"""

import music21
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERACIONES Y TIPOS
# =============================================================================

class Modo(Enum):
    """Modos tonales soportados"""
    MAYOR = "major"
    MENOR = "minor"


class FuncionArmonica(Enum):
    """Funciones armónicas principales"""
    TONICA = "T"
    SUBDOMINANTE = "S"
    DOMINANTE = "D"


class TipoCadencia(Enum):
    """Tipos de cadencias"""
    PERFECTA_AUTENTICA = "PAC"      # V(7) → I, soprano en tónica, fundamentales
    IMPERFECTA_AUTENTICA = "IAC"    # V → I, pero con inversión o soprano no en tónica
    SEMICADENCIA = "HC"              # ? → V
    ROTA = "DC"                      # V → vi (o VI en menor)
    PLAGAL = "PC"                    # IV → I


class TipoAcordeEspecial(Enum):
    """Acordes cromáticos especiales"""
    NAPOLITANA = "N"
    SEXTA_ITALIANA = "+6it"
    SEXTA_FRANCESA = "+6fr"
    SEXTA_ALEMANA = "+6al"
    DOMINANTE_SECUNDARIA = "V/"
    SENSIBLE_SECUNDARIA = "vii°/"


# =============================================================================
# CONTEXTO TONAL
# =============================================================================

@dataclass
class ContextoTonal:
    """
    Mantiene el estado del contexto tonal actual.
    
    Atributos:
        tonica: Nota fundamental de la tonalidad (C, D, E, etc.)
        modo: Mayor o menor
        tonalidad_local: Para tonicizaciones temporales
        armadura: Número de alteraciones (-7 a +7, negativo = bemoles)
    """
    tonica: str = "C"
    modo: Modo = Modo.MAYOR
    tonalidad_local: Optional[str] = None
    
    def __post_init__(self):
        """Calcula la armadura automáticamente"""
        self._calcular_armadura()
    
    def _calcular_armadura(self):
        """Calcula el número de alteraciones de la armadura"""
        # Orden de sostenidos: F C G D A E B
        # Orden de bemoles: B E A D G C F
        orden_sostenidos = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#']
        orden_bemoles = ['C', 'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb']
        
        tonica_normalizada = self.tonica.replace('b', '-')
        
        try:
            if self.modo == Modo.MAYOR:
                if self.tonica in orden_sostenidos:
                    self.armadura = orden_sostenidos.index(self.tonica)
                elif self.tonica.replace('#', '').replace('-', 'b') in orden_bemoles:
                    self.armadura = -orden_bemoles.index(self.tonica.replace('-', 'b').replace('#', ''))
                else:
                    self.armadura = 0
            else:
                # Menor: relativo mayor tiene 3 semitonos más arriba
                # Por ahora, cálculo simplificado
                self.armadura = 0
        except (ValueError, IndexError):
            self.armadura = 0
    
    @property
    def tonalidad_str(self) -> str:
        """Retorna la tonalidad como string legible"""
        modo_str = "Mayor" if self.modo == Modo.MAYOR else "menor"
        return f"{self.tonica} {modo_str}"
    
    @property
    def key_music21(self) -> music21.key.Key:
        """Retorna el objeto Key de music21"""
        return music21.key.Key(self.tonica, self.modo.value)
    
    def establecer_tonalidad(self, tonica: str, modo: str = "major"):
        """Actualiza la tonalidad"""
        self.tonica = tonica
        self.modo = Modo.MAYOR if modo == "major" else Modo.MENOR
        self.tonalidad_local = None
        self._calcular_armadura()


# =============================================================================
# TRADUCTOR DE CIFRADO
# =============================================================================

class TraductorCifrado:
    """
    Traduce el cifrado de music21 (anglosajón) al cifrado europeo de conservatorio.
    
    Conversiones principales:
        V65 → +6 (séptima de dominante, 1ª inversión)
        V43 → +4/3
        V42 → +2
        viio7 → VII7 dis. o "sensible"
        I6 → I6 (sin cambio, pero formateado)
        I64 → I 6/4
    """
    
    def __init__(self, contexto: ContextoTonal):
        self.contexto = contexto
    
    def traducir(self, numeral_m21: music21.roman.RomanNumeral) -> Dict:
        """
        Traduce un RomanNumeral de music21 a cifrado europeo.
        
        Args:
            numeral_m21: Objeto RomanNumeral de music21
            
        Returns:
            Dict con:
                - grado: str (I, ii, V, etc.)
                - cifrado: str (+6, 6/4, etc.)
                - funcion: FuncionArmonica
                - texto_completo: str (V+6, I6/4, etc.)
        """
        try:
            # Obtener grado base
            grado_num = numeral_m21.scaleDegree
            figura = numeral_m21.figure  # Ej: "V65", "I6", "viio7"
            
            # Determinar si es mayor/menor por la figura
            grado_str = self._obtener_grado_str(numeral_m21)
            
            # Detectar si tiene séptima
            # music21.containsSeventh() puede fallar en acordes incompletos (ej: 5ta omitida)
            # Por eso miramos también la figura que music21 ha identificado
            tiene_septima = numeral_m21.containsSeventh() or \
                            ('7' in figura and '17' not in figura) or \
                            '65' in figura or \
                            '43' in figura or \
                            '42' in figura or \
                            (figura.endswith('2') and not figura.endswith('12'))
            
            # Detectar si tiene novena (music21 no lo expone directo, lo calculamos luego)
            tiene_novena = False
            
            # Obtener inversión
            inversion = numeral_m21.inversion()
            
            # Traducir cifrado
            if tiene_septima:
                # Determinar tipo de séptima
                es_dominante = numeral_m21.isDominantSeventh() or (grado_num == 5)
                es_disminuida = numeral_m21.isDiminishedSeventh() or 'o7' in figura
                es_sensible = numeral_m21.isHalfDiminishedSeventh() or '/o' in figura or 'ø' in figura
                
                if es_dominante and not (es_disminuida or es_sensible):
                    # Séptima de dominante (V7)
                    cifrado = self._cifrado_septima_dominante(inversion)
                elif es_disminuida:
                    # Séptima disminuida
                    cifrado = self._cifrado_septima_disminuida(inversion)
                elif es_sensible:
                    # Séptima de sensible (semidisminuida)
                    cifrado = self._cifrado_septima_sensible(inversion)
                else:
                    # Otras séptimas (diatónicas mayores/menores)
                    cifrado = self._cifrado_septima_general(inversion)
            else:
                # Triada
                cifrado = self._cifrado_triada(inversion)
            
            # Determinar función armónica
            funcion = self._obtener_funcion(grado_num)
            
            # Construir texto completo
            texto = f"{grado_str}{cifrado}"
            
            return {
                "grado": grado_str,
                "grado_num": grado_num,
                "cifrado": cifrado,
                "funcion": funcion,
                "texto_completo": texto,
                "tiene_septima": tiene_septima,
                "tiene_novena": tiene_novena,
                "inversion": inversion
            }
        except Exception as e:
            logger.error(f"Error traduciendo cifrado: {e}")
            return {
                "grado": "?",
                "grado_num": 0,
                "cifrado": "",
                "funcion": FuncionArmonica.TONICA,
                "texto_completo": "?",
                "tiene_septima": False,
                "tiene_novena": False,
                "inversion": 0
            }
    
    def _obtener_grado_str(self, numeral: music21.roman.RomanNumeral) -> str:
        """Obtiene el grado como string (I, ii, V, etc.)"""
        # Usar romanNumeral para preservar alteraciones (bII, #iv)
        rn = numeral.romanNumeral
        calidad = numeral.quality
        
        # Ajustar calidad si es necesario (music21 ya suele hacerlo bien en romanNumeral)
        # Pero aseguramos símbolos europeos
        
        grado_base = rn
        
        # Añadir símbolo de calidad si falta
        if numeral.isHalfDiminishedSeventh():
            if 'ø' not in grado_base:
                grado_base += "ø"
        elif numeral.isDiminishedSeventh():
            if '°' not in grado_base:
                grado_base += "°"
        elif calidad == "diminished":
            if '°' not in grado_base and 'o' not in grado_base:
                grado_base += "°"
        elif calidad == "augmented":
            if '+' not in grado_base:
                grado_base += "+"
            
        return grado_base
    
    def _cifrado_septima_dominante(self, inversion: int) -> str:
        """Cifrado europeo para séptima de dominante"""
        mapeo = {0: "7,+", 1: "6,5t", 2: "+6", 3: "+4"}
        return mapeo.get(inversion, "7")

    def _cifrado_septima_disminuida(self, inversion: int) -> str:
        """Cifrado europeo para séptima disminuida (vii°7)"""
        mapeo = {0: "7t", 1: "+6,5t", 2: "+4,3", 3: "+2"}
        return mapeo.get(inversion, "7t")

    def _cifrado_septima_sensible(self, inversion: int) -> str:
        """Cifrado europeo para séptima de sensible (viiø7)"""
        mapeo = {0: "7,5t", 1: "+6,5", 2: "+4,3", 3: "4,+2"}
        return mapeo.get(inversion, "7,5t")
    
    def _cifrado_septima_general(self, inversion: int) -> str:
        """Cifrado para otras séptimas (diatónicas)"""
        mapeo = {0: "7", 1: "6,5", 2: "4,3", 3: "2"}
        return mapeo.get(inversion, "7")
    
    def _cifrado_triada(self, inversion: int) -> str:
        """Cifrado para triadas"""
        mapeo = {0: "", 1: "6", 2: "6,4"}
        return mapeo.get(inversion, "")
    
    def _obtener_funcion(self, grado: int) -> FuncionArmonica:
        """Determina la función armónica"""
        if grado in [1, 6]:
            return FuncionArmonica.TONICA
        elif grado in [2, 4]:
            return FuncionArmonica.SUBDOMINANTE
        elif grado in [5, 7]:
            return FuncionArmonica.DOMINANTE
        else:  # grado 3
            return FuncionArmonica.TONICA


# =============================================================================
# DETECTOR DE FUNCIONES
# =============================================================================

class DetectorFunciones:
    """
    Detecta funciones armónicas avanzadas:
    - Dominantes secundarias (V/V, V/vi, etc.)
    - Sensibles secundarias (vii°/V, etc.)
    - Subdominantes con función de dominante
    
    Lógica principal:
        Si un acorde Mayor o Dominante7 aparece donde se esperaba uno menor,
        probablemente es una dominante secundaria.
        
    Ejemplo en Do Mayor:
        Re Mayor (D-F#-A) → No es ii (menor), es V/V
        Mi Mayor (E-G#-B) → No es iii (menor), es V/vi
    """
    
    # Grados diatónicos esperados en modo Mayor
    GRADOS_MAYOR = {
        1: ("I", "major"),
        2: ("ii", "minor"),
        3: ("iii", "minor"),
        4: ("IV", "major"),
        5: ("V", "major"),
        6: ("vi", "minor"),
        7: ("vii°", "diminished")
    }
    
    # Grados diatónicos esperados en modo menor (armónica)
    GRADOS_MENOR = {
        1: ("i", "minor"),
        2: ("ii°", "diminished"),
        3: ("III", "major"),
        4: ("iv", "minor"),
        5: ("V", "major"),      # Con sensible elevada
        6: ("VI", "major"),
        7: ("vii°", "diminished")  # Con sensible elevada
    }
    
    def __init__(self, contexto: ContextoTonal):
        self.contexto = contexto
    
    def detectar_dominante_secundaria(self, acorde: music21.chord.Chord) -> Optional[Dict]:
        """
        Detecta si un acorde es una dominante secundaria.
        
        Lógica:
            1. El acorde debe ser Mayor o séptima de dominante
            2. Debe contener al menos una nota cromática (no diatónica)
            3. La fundamental del acorde resuelve por quinta al grado objetivo
        
        Args:
            acorde: Chord de music21
            
        Returns:
            Dict con información de la dominante secundaria o None:
                - grado: "V" o "vii°"
                - objetivo: grado romano del objetivo (V, vi, IV, etc.)
                - tiene_septima: bool
                - cifrado: cifrado de inversión
        """
        try:
            key = self.contexto.key_music21
            escala = key.getScale()
            pitches_escala = [p.pitchClass for p in escala.getPitches()]
            
            # Verificar si tiene notas cromáticas
            tiene_cromatismo = False
            for p in acorde.pitches:
                if p.pitchClass not in pitches_escala:
                    tiene_cromatismo = True
                    break
            
            if not tiene_cromatismo:
                return None  # Es diatónico, no es dominante secundaria
            
            # Verificar si es acorde Mayor o séptima de dominante
            es_dom7 = acorde.isDominantSeventh()
            es_mayor = acorde.quality == 'major'
            es_disminuido = acorde.quality == 'diminished' or acorde.isHalfDiminishedSeventh()
            
            if not (es_dom7 or es_mayor or es_disminuido):
                return None
            
            # Obtener la fundamental del acorde
            root = acorde.root()
            if root is None:
                return None
            
            # Calcular el grado objetivo
            # Para V/x: la dominante resuelve por 4ta ascendente (o 5ta descendente)
            #           root + P4 = objetivo (ej: D + P4 = G, entonces D7 es V7/V en Do)
            # Para vii°/x: la sensible resuelve por semitono ascendente
            #           root + m2 = objetivo
            if es_disminuido:
                # Sensible secundaria: resuelve por semitono ascendente
                objetivo_pitch = root.transpose('m2')
                if acorde.isHalfDiminishedSeventh():
                    tipo_secundaria = "viiø"
                else:
                    tipo_secundaria = "vii°"
            else:
                # Dominante secundaria: resuelve por cuarta ascendente
                objetivo_pitch = root.transpose('P4')
                tipo_secundaria = "V"
            
            # Encontrar qué grado de la escala es el objetivo
            objetivo_grado = self._pitch_a_grado(objetivo_pitch, key)
            
            if objetivo_grado is None:
                return None
            
            # Excluir dominantes de grados que no tienen sentido
            # No se usa V/I (eso es simplemente V) ni V/vii° (muy raro)
            if objetivo_grado.upper() not in ['II', 'III', 'IV', 'V', 'VI']:
                return None
            
            # Formatear el objetivo según el modo de la tonalidad principal
            # En modo Mayor: ii, iii, IV, V, vi son los grados diatónicos
            # En modo menor: ii°, III, iv, V, VI son los grados diatónicos
            if self.contexto.modo == Modo.MAYOR:
                # Grados diatónicos en Mayor: I, ii, iii, IV, V, vi, vii°
                objetivos_formato = {
                    'II': 'ii',    # V/ii (dominante del ii grado)
                    'III': 'iii',  # V/iii (dominante del iii grado)
                    'IV': 'IV',    # V/IV (dominante del IV grado)
                    'V': 'V',      # V/V (dominante del V grado)
                    'VI': 'vi'     # V/vi (dominante del vi grado)
                }
            else:
                # Grados diatónicos en menor armónico: i, ii°, III, iv, V, VI, vii°
                objetivos_formato = {
                    'II': 'ii°',   # V/ii° 
                    'III': 'III',  # V/III
                    'IV': 'iv',    # V/iv
                    'V': 'V',      # V/V
                    'VI': 'VI'     # V/VI
                }
            
            objetivo_romano = objetivos_formato.get(objetivo_grado.upper(), objetivo_grado)
            
            # Determinar inversión y cifrado
            inversion = acorde.inversion()
            if es_dom7:
                cifrado_map = {0: "7,+", 1: "6,5t", 2: "+6", 3: "+4"}
                cifrado = cifrado_map.get(inversion, "7")
            elif es_disminuido:
                if acorde.containsSeventh():
                    cifrado_map = {0: "7t", 1: "6,5t", 2: "4,3t", 3: "2"}
                    cifrado = cifrado_map.get(inversion, "7t")
                else:
                    cifrado_map = {0: "", 1: "6", 2: "6,4"}
                    cifrado = cifrado_map.get(inversion, "")
            else:
                cifrado_map = {0: "", 1: "6", 2: "6,4"}
                cifrado = cifrado_map.get(inversion, "")
            
            return {
                "tipo": tipo_secundaria,
                "objetivo": objetivo_romano,
                "tiene_septima": es_dom7 or acorde.containsSeventh(),
                "cifrado": cifrado,
                "inversion": inversion
            }
            
        except Exception as e:
            logger.warning(f"Error detectando dominante secundaria: {e}")
            return None

    def detectar_prestamo_menor(self, acorde: music21.chord.Chord) -> Optional[Dict]:
        """Detecta acordes prestados del modo menor cuando la tonalidad es mayor.

        Casos soportados:
            - i, iv, ii° (subdominante modal), v (dominante menor), bVI, bVII
        Devuelve dict con la figura en el modo menor paralelo.
        """
        if self.contexto.modo != Modo.MAYOR:
            return None
        try:
            key_minor = music21.key.Key(self.contexto.tonica, 'minor')
            rn_minor = music21.roman.romanNumeralFromChord(acorde, key_minor)
            figura = rn_minor.figure  # ej: iv6, bVI, bVII, i
            base = rn_minor.romanNumeral  # sin inversiones

            permitidos = ['i', 'iv', 'bVI', 'bVII', 'ii°', 'v', 'bIII']
            if base not in permitidos:
                return None

            return {
                "rn_minor": rn_minor,
                "base": base,
                "inversion": rn_minor.inversion(),
                "tiene_septima": rn_minor.containsSeventh(),
                "grado_num": rn_minor.scaleDegree
            }
        except Exception as e:
            logger.warning(f"Error detectando préstamo modal: {e}")
            return None
    
    def _pitch_a_grado(self, pitch: music21.pitch.Pitch, key: music21.key.Key) -> Optional[str]:
        """Convierte un pitch al grado romano correspondiente en la tonalidad"""
        try:
            # Usar music21 para obtener el grado de la escala de forma estricta
            degree = key.getScaleDegreeFromPitch(pitch)
            
            if degree:
                grados = ["", "I", "II", "III", "IV", "V", "VI", "VII"]
                return grados[degree]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error convirtiendo pitch a grado: {e}")
            return None
    
    def obtener_funcion(self, grado: int, calidad: str) -> FuncionArmonica:
        """
        Determina la función armónica de un grado.
        
        Funciones:
            - TÓNICA: I, vi (iii en algunos contextos)
            - SUBDOMINANTE: IV, ii (vi en algunos contextos)
            - DOMINANTE: V, vii°
        """
        if grado in [1, 6]:
            return FuncionArmonica.TONICA
        elif grado in [4, 2]:
            return FuncionArmonica.SUBDOMINANTE
        elif grado in [5, 7]:
            return FuncionArmonica.DOMINANTE
        else:
            return FuncionArmonica.TONICA  # iii es ambiguo


# =============================================================================
# DETECTOR DE ACORDES ESPECIALES
# =============================================================================

class DetectorAcordesEspeciales:
    """
    Detecta acordes cromáticos especiales:
    - Napolitana (bII6)
    - Sexta aumentada italiana (+6it): b6 - 1 - #4
    - Sexta aumentada francesa (+6fr): b6 - 1 - 2 - #4
    - Sexta aumentada alemana (+6al): b6 - 1 - b3 - #4
    """
    
    def __init__(self, contexto: ContextoTonal):
        self.contexto = contexto
    
    def detectar_napolitana(self, acorde: music21.chord.Chord) -> bool:
        """
        Detecta si un acorde es la Napolitana (bII6).
        
        Características:
            - Triada Mayor sobre el II grado rebajado (bII)
            - Generalmente en primera inversión (6)
            - En Do Mayor: Db-F-Ab (o Reb-Fa-Lab)
        
        Returns:
            True si es Napolitana, False en caso contrario
        """
        try:
            key = self.contexto.key_music21
            tonica = key.tonic
            
            # El bII está 1 semitono arriba de la tónica
            bII_root = tonica.transpose('m2')
            
            # Verificar si la fundamental del acorde es bII
            root = acorde.root()
            if root is None:
                return False
            
            # Comparar pitch class (ignorar octava)
            if root.pitchClass != bII_root.pitchClass:
                return False
            
            # Verificar que es una triada Mayor
            if acorde.quality != 'major':
                return False
            
            # Verificar que está en primera inversión (común pero no obligatorio)
            # La Napolitana clásica está en 6 (primera inversión)
            # Pero también puede estar en fundamental
            
            return True
            
        except Exception as e:
            logger.warning(f"Error detectando Napolitana: {e}")
            return False
    
    def detectar_sexta_aumentada(self, acorde: music21.chord.Chord) -> Optional[TipoAcordeEspecial]:
        """
        Detecta el tipo de acorde de sexta aumentada.
        
        Los acordes de +6 contienen un intervalo de sexta aumentada (9 semitonos)
        entre el b6 y #4 de la escala. Resuelven típicamente a V.
        
        En Do Mayor/menor:
            - b6 = Lab (Ab)
            - #4 = Fa# (F#)
            
        Tipos:
            - Italiana (+6it): 3 notas - Ab, C, F# (b6, 1, #4)
            - Francesa (+6fr): 4 notas - Ab, C, D, F# (b6, 1, 2, #4)  
            - Alemana (+6al): 4 notas - Ab, C, Eb, F# (b6, 1, b3, #4)
        
        Returns:
            TipoAcordeEspecial o None
        """
        try:
            key = self.contexto.key_music21
            tonica = key.tonic
            
            # Calcular las notas características
            b6 = tonica.transpose('m6')   # Sexta menor = b6
            sharp4 = tonica.transpose('A4')  # Cuarta aumentada = #4
            grado1 = tonica  # Tónica
            grado2 = tonica.transpose('M2')  # Segunda mayor
            b3 = tonica.transpose('m3')  # Tercera menor
            
            # Obtener pitch classes del acorde
            chord_pcs = set(p.pitchClass for p in acorde.pitches)
            
            # Verificar que contiene b6 y #4 (intervalo de +6)
            if b6.pitchClass not in chord_pcs or sharp4.pitchClass not in chord_pcs:
                return None
            
            # Verificar que contiene la tónica
            if grado1.pitchClass not in chord_pcs:
                return None
            
            num_notas = len(chord_pcs)
            
            # Clasificar por tipo
            if num_notas == 3:
                # Italiana: b6, 1, #4
                return TipoAcordeEspecial.SEXTA_ITALIANA
            elif num_notas == 4:
                if b3.pitchClass in chord_pcs:
                    # Alemana: b6, 1, b3, #4
                    return TipoAcordeEspecial.SEXTA_ALEMANA
                elif grado2.pitchClass in chord_pcs:
                    # Francesa: b6, 1, 2, #4
                    return TipoAcordeEspecial.SEXTA_FRANCESA
            
            return None
            
        except Exception as e:
            logger.warning(f"Error detectando sexta aumentada: {e}")
            return None


# =============================================================================
# DETECTOR DE CADENCIAS
# =============================================================================

class DetectorCadencias:
    """
    Detecta cadencias en secuencias de acordes.
    
    Tipos soportados:
        - PAC (Cadencia Auténtica Perfecta): V(7) → I, ambos en fundamental, soprano en tónica
        - IAC (Cadencia Auténtica Imperfecta): V → I con inversión o soprano no en tónica
        - HC (Semicadencia): cualquier acorde → V
        - DC (Cadencia Rota/Deceptiva): V → vi (o VI en menor)
        - PC (Cadencia Plagal): IV → I
    """
    
    def __init__(self, contexto: ContextoTonal):
        self.contexto = contexto
    
    def detectar_cadencia(self, acorde_prev: Dict, acorde_actual: Dict, 
                          soprano_actual: str) -> Optional[TipoCadencia]:
        """
        Detecta si hay una cadencia entre dos acordes consecutivos.
        
        Args:
            acorde_prev: Análisis del acorde anterior
            acorde_actual: Análisis del acorde actual
            soprano_actual: Nota de la soprano en el acorde actual
            
        Returns:
            TipoCadencia o None
        """
        # TODO: Implementar en FASE 2.3
        return None
    
    def _es_cadencia_autentica_perfecta(self, prev: Dict, actual: Dict, 
                                         soprano: str) -> bool:
        """Verifica criterios de PAC"""
        # V(7) → I, ambos en estado fundamental, soprano en tónica
        # TODO: Implementar
        return False


# =============================================================================
# CEREBRO TONAL (CLASE PRINCIPAL)
# =============================================================================

class CerebroTonal:
    """
    Clase principal que coordina todos los componentes del análisis tonal.
    
    Uso:
        cerebro = CerebroTonal("C", "major")
        resultado = cerebro.analizar_acorde(notas)
        cadencia = cerebro.analizar_progresion(lista_acordes)
    """
    
    def __init__(self, tonica: str = "C", modo: str = "major"):
        """
        Inicializa el Cerebro Tonal.
        
        Args:
            tonica: Nota fundamental (C, D, E, F, G, A, B con # o b)
            modo: "major" o "minor"
        """
        self.contexto = ContextoTonal(tonica, 
                                       Modo.MAYOR if modo == "major" else Modo.MENOR)
        self.traductor = TraductorCifrado(self.contexto)
        self.detector_funciones = DetectorFunciones(self.contexto)
        self.detector_especiales = DetectorAcordesEspeciales(self.contexto)
        self.detector_cadencias = DetectorCadencias(self.contexto)
        
        logger.info(f"CerebroTonal inicializado en {self.contexto.tonalidad_str}")
    
    def establecer_tonalidad(self, tonica: str, modo: str = "major"):
        """Cambia la tonalidad de análisis"""
        self.contexto.establecer_tonalidad(tonica, modo)
        logger.info(f"Tonalidad cambiada a {self.contexto.tonalidad_str}")
    
    def analizar_acorde(self, notas: Dict[str, str]) -> Dict:
        """
        Analiza un acorde dado como diccionario de voces.
        
        Args:
            notas: {"S": "C5", "A": "E4", "T": "G3", "B": "C3"}
            
        Returns:
            Dict con análisis completo:
                - grado: str
                - cifrado_europeo: str
                - funcion: str
                - es_diatonico: bool
                - tipo_especial: str o None
        """
        try:
            # Filtrar notas vacías y normalizar bemoles (b -> -)
            notas_validas = []
            for n in notas.values():
                if n:
                    # Reemplazar 'b' por '-' para music21, excepto si ya es '-'
                    nota_norm = n.replace('b', '-')
                    notas_validas.append(nota_norm)
            
            if len(notas_validas) < 2:
                return self._resultado_vacio(notas)
            
            # Crear Chord de music21
            chord_m21 = music21.chord.Chord(notas_validas)

            # Detectar novena (intervalo de 13 o 14 semitonos desde la fundamental)
            def _tiene_novena(chord: music21.chord.Chord) -> bool:
                try:
                    root = chord.root()
                    if root is None:
                        return False
                    for p in chord.pitches:
                        if p == root:
                            continue
                        interval = music21.interval.Interval(root, p)
                        if interval.semitones in (13, 14):
                            return True
                    return False
                except Exception:
                    return False
            tiene_novena = _tiene_novena(chord_m21)
            
            # Obtener el bajo para determinar inversión
            bajo = notas.get('B')
            
            # Analizar con music21 en el contexto tonal
            key_m21 = self.contexto.key_music21
            
            # Obtener numeral romano
            numeral = music21.roman.romanNumeralFromChord(chord_m21, key_m21)
            
            # Traducir a cifrado europeo
            traduccion = self.traductor.traducir(numeral)
            traduccion["tiene_novena"] = tiene_novena

            # Ajustar cifrado para acordes con novena
            if tiene_novena:
                if traduccion["grado_num"] == 5:
                    # Dominante de novena
                    traduccion["cifrado"] = "9"
                    traduccion["texto_completo"] = f"{traduccion['grado']}9"
                    traduccion["tiene_septima"] = True  # asumimos 7 incluida
                else:
                    traduccion["cifrado"] = "9"
                    traduccion["texto_completo"] = f"{traduccion['grado']}9"
            
            # Verificar si es diatónico
            es_diatonico = self._es_diatonico(chord_m21)
            
            # Detectar dominante secundaria
            dom_secundaria = self.detector_funciones.detectar_dominante_secundaria(chord_m21)

            # Detectar acordes prestados del modo menor (solo en tonalidad mayor)
            prestamo_menor = self.detector_funciones.detectar_prestamo_menor(chord_m21)
            # Fallback de préstamo modal: si music21 ya etiqueta con bemol o calidad menor en modo mayor
            if not prestamo_menor and self.contexto.modo == Modo.MAYOR:
                base_rn = numeral.romanNumeral  # ej: iv, bVI, bVII, i, v, ii°
                # Lista estricta de préstamos modales comunes
                prestamos_comunes = ['i', 'iv', 'ii°', 'v', 'bVI', 'bVII', 'bIII', 'bII']
                
                if base_rn in prestamos_comunes:
                    prestamo_menor = {
                        "rn_minor": numeral,
                        "base": base_rn,
                        "inversion": numeral.inversion(),
                        "tiene_septima": numeral.containsSeventh(),
                        "grado_num": numeral.scaleDegree
                    }
            
            # Detectar acordes especiales (Napolitana, +6)
            tipo_especial = None
            es_napolitana = self.detector_especiales.detectar_napolitana(chord_m21)
            sexta_aug = self.detector_especiales.detectar_sexta_aumentada(chord_m21)
            
            if es_napolitana:
                tipo_especial = "N"
                grado_napo = "bII"
                inversion = chord_m21.inversion()
                tiene7_napo = chord_m21.containsSeventh()

                if tiene7_napo:
                    cifrado_napo = self.traductor._cifrado_septima_general(inversion)
                else:
                    cifrado_napo = self.traductor._cifrado_triada(inversion)

                traduccion["texto_completo"] = f"{grado_napo}{cifrado_napo}"
                traduccion["grado"] = grado_napo
                traduccion["cifrado"] = cifrado_napo
                traduccion["tiene_septima"] = tiene7_napo
                traduccion["inversion"] = inversion
                traduccion["funcion"] = FuncionArmonica.SUBDOMINANTE
                
            elif sexta_aug:
                tipo_especial = sexta_aug.value
                # Formato: +6it, +6fr, +6al
                traduccion["texto_completo"] = sexta_aug.value
                traduccion["grado"] = sexta_aug.value
                traduccion["cifrado"] = ""
                traduccion["funcion"] = FuncionArmonica.SUBDOMINANTE  # Función predominante
                
            elif dom_secundaria:
                # Construir texto completo: V7/V, V/vi, vii°/V, etc.
                tipo = dom_secundaria["tipo"]  # "V" o "vii°"
                objetivo = dom_secundaria["objetivo"]  # "V", "vi", etc.
                cifrado = dom_secundaria["cifrado"]  # "7", "+6", "", etc.
                
                # Formato: V7/V, V+6/vi, vii°7/V
                if cifrado:
                    texto_secundaria = f"{tipo}{cifrado}/{objetivo}"
                else:
                    texto_secundaria = f"{tipo}/{objetivo}"
                
                traduccion["texto_completo"] = texto_secundaria
                traduccion["grado"] = f"{tipo}/{objetivo}"
                traduccion["cifrado"] = cifrado
                traduccion["tiene_septima"] = dom_secundaria["tiene_septima"]
                traduccion["inversion"] = dom_secundaria["inversion"]
                traduccion["funcion"] = FuncionArmonica.DOMINANTE  # Siempre función dominante
                tipo_especial = "dominante_secundaria"

            elif prestamo_menor:
                rn_pm = prestamo_menor["rn_minor"]
                # Usar _obtener_grado_str para formatear correctamente (iv, bVI, etc.)
                grado_pm = self.traductor._obtener_grado_str(rn_pm)
                inversion_pm = rn_pm.inversion()
                tiene7_pm = prestamo_menor["tiene_septima"]
                # Cifrado inversión
                if tiene7_pm:
                    cif_pm = self.traductor._cifrado_septima_general(inversion_pm)
                else:
                    cif_pm = self.traductor._cifrado_triada(inversion_pm)

                traduccion["texto_completo"] = grado_pm + (cif_pm or "")
                traduccion["grado"] = grado_pm
                traduccion["cifrado"] = cif_pm
                traduccion["tiene_septima"] = tiene7_pm
                traduccion["inversion"] = inversion_pm
                traduccion["funcion"] = FuncionArmonica.SUBDOMINANTE if prestamo_menor["base"] in ["iv", "ii°", "bVI", "bVII"] else self.traductor._obtener_funcion(prestamo_menor["grado_num"])
                tipo_especial = "prestamo_menor"
            
            # Refinamiento: Marcar acordes cromáticos desconocidos/extraños
            if not es_diatonico and tipo_especial is None:
                g = traduccion["grado"]
                # Lista blanca de grados cromáticos aceptados
                aceptados = ['bII', 'bIII', 'bVI', 'bVII', 'N', 'iv', 'v', 'ii°', 'vii°7']
                
                # Si el grado tiene alteraciones y no es uno de los estándares aceptados
                if g not in aceptados and (g.startswith('b') or g.startswith('#') or 'b' in g or '#' in g):
                    traduccion["texto_completo"] += "?"
                    traduccion["grado"] += "?"
                    # Opcional: invalidar función si es muy extraño
            
            # Obtener fundamental del acorde para reglas armónicas
            try:
                fundamental = chord_m21.root().name if chord_m21.root() else None
            except Exception:
                fundamental = None
            
            # Normalizar quality para compatibilidad con chord_knowledge.py
            # music21.quality devuelve 'major', 'minor', 'dominant-seventh', etc.
            # NO usar pitchedCommonName que devuelve 'C-minor triad'
            try:
                quality_str = numeral.quality if numeral else None
            except Exception:
                quality_str = None
            
            return {
                "grado": traduccion["grado"],
                "grado_num": traduccion.get("grado_num", 0),
                "cifrado_europeo": traduccion["cifrado"],
                "texto_completo": traduccion["texto_completo"],
                "funcion": traduccion["funcion"].value,
                "es_diatonico": es_diatonico,
                "tipo_especial": tipo_especial,
                "tiene_septima": traduccion.get("tiene_septima", False),
                "tiene_novena": traduccion.get("tiene_novena", False),
                "inversion": traduccion.get("inversion", 0),
                "notas": notas,
                "fundamental": fundamental,  # NUEVO: para harmonic_rules
                "tipo": quality_str  # CORREGIDO: usar quality en lugar de pitchedCommonName
            }
            
        except Exception as e:
            logger.error(f"Error analizando acorde: {e}")
            return self._resultado_vacio(notas)
    
    def _resultado_vacio(self, notas: Dict[str, str]) -> Dict:
        """Retorna un resultado vacío/por defecto"""
        return {
            "grado": "",
            "grado_num": 0,
            "cifrado_europeo": "",
            "texto_completo": "",
            "funcion": "",
            "es_diatonico": True,
            "tipo_especial": None,
            "tiene_septima": False,
            "tiene_novena": False,
            "inversion": 0,
            "notas": notas,
            "fundamental": None,
            "tipo": None
        }

    def _es_diatonico(self, chord: music21.chord.Chord) -> bool:
        """Verifica si todas las notas del acorde son diatónicas"""
        try:
            escala = self.contexto.key_music21.getScale()
            for pitch in chord.pitches:
                # Comprobar si el pitch class está en la escala
                if pitch.pitchClass not in [p.pitchClass for p in escala.getPitches()]:
                    return False
            return True
        except:
            return True
    
    def analizar_progresion(self, acordes: List[Dict[str, str]]) -> List[Dict]:
        """
        Analiza una progresión de acordes.
        
        Args:
            acordes: Lista de diccionarios de notas
            
        Returns:
            Lista de análisis con cadencias marcadas
        """
        # TODO: Implementar en FASE 2.3
        resultados = []
        for acorde in acordes:
            analisis = self.analizar_acorde(acorde)
            analisis["cadencia"] = None
            resultados.append(analisis)
        return resultados
    
    def obtener_armadura_vexflow(self) -> str:
        """
        Retorna la tonalidad en formato VexFlow.
        
        Returns:
            String como "C", "G", "F", "Am", "Em", etc.
        """
        if self.contexto.modo == Modo.MAYOR:
            return self.contexto.tonica
        else:
            return f"{self.contexto.tonica}m"


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def crear_cerebro_tonal(tonica: str = "C", modo: str = "major") -> CerebroTonal:
    """
    Factory function para crear un CerebroTonal.
    
    Args:
        tonica: Nota fundamental
        modo: "major" o "minor"
        
    Returns:
        Instancia de CerebroTonal configurada
    """
    return CerebroTonal(tonica, modo)


# =============================================================================
# CONSTANTES DE REFERENCIA
# =============================================================================

# Tonalidades mayores ordenadas por armadura
TONALIDADES_MAYORES = [
    ("Cb", -7), ("Gb", -6), ("Db", -5), ("Ab", -4), ("Eb", -3), 
    ("Bb", -2), ("F", -1), ("C", 0), ("G", 1), ("D", 2), 
    ("A", 3), ("E", 4), ("B", 5), ("F#", 6), ("C#", 7)
]

# Tonalidades menores (relativas)
TONALIDADES_MENORES = [
    ("Ab", -7), ("Eb", -6), ("Bb", -5), ("F", -4), ("C", -3),
    ("G", -2), ("D", -1), ("A", 0), ("E", 1), ("B", 2),
    ("F#", 3), ("C#", 4), ("G#", 5), ("D#", 6), ("A#", 7)
]

# Tonalidades prácticas (las más usadas en ejercicios)
TONALIDADES_PRACTICAS = [
    {"tonica": "C", "modo": "major", "nombre": "Do Mayor"},
    {"tonica": "G", "modo": "major", "nombre": "Sol Mayor"},
    {"tonica": "D", "modo": "major", "nombre": "Re Mayor"},
    {"tonica": "F", "modo": "major", "nombre": "Fa Mayor"},
    {"tonica": "Bb", "modo": "major", "nombre": "Si♭ Mayor"},
    {"tonica": "A", "modo": "minor", "nombre": "La menor"},
    {"tonica": "E", "modo": "minor", "nombre": "Mi menor"},
    {"tonica": "D", "modo": "minor", "nombre": "Re menor"},
]
