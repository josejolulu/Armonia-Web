"""
================================================================================
HARMONIC RULES ENGINE - Sistema de Reglas Armónicas con Excepciones
================================================================================

Arquitectura modular para validación de reglas de conducción de voces SATB.

Componentes:
    - ConfidenceLevel: Niveles de confianza en detección de errores
    - RuleTier: Prioridad de las reglas (Críticas, Importantes, Avanzadas)
    - HarmonicRule: Clase base abstracta para todas las reglas
    - ContextAnalyzer: Detecta contexto armónico para excepciones
    - RulesEngine: Motor que coordina todas las reglas

Uso:
    engine = RulesEngine(key="C", mode="major")
    errors = engine.validate_progression(chord1, chord2, context)

Autor: Aula de Armonía
Versión: 3.0 (Phase 3A)
================================================================================
"""

from enum import Enum
from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass
import music21
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERACIONES Y CONFIGURACIÓN
# =============================================================================

class ConfidenceLevel(Enum):
    """Niveles de confianza en la detección de errores"""
    CERTAIN = 100    # Regla clara, sin ambigüedad
    HIGH = 80        # Muy probable error, contexto claro
    MEDIUM = 60      # Dudoso, posible excepción no contemplada
    LOW = 40         # Caso edge, sugerencia pedagógica


class RuleTier(Enum):
    """Prioridad/complejidad de las reglas"""
    CRITICAL = 1      # Tier 1: Errores graves (paralelas, resoluciones)
    IMPORTANT = 2     # Tier 2: Errores notables (saltos, unísono)
    ADVANCED = 3      # Tier 3: Refinamientos (modulaciones, acordes especiales)


# =============================================================================
# ANALIZADOR DE CONTEXTO
# =============================================================================

class ContextAnalyzer:
    """
    Analiza el contexto armónico para determinar excepciones.
    
    Detecta:
        - Cambios de disposición (mismo acorde, diferente voicing)
        - Pares V-VII (misma función dominante)
        - Modulaciones
        - Progresiones secuenciales
    """
    
    @staticmethod
    def is_voicing_change(chord1: Dict, chord2: Dict) -> bool:
        """
        Detecta si dos acordes son el mismo acorde con diferente disposición.
        
        Detecta si dos acordes son el mismo acorde con diferente disposición (voicing).
        
        Un cambio de disposición ocurre cuando:
        - Mismo acorde (root, quality, inversión)
        - Mismas pitch classes (notas sin considerar octava)
        - Pero diferentes octavas en las voces
        
        Ejemplo:
            Acorde 1: C3-E3-G3-C4 (Do Mayor cerrado)
            Acorde 2: C3-G3-C4-E4 (Do Mayor abierto)
            → Mismo pitch classes {0,4,7} pero diferente distribución
        
        Returns:
            True si es cambio de disposición válido, False si no
        """
        from music21 import pitch
        
        # DEBUG: Log para ver qué llega
        logger.debug(f"=== is_voicing_change DEBUG ===")
        logger.debug(f"chord1: root={chord1.get('root')}, quality={chord1.get('quality')}, inv={chord1.get('inversion')}")
        logger.debug(f"chord2: root={chord2.get('root')}, quality={chord2.get('quality')}, inv={chord2.get('inversion')}")
        
        # Verificar que sean el mismo acorde básico
        same_root = chord1.get('root') == chord2.get('root')
        same_quality = chord1.get('quality') == chord2.get('quality')
        same_inversion = chord1.get('inversion') == chord2.get('inversion')
        
        logger.debug(f"same_root={same_root}, same_quality={same_quality}, same_inversion={same_inversion}")
        
        if not (same_root and same_quality and same_inversion):
            logger.debug("NO es mismo acorde básico → False")
            return False
        
        # NUEVO: Comparar pitch classes en lugar de strings
        def get_pitch_classes(chord_dict):
            """
            Obtiene pitch classes (0-11) de las notas del acorde.
            
            Pitch class: Clase de altura cromática sin octava
            Do=0, Do#=1, Re=2, ..., Si=11
            
            Esto permite comparar "C4" y "C5" como la misma nota (pitch class 0)
            """
            pitch_classes = set()
            for voice in ['S', 'A', 'T', 'B']:
                note_str = chord_dict.get(voice)
                if note_str:
                    try:
                        p = pitch.Pitch(note_str)
                        pitch_classes.add(p.pitchClass)  # 0-11
                    except:
                        # Si falla parseo, ignorar esta nota
                        pass
            return pitch_classes
        
        pc1 = get_pitch_classes(chord1)
        pc2 = get_pitch_classes(chord2)
        
        logger.debug(f"pitch_classes1={pc1}, pitch_classes2={pc2}")
        
        # Si NO tienen los mismos pitch classes, no es el mismo acorde
        if pc1 != pc2:
            logger.debug("Pitch classes diferentes → False")
            return False
        
        # Si tienen los mismos pitch classes...
        # ...entonces verificar si las voces están en diferentes octavas
        voices1 = {chord1.get('S'), chord1.get('A'), chord1.get('T'), chord1.get('B')}
        voices2 = {chord2.get('S'), chord2.get('A'), chord2.get('T'), chord2.get('B')}
        
        # Eliminar None values
        voices1.discard(None)
        voices2.discard(None)
        
        logger.debug(f"voices1={voices1}, voices2={voices2}")
        
        if voices1 != voices2:
            # Mismas pitch classes, pero diferentes strings de notas
            # → Es un cambio de disposición válido
            logger.info(f"✅ VOICING CHANGE DETECTADO: {pc1}")
            return True
        
        # Exactamente el mismo voicing (mismas notas, mismas octavas)
        logger.debug("Exactamente el mismo voicing → False")
        return False
    
    @staticmethod
    def is_V_VII_pair(chord1: Dict, chord2: Dict, key: str) -> bool:
        """
        Detecta si una progresión es V-VII o VII-V (ambas direcciones).
        
        Razón pedagógica:
            Tanto V como VII tienen función dominante y comparten el tritono.
            La progresión V→VII o VII→V es aceptable armónicamente por esta razón.
        
        Criterios:
            - Grados 5 y 7 (en cualquier orden)
            - Preferiblemente ambos con función dominante 'D'
            - Si no hay función disponible, asumir válido (fallback)
        
        Args:
            chord1, chord2: Diccionarios de acordes
            key: Tonalidad (no usado actualmente, pero disponible)
        
        Returns:
            True si es un par V-VII válido
        
        Examples:
            V → VII (Do Mayor): G → B° ✅
            VII → V (Do Mayor): B° → G ✅
        """
        try:
            # Obtener grados de ambos acordes
            degree1 = chord1.get('degree_num', 0)
            degree2 = chord2.get('degree_num', 0)
            
            degrees = {degree1, degree2}
            
            # Verificar que sean los grados 5 y 7 (V y VII)
            if degrees != {5, 7}:
                return False
            
            # NUEVO: Verificar función dominante con fallback robusto
            # Intentar múltiples nombres de campo por si acaso
            func1 = chord1.get('function', chord1.get('funcion', ''))
            func2 = chord2.get('function', chord2.get('funcion', ''))
            
            # Si ambos tienen función dominante explícita, aceptar
            if func1 == 'D' and func2 == 'D':
                logger.debug(f"Excepción V-VII aplicada: grados {degree1}→{degree2} (ambos con función D)")
                return True
            
            # FALLBACK: Si no hay campo function disponible,
            # asumir que V y VII son dominantes (pedagógicamente correcto)
            if not func1 or not func2:
                logger.debug(f"Excepción V-VII aplicada: grados {degree1}→{degree2} (sin campo function, asumiendo dominantes)")
                return True
            
            # Si solo uno tiene función D, también considerarlo (caso edge)
            if 'D' in (func1, func2):
                logger.debug(f"Excepción V-VII aplicada: grados {degree1}→{degree2} (al menos uno con función D)")
                return True
            
            # No se cumplen criterios
            return False
                
        except Exception as e:
            logger.warning(f"Error detectando par V-VII: {e}")
            return False
    
    @staticmethod
    def detect_modulation(context: Dict) -> Optional[str]:
        """
        Detecta si hay una modulación en el contexto.
        
        Args:
            context: Dict con información del contexto
                     (chord_sequence, current_index, etc.)
        
        Returns:
            Nueva tonalidad si hay modulación, None si no
        """
        # TODO: Implementar detección de modulación en fase posterior
        return None
    
    @staticmethod
    def is_in_pattern(context: Dict) -> bool:
        """
        Detecta si el acorde forma parte de una progresión secuencial.
        
        Progresiones secuenciales (marcha armónica) repiten un patrón
        melódico/armónico, y ciertas reglas se relajan dentro del patrón.
        
        Args:
            context: Información del contexto
            
        Returns:
            True si está en un patrón
        """
        # TODO: Implementar detección de patrones en fase posterior
        return False


# =============================================================================
# CLASE BASE: HARMONIC RULE
# =============================================================================

class HarmonicRule:
    """
    Clase base abstracta para todas las reglas armónicas.
    
    Cada regla específica hereda de esta clase e implementa:
        - _detect_violation(): Lógica de detección del error
        - _calculate_confidence(): Nivel de confianza del error
        
    Sistema de excepciones:
        Las excepciones se añaden con add_exception() y se verifican
        automáticamente antes de reportar un error.
    
    Ejemplo de uso:
        rule = ParallelFifthsRule()
        error = rule.validate(chord1, chord2, context)
        if error:
            print(f"Error: {error['short_msg']} ({error['confidence']}%)")
    """
    
    def __init__(
        self,
        name: str,
        tier: RuleTier,
        color: str,
        short_msg: str,
        full_msg: str
    ):
        """
        Inicializa una regla armónica.
        
        Args:
            name: Identificador único de la regla
            tier: Prioridad (CRITICAL, IMPORTANT, ADVANCED)
            color: Color hexadecimal para UI (#FF0000, etc.)
            short_msg: Mensaje corto para UI compacta
            full_msg: Mensaje completo pedagógico
        """
        self.name = name
        self.tier = tier
        self.color = color
        self.short_msg = short_msg
        self.full_msg = full_msg
        self.exceptions: List[Dict] = []
        self.enabled = True
    
    def add_exception(
        self,
        exception_name: str,
        check: Callable[[Dict, Dict, Dict], bool],
        description: str
    ) -> None:
        """
        Añade una excepción a la regla.
        
        Args:
            exception_name: Nombre descriptivo de la excepción
            check: Función que retorna True si la excepción aplica
            description: Explicación pedagógica de la excepción
        """
        self.exceptions.append({
            'name': exception_name,
            'check': check,
            'description': description
        })
    
    def validate(
        self,
        chord1: Dict,
        chord2: Dict,
        context: Dict
    ) -> Optional[Dict]:
        """
        Valida la regla entre dos acordes consecutivos.
        
        Proceso:
            1. Verifica si la regla está habilitada
            2. Detecta violación básica
            3. Verifica TODAS las excepciones
            4. Si ninguna excepción aplica, retorna el error
        
        Args:
            chord1: Análisis del primer acorde
            chord2: Análisis del segundo acorde
            context: Contexto armónico (tonalidad, secuencia, etc.)
            
        Returns:
            None si no hay error o aplica excepción
            Dict con información del error si se viola la regla
        """
        if not self.enabled:
            return None
        
        # CRITICAL FIX: Inyectar 'key' de context en chords antes de validar
        # El frontend envía 'key' en context, NO en los acordes individuales
        # Sin esto, las reglas que dependen de tonalidad fallan en producción
        if 'key' in context:
            if 'key' not in chord1:
                chord1 = {**chord1, 'key': context['key']}
            if 'key' not in chord2:
                chord2 = {**chord2, 'key': context['key']}
        
        # Detección básica (implementada por cada regla)
        violation = self._detect_violation(chord1, chord2)
        
        if not violation:
            return None
        
        # Verificar TODAS las excepciones
        for exc in self.exceptions:
            try:
                if exc['check'](chord1, chord2, context):
                    # Excepción aplicada, no es error
                    logger.debug(f"Excepción '{exc['name']}' aplicada a {self.name}")
                    return None
            except Exception as e:
                logger.error(f"Error en excepción '{exc['name']}': {e}")
                # Si falla la excepción, no asumimos que aplica
                continue
        
        # Ninguna excepción aplica, es un error
        confidence = self._calculate_confidence(chord1, chord2, context)
        
        # Determinar mensaje según tipo de movimiento
        motion_type = violation.get('motion_type', 'parallel')
        
        # Mensajes diferenciados:
        # "Paralelas" = movimiento directo (mismo sentido)
        # "Consecutivas" = movimiento contrario (sentido opuesto)
        if motion_type == 'parallel':
            short_msg = self.short_msg  # Use el mensaje base (ej: "Quintas paralelas")
        else:  # contrary
            # Cambiar "paralelas" por "consecutivas" en el mensaje
            short_msg = self.short_msg.replace('paralelas', 'consecutivas')
        
        return {
            'rule': self.name,
            'color': self.color,
            'short_msg': short_msg,
            'full_msg': self.full_msg,
            'confidence': confidence,
            'chord_index': violation['chord_index'],
            'voices': violation['voices'],
            'tier': self.tier.value,
            'motion_type': motion_type
        }
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si se viola la regla.
        
        Debe ser implementado por cada regla específica.
        
        Returns:
            None si no hay violación
            Dict con {'chord_index': int, 'voices': List[str]} si hay violación
        """
        raise NotImplementedError(f"Regla {self.name} debe implementar _detect_violation()")
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        Calcula el nivel de confianza del error detectado.
        
        Por defecto retorna CERTAIN. Cada regla puede sobrescribir
        para ajustar basándose en el contexto.
        
        Returns:
            Nivel de confianza (0-100)
        """
        return ConfidenceLevel.CERTAIN.value


# =============================================================================
# UTILIDADES PARA REGLAS
# =============================================================================

class VoiceLeadingUtils:
    """Utilidades estáticas para análisis de conducción de voces"""
    
    @staticmethod
    def get_interval_object(note1: str, note2: str) -> Optional[music21.interval.Interval]:
        """
        Obtiene el objeto Interval de music21 entre dos notas.
        
        Args:
            note1, note2: Notas en formato music21 ('C4', 'E4', etc.)
            
        Returns:
            Objeto Interval de music21 o None si hay error
        """
        try:
            p1 = music21.pitch.Pitch(note1)
            p2 = music21.pitch.Pitch(note2)
            return music21.interval.Interval(p1, p2)
        except Exception as e:
            logger.warning(f"Error calculando intervalo {note1}-{note2}: {e}")
            return None
    
    @staticmethod
    def get_interval(note1: str, note2: str) -> int:
        """
        Calcula el intervalo en semitonos entre dos notas.
        
        Args:
            note1, note2: Notas en formato music21 ('C4', 'E4', etc.)
            
        Returns:
            Número de semitonos (puede ser negativo si note2 < note1)
        """
        interval = VoiceLeadingUtils.get_interval_object(note1, note2)
        return interval.semitones if interval else 0
    
    @staticmethod
    def is_perfect_fifth(note1: str, note2: str) -> bool:
        """
        Verifica si un intervalo es quinta justa.
        
        Usa el nombre del intervalo de music21, no solo semitonos,
        para evitar confusiones con sextas menores descendentes.
        
        Args:
            note1, note2: Notas a comparar
            
        Returns:
            True si el intervalo es quinta justa (P5)
        """
        interval = VoiceLeadingUtils.get_interval_object(note1, note2)
        if not interval:
            return False
        
        # Verificar nombre del intervalo (P5, P12, P19, etc.)
        # music21 usa 'P' para perfecto (Perfect)
        simple_name = interval.simpleName  # Reduce a una octava (P12 -> P5)
        return simple_name == 'P5'
    
    @staticmethod
    def is_augmented_fifth(note1: str, note2: str) -> bool:
        """
        Verifica si un intervalo es quinta aumentada.
        
        Args:
            note1, note2: Notas a comparar
            
        Returns:
            True si el intervalo es quinta aumentada (A5)
        """
        interval = VoiceLeadingUtils.get_interval_object(note1, note2)
        if not interval:
            return False
        
        simple_name = interval.simpleName
        return simple_name == 'A5'
    
    @staticmethod
    def is_diminished_fifth(note1: str, note2: str) -> bool:
        """
        Verifica si un intervalo es quinta disminuida.
        
        Args:
            note1, note2: Notas a comparar
            
        Returns:
            True si el intervalo es quinta disminuida (d5)
        """
        interval = VoiceLeadingUtils.get_interval_object(note1, note2)
        if not interval:
            return False
        
        simple_name = interval.simpleName
        return simple_name == 'd5'
    
    @staticmethod
    def is_fifth(note1: str, note2: str) -> bool:
        """
        Verifica si un intervalo es quinta (justa o aumentada).
        
        IMPORTANTE: Usa interval.simpleName de music21 para precisión.
        NO confía solo en semitonos para evitar falsos positivos.
        
        Args:
            note1, note2: Notas a comparar
            
        Returns:
            True si es quinta justa (P5) o aumentada (A5)
        """
        return (VoiceLeadingUtils.is_perfect_fifth(note1, note2) or
                VoiceLeadingUtils.is_augmented_fifth(note1, note2))
    
    @staticmethod
    def is_octave(note1: str, note2: str) -> bool:
        """
        Verifica si un intervalo es octava.
        
        Args:
            note1, note2: Notas a comparar
            
        Returns:
            True si es octava justa (P8, P15, etc.)
        """
        interval = VoiceLeadingUtils.get_interval_object(note1, note2)
        if not interval:
            return False
        
        simple_name = interval.simpleName
        return simple_name == 'P8' or simple_name == 'P1'
    
    @staticmethod
    def is_leap(note1: str, note2: str, threshold: int = 2) -> bool:
        """
        Detecta si hay salto melódico entre dos notas.
        
        Un salto es un movimiento mayor que el threshold especificado.
        Por defecto, threshold=2 significa "más de un tono entero".
        
        Args:
            note1, note2: Notas a comparar (ej: 'C4', 'E4')
            threshold: Umbral en semitonos (default: 2 = más de un tono)
            
        Returns:
            True si el movimiento es mayor que threshold (es un salto)
            
        Examples:
            is_leap('C4', 'D4', 2) → False (2 semitonos, grado conjunto)
            is_leap('C4', 'E4', 2) → True (4 semitonos, salto de 3ª)
            is_leap('C4', 'G4', 2) → True (7 semitonos, salto de 5ª)
        """
        try:
            n1 = music21.note.Note(note1)
            n2 = music21.note.Note(note2)
            return abs(n2.pitch.ps - n1.pitch.ps) > threshold
        except:
            return False
    
    @staticmethod
    def get_motion_type(
        voice1_note1: str, voice1_note2: str,
        voice2_note1: str, voice2_note2: str
    ) -> str:
        """
        Determina el tipo de movimiento entre dos voces.
        
        Tipos:
            - 'parallel': Ambas voces se mueven en la misma dirección
            - 'contrary': Voces se mueven en direcciones opuestas
            - 'oblique': Una voz se mueve, la otra permanece
            - 'static': Ninguna voz se mueve
        
        Returns:
            Tipo de movimiento como string
        """
        try:
            p1_1 = music21.pitch.Pitch(voice1_note1)
            p1_2 = music21.pitch.Pitch(voice1_note2)
            p2_1 = music21.pitch.Pitch(voice2_note1)
            p2_2 = music21.pitch.Pitch(voice2_note2)
            
            # Calcular direcciones
            dir1 = p1_2.ps - p1_1.ps  # pitch space (incluye octava)
            dir2 = p2_2.ps - p2_1.ps
            
            if dir1 == 0 and dir2 == 0:
                return 'static'
            elif dir1 == 0 or dir2 == 0:
                return 'oblique'
            elif (dir1 > 0 and dir2 > 0) or (dir1 < 0 and dir2 < 0):
                return 'parallel'
            else:
                return 'contrary'
                
        except Exception as e:
            logger.warning(f"Error determinando tipo de movimiento: {e}")
            return 'unknown'

    @staticmethod
    def get_scale_degree_info(note_name: str, key_str: str) -> Dict:
        """Helper para obtener info de grado de escala"""
        try:
            if 'major' not in key_str and 'minor' not in key_str:
                k = music21.key.Key('C', 'major')
            else:
                try:
                    k = music21.key.Key(key_str)
                except:
                    k = music21.key.Key('C', 'major')

            p = music21.pitch.Pitch(note_name)
            tonic = k.tonic
            interval = music21.interval.Interval(tonic, p)
            semitones = interval.semitones % 12
            
            degree_map = {0:1, 1:2, 2:2, 3:3, 4:3, 5:4, 6:4, 7:5, 8:6, 9:6, 10:7, 11:7}
            degree = degree_map.get(semitones, 0)
            is_leading = (semitones == 11)
            
            return {'degree': degree, 'semitones_from_tonic': semitones, 'is_leading_tone': is_leading}
        except:
            return {'degree': 0, 'semitones_from_tonic': 0, 'is_leading_tone': False}

    @staticmethod
    def get_degree_from_chord(chord: Dict, key_str: str) -> str:
        """Helper para obtener grado romano del acorde"""
        if not chord.get('root'): return '?'
        deg = VoiceLeadingUtils.get_scale_degree_info(chord['root'] + '4', key_str)['degree']
        major = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
        minor = ['i', 'ii°', 'III', 'iv', 'V', 'VI', 'vii°']
        try:
            lst = minor if 'minor' in key_str.lower() else major
            return lst[deg-1] if 1 <= deg <= 7 else '?'
        except:
            return '?'

    @staticmethod
    def get_chord_factor(note_name: str, root_name: str) -> str:
        """
        Determina qué factor es una nota respecto a la fundamental.
        
        Usa pitch classes (mod 12) para calcular el intervalo sin importar
        la octava o dirección.
        
        Args:
            note_name: Nota a analizar (ej: 'E3', 'G4', 'B5')
            root_name: Fundamental del acorde (ej: 'C', 'D', 'E♭')
        
        Returns:
            '1', '3', '5', '7', '9', o '?' si no se puede determinar
        """
        try:
            # Asumir octava 4 si no se da
            if not note_name[-1].isdigit(): note_name += '4'
            if not root_name[-1].isdigit(): root_name += '4'
            
            # Crear pitches y calcular diferencia en semitonos (mod 12)
            p_root = music21.pitch.Pitch(root_name)
            p_note = music21.pitch.Pitch(note_name)
            
            # Diferencia en pitch class (0-11)
            semitones = (p_note.pitchClass - p_root.pitchClass) % 12
            
            # Mapear semitonos a factores del acorde
            # 0 = fundamental (P1)
            # 3-4 = tercera (m3, M3)
            # 7 = quinta (P5)
            # 6 = quinta disminuida (d5) o aumentada dependiendo contexto
            # 8 = quinta aumentada (A5)
            # 10-11 = séptima (m7, M7)
            # 2 = novena (M2, m2)
            
            if semitones == 0:
                return '1'
            elif semitones in [3, 4]:  # m3, M3
                return '3'
            elif semitones in [6, 7, 8]:  # d5, P5, A5
                return '5'
            elif semitones in [10, 11]:  # m7, M7
                return '7'
            elif semitones in [1, 2]:  # m9, M9
                return '9'
            else:
                # 5 = 4ªJ, 9 = 6ªM (no son factores típicos de triadas/cuatriadas)
                return '?'
                
        except Exception as e:
            logger.warning(f"Error calculating chord factor for {note_name} from {root_name}: {e}")
            return '?'


# =============================================================================
# CHORD INTEGRATION HELPERS
# =============================================================================

def _dict_to_chord_safe(chord_dict: Dict) -> Optional['Chord']:
    """
    Convierte dict de acorde a Chord class de forma segura.
    
    Usado por reglas para integrar con chord_knowledge.Chord sin romper
    backward compatibility. Si la conversión falla,retorna None y la
    regla puede usar su método legacy.
    
    Args:
        chord_dict: Dict con formato {'S': 'G4', 'A': 'E4', ..., 'root': 'C', ...}
        
    Returns:
        Chord object o None si faltan campos críticos
        
    Example:
        chord_obj = _dict_to_chord_safe(chord1)
        if chord_obj:
            voices_with_7th = chord_obj.get_voices_with_factor('7')
        else:
            # Fallback a método antiguo
            ...
    """
    try:
        from chord_knowledge import Chord
        
        # Campos requeridos: root es crítico
        if 'root' not in chord_dict or not chord_dict['root']:
            return None  # No podemos analizar sin root
        
        # Extraer voces SATB
        voices = {}
        for voice in ['S', 'A', 'T', 'B']:
            note = chord_dict.get(voice)
            if note is not None:
                voices[voice] = note
        
        if len(voices) == 0:
            return None  # No hay voces
        
        # Crear Chord con campos disponibles
        chord = Chord(
            voices=voices,
            root=chord_dict.get('root'),
            quality=chord_dict.get('quality'),
            key=chord_dict.get('key'),
            inversion=chord_dict.get('inversion', 0)
        )
        
        return chord
        
    except Exception as e:
        logger.warning(f"Error converting dict to Chord: {e}")
        return None  # Fallback seguro




# =============================================================================
# REGLA #1: QUINTAS PARALELAS
# =============================================================================

class ParallelFifthsRule(HarmonicRule):
    """
    Detecta quintas paralelas y contrarias entre pares de voces.
    
    Regla base:
        No permitir quintas consecutivas (P5→P5 o A5→A5) entre el mismo
        par de voces en movimiento paralelo o contrario.
    
    Excepciones:
        1. V-VII o VII-V (misma función dominante)
        2. Cambio de disposición del mismo acorde
        3. Primera quinta justa → segunda quinta disminuida
        4. Sexta alemana (implementar en Tier 3)
    
    Color: #FF0000 (RED)
    """
    
    def __init__(self):
        super().__init__(
            name='parallel_fifths',
            tier=RuleTier.CRITICAL,
            color='#FF0000',
            short_msg='Quintas paralelas',
            full_msg='Dos quintas justas consecutivas. Prohibidas tanto en movimiento paralelo como contrario: debilitan la independencia de las voces y oscurecen la claridad armónica.'
        )
        self._add_common_exceptions()
    
    def _add_common_exceptions(self):
        """Añade las excepciones comunes de las quintas paralelas"""
        
        # Excepción 1: Par V-VII (misma función dominante)
        self.add_exception(
            'V_VII_pair',
            lambda c1, c2, ctx: ContextAnalyzer.is_V_VII_pair(c1, c2, ctx.get('key', 'C major')),
            'Permitido entre V-VII o VII-V: ambos tienen función dominante'
        )
        
        # Excepción 2: Cambio de disposición
        self.add_exception(
            'voicing_change',
            lambda c1, c2, ctx: ContextAnalyzer.is_voicing_change(c1, c2),
            'Permitido en cambio de disposición del mismo acorde'
        )
        
        # Excepción 3: Segunda quinta es disminuida
        self.add_exception(
            'second_diminished',
            lambda c1, c2, ctx: self._second_fifth_is_diminished(c1, c2),
            'Permitido cuando la segunda quinta es disminuida (P5→d5)'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta quintas paralelas o contrarias entre todos los pares de voces.
        
        Proceso:
            1. Para cada par de voces (S-A, S-T, S-B, A-T, A-B, T-B)
            2. Calcular intervalo en chord1 y chord2 usando music21
            3. Verificar si ambos son quintas (justa o aumentada) por NOMBRE
            4. Verificar si el movimiento es paralelo o contrario
            5. Si es así, marcar violación
        
        Returns:
            Dict con información de la primera violación encontrada, o None
        """
        voice_pairs = [
            ('S', 'A'), ('S', 'T'), ('S', 'B'),
            ('A', 'T'), ('A', 'B'),
            ('T', 'B')
        ]
        
        for v1, v2 in voice_pairs:
            # Obtener notas de cada voz
            note1_v1 = chord1.get(v1)
            note1_v2 = chord1.get(v2)
            note2_v1 = chord2.get(v1)
            note2_v2 = chord2.get(v2)
            
            # Verificar que todas las notas existen
            if not all([note1_v1, note1_v2, note2_v1, note2_v2]):
                continue
            
            # Verificar si ambos intervalos son quintas usando nombres de music21
            # Esto evita falsos positivos como -8 semitonos (m6 desc) detectado como A5
            is_fifth_1 = VoiceLeadingUtils.is_fifth(note1_v1, note1_v2)
            is_fifth_2 = VoiceLeadingUtils.is_fifth(note2_v1, note2_v2)
            
            if is_fifth_1 and is_fifth_2:
                # Verificar tipo de movimiento
                motion = VoiceLeadingUtils.get_motion_type(
                    note1_v1, note2_v1,
                    note1_v2, note2_v2
                )
                
                # Paralelas (movimiento directo) o Consecutivas (movimiento contrario)
                # Ambas están prohibidas
                if motion in ['parallel', 'contrary']:
                    return {
                        'chord_index': 0,
                        'voices': [v1, v2],
                        'motion_type': motion  # Para diferenciar el mensaje
                    }
        
        return None
    
    def _second_fifth_is_diminished(self, chord1: Dict, chord2: Dict) -> bool:
        """
        Verifica si la segunda quinta es disminuida (P5→d5).
        
        Esta es una excepción porque la quinta disminuida tiene una
        función melódica diferente y tiende a resolver.
        """
        # TODO: Implementar verificación específica
        # Por ahora retorna False (no aplica excepción)
        return False
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        Calcula la confianza del error.
        
        Quintas paralelas son típicamente CERTAIN, pero pueden ser
        HIGH si hay ambigüedad en la detección de voces.
        """
        # Si las voces están muy separadas o hay crossing, reducir confianza
        # Por ahora, siempre CERTAIN
        return ConfidenceLevel.CERTAIN.value


# =============================================================================
# REGLA #2: OCTAVAS PARALELAS/CONSECUTIVAS
# =============================================================================

class ParallelOctavesRule(HarmonicRule):
    """
    Detecta octavas paralelas y consecutivas entre pares de voces.
    
    Regla: Dos octavas justas consecutivas están prohibidas tanto en
    movimiento paralelo (directo) como contrario.
    
    Excepciones:
        Por ahora ninguna implementada (más estricto que quintas).
        TODO: Consultar con experto si existen excepciones pedagógicas.
    """
    
    def __init__(self):
        super().__init__(
            name='parallel_octaves',
            tier=RuleTier.CRITICAL,
            color='#FF0000',
            short_msg='Octavas paralelas',
            full_msg='Dos octavas justas consecutivas. Prohibidas tanto en movimiento paralelo como contrario: debilitan la independencia de las voces y reducen la riqueza armónica.'
        )
        # Por ahora sin excepciones
        # TODO: Implementar si es necesario tras consulta pedagógica
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta octavas paralelas o consecutivas entre todos los pares de voces.
        
        Similar a ParallelFifthsRule pero con is_octave() en lugar de is_fifth().
        
        Args:
            chord1, chord2: Acordes con voces {voz: nota}
            
        Returns:
            Dict con información del error o None si no hay error
        """
        voice_pairs = [
            ('S', 'A'), ('S', 'T'), ('S', 'B'),
            ('A', 'T'), ('A', 'B'),
            ('T', 'B')
        ]
        
        for v1, v2 in voice_pairs:
            # Obtener notas de ambos acordes
            note1_v1 = chord1.get(v1)
            note1_v2 = chord1.get(v2)
            note2_v1 = chord2.get(v1)
            note2_v2 = chord2.get(v2)
            
            # Verificar que todas las notas existen
            if not all([note1_v1, note1_v2, note2_v1, note2_v2]):
                continue
            
            # Verificar si ambos intervalos son octavas usando nombres de music21
            is_octave_1 = VoiceLeadingUtils.is_octave(note1_v1, note1_v2)
            is_octave_2 = VoiceLeadingUtils.is_octave(note2_v1, note2_v2)
            
            if is_octave_1 and is_octave_2:
                # Verificar tipo de movimiento
                motion = VoiceLeadingUtils.get_motion_type(
                    note1_v1, note2_v1,
                    note1_v2, note2_v2
                )
                
                # Paralelas (movimiento directo) o Consecutivas (movimiento contrario)
                # Ambas están prohibidas
                if motion in ['parallel', 'contrary']:
                    return {
                        'chord_index': 0,
                        'voices': [v1, v2],
                        'motion_type': motion  # Para diferenciar el mensaje
                    }
        
        return None
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        Calcula el nivel de confianza para octavas paralelas.
        
        Octavas paralelas son típicamente CERTAIN, similar a quintas.
        
        Args:
            chord1, chord2: Acordes involucrados
            context: Contexto armónico
            
        Returns:
            Nivel de confianza (0-100)
        """
        # Por ahora siempre CERTAIN (100%)
        return ConfidenceLevel.CERTAIN.value


# =============================================================================
# REGLA #3: QUINTAS DIRECTAS (OCULTAS)
# =============================================================================

class DirectFifthsRule(HarmonicRule):
    """
    Detecta quintas directas (ocultas) entre pares de voces.
    
    Regla: Dos voces llegan a quinta justa por movimiento directo
    con la voz superior saltando (no por grado conjunto).
    
    Diferencia con quintas paralelas:
        - Paralelas: P5 → P5 (ya había quinta) → CRITICAL
        - Directas: X → P5 (llegan a quinta) → GRAVE (menos que paralelas)
    
    Severidad según pares:
        - Bajo-Soprano: CERTAIN (100%) - más grave
        - Con Bajo: HIGH (90%)
        - Sin Bajo: MEDIUM (70-80%)
    """
    
    def __init__(self):
        super().__init__(
            name='direct_fifths',
            tier=RuleTier.CRITICAL,  # Para casos más graves (B-S)
            color='#FFFF00',  # YELLOW (menos grave que paralelas RED)
            short_msg='Quinta directa',
            full_msg='Dos voces llegan a quinta justa por movimiento directo. Evita: debilita la independencia de voces.'
        )
        # NUEVO: Añadir excepción de cambio de disposición
        self.add_exception(
            'voicing_change',
            lambda c1, c2, ctx: ContextAnalyzer.is_voicing_change(c1, c2),
            'Permitido en cambio de disposición del mismo acorde'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta quintas directas entre pares de voces.
        
        Condiciones:
        1. Intervalo final = P5 (quinta justa)
        2. Intervalo inicial ≠ P5 (si no, serían paralelas)
        3. Movimiento directo (ambas voces mismo sentido)
        4. Voz superior salta (> 2 semitonos)
        
        Args:
            chord1, chord2: Acordes con voces {voz: nota}
            
        Returns:
            Dict con información del error o None
        """
        voice_pairs = [
            ('S', 'A'), ('S', 'T'), ('S', 'B'),
            ('A', 'T'), ('A', 'B'),
            ('T', 'B')
        ]
        
        for v1, v2 in voice_pairs:
            # Obtener notas
            note1_v1 = chord1.get(v1)
            note1_v2 = chord1.get(v2)
            note2_v1 = chord2.get(v1)
            note2_v2 = chord2.get(v2)
            
            if not all([note1_v1, note1_v2, note2_v1, note2_v2]):
                continue
            
            # Condición 1: Intervalo final debe ser P5
            is_fifth_final = VoiceLeadingUtils.is_perfect_fifth(note2_v1, note2_v2)
            if not is_fifth_final:
                continue  # No llegan a quinta, OK
            
            # Condición 2: Intervalo inicial NO debe ser P5 (si no, son paralelas)
            is_fifth_initial = VoiceLeadingUtils.is_perfect_fifth(note1_v1, note1_v2)
            if is_fifth_initial:
                continue  # Ya detectado por ParallelFifthsRule
            
            # PRIORIDAD: Si intervalo inicial es d5, dejar que UnequalFifthsRule lo maneje
            # Evita duplicación de errores (d5→P5 YA es quinta desigual)
            is_dim_fifth_initial = VoiceLeadingUtils.is_diminished_fifth(note1_v1, note1_v2)
            if is_dim_fifth_initial:
                continue  # Prioridad a UnequalFifthsRule
            
            # Condición 3: Movimiento directo (mismo sentido)
            motion = VoiceLeadingUtils.get_motion_type(
                note1_v1, note2_v1,
                note1_v2, note2_v2
            )
            if motion != 'parallel':
                continue  # No es movimiento directo, OK
            
            
            # VERIFICAR EXCEPCIONES (si se cumple alguna, NO es error)
            # Calcular movimientos de cada voz
            v1_movement = abs(VoiceLeadingUtils.get_interval_object(note1_v1, note2_v1).semitones)
            v2_movement = abs(VoiceLeadingUtils.get_interval_object(note1_v2, note2_v2).semitones)
            
            v1_stepwise = v1_movement <= 2  # Grado conjunto (≤ 2 semitonos)
            v2_stepwise = v2_movement <= 2
            
            # Excepción 1: Partes extremas (B-S)
            if 'B' in [v1, v2] and 'S' in [v1, v2]:
                # Determinar cuál es soprano y cuál es bajo
                if v1 == 'S':
                    soprano_stepwise = v1_stepwise
                    bajo_movement = v2_movement
                else:  # v2 == 'S'
                    soprano_stepwise = v2_stepwise
                    bajo_movement = v1_movement
                
                # Permitir si S hace 2ª Y B hace 3ª, 4ª o 5ª (3-7 semitonos)
                if soprano_stepwise and 3 <= bajo_movement <= 7:
                    continue  # Excepción aplicada, permitido
            
            # Excepción 2: Partes intermedias (resto de pares)
            else:
                # Permitir si UNA hace grado conjunto (pero NO ambas)
                if (v1_stepwise and not v2_stepwise) or (v2_stepwise and not v1_stepwise):
                    continue  # Excepción aplicada, permitido
            
            # NO se cumple ninguna excepción → ERROR
            return {
                'chord_index': 0,
                'voices': [v1, v2],
                'upper_voice': v1
            }
        
        return None
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        Calcula confianza según severidad del par de voces.
        
        Bajo-Soprano: CERTAIN (100%) - más audible y grave
        Con Bajo: HIGH (90%)
        Sin Bajo: MEDIUM (70-80%)
        """
        # Buscar cuál fue el error detectado
        violation = self._detect_violation(chord1, chord2)
        if not violation:
            return 0
        
        voices = violation['voices']
        v1, v2 = voices[0], voices[1]
        
        # Severidad según pares
        if 'B' in voices and 'S' in voices:
            return ConfidenceLevel.CERTAIN.value  # 100%
        elif 'B' in voices:
            return 90  # HIGH (con bajo pero no S)
        elif ('T' in voices or 'A' in voices) and 'S' in voices:
            return 80  # MEDIUM-HIGH (voces externas sin bajo)
        else:
            return 70  # MEDIUM (voces internas)


# =============================================================================
# REGLA #4: OCTAVAS DIRECTAS (OCULTAS)
# =============================================================================

class DirectOctavesRule(HarmonicRule):
    """
    Detecta octavas directas (ocultas) entre pares de voces.
    
    Regla: Dos voces llegan a octava justa por movimiento directo.
    
    Similar a DirectFifthsRule pero:
    - Llegar a P8 en lugar de P5
    - Excepción B-S MÁS ESTRICTA: soprano sube 1 semitono (sensible→tónica)
      Y bajo sube 4ª justa (5 semitonos)
    
    Severidad:
        - B-S: CERTAIN (100%)
        - Con Bajo: HIGH (90%)
        - Sin Bajo: MEDIUM (70-80%)
    """
    
    def __init__(self):
        super().__init__(
            name='direct_octaves',
            tier=RuleTier.CRITICAL,
            color='#FFFF00',  # YELLOW (igual que quintas directas)
            short_msg='Octava directa',
            full_msg='Dos voces llegan a octava justa por movimiento directo. Evita: debilita la independencia de voces.'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta octavas directas entre pares de voces.
        
        Condiciones:
        1. Intervalo final = P8 o P1 (octava justa o unísono)
        2. Intervalo inicial ≠ P8/P1 (si no, serían paralelas)
        3. Movimiento directo (ambas voces mismo sentido)
        4. NO cumple excepciones
        
        Excepciones:
        - B-S: soprano +1 semitono ascendente Y bajo +5 semitonos (4ª justa)
        - Otras: una voz hace 2ª (pero no ambas)
        
        Returns:
            Dict con información del error o None
        """
        voice_pairs = [
            ('S', 'A'), ('S', 'T'), ('S', 'B'),
            ('A', 'T'), ('A', 'B'),
            ('T', 'B')
        ]
        
        for v1, v2 in voice_pairs:
            note1_v1 = chord1.get(v1)
            note1_v2 = chord1.get(v2)
            note2_v1 = chord2.get(v1)
            note2_v2 = chord2.get(v2)
            
            if not all([note1_v1, note1_v2, note2_v1, note2_v2]):
                continue
            
            # Condición 1: Intervalo final debe ser P8 o P1
            is_octave_final = VoiceLeadingUtils.is_octave(note2_v1, note2_v2)
            if not is_octave_final:
                continue
            
            # Condición 2: Intervalo inicial NO debe ser P8/P1
            is_octave_initial = VoiceLeadingUtils.is_octave(note1_v1, note1_v2)
            if is_octave_initial:
                continue  # Ya detectado por ParallelOctavesRule
            
            # Condición 3: Movimiento directo
            motion = VoiceLeadingUtils.get_motion_type(
                note1_v1, note2_v1,
                note1_v2, note2_v2
            )
            if motion != 'parallel':
                continue
            
            # VERIFICAR EXCEPCIONES
            # Calcular movimientos (con signo para dirección)
            v1_interval = VoiceLeadingUtils.get_interval_object(note1_v1, note2_v1)
            v2_interval = VoiceLeadingUtils.get_interval_object(note1_v2, note2_v2)
            
            v1_semitones = v1_interval.semitones  # Con signo (+ sube, - baja)
            v2_semitones = v2_interval.semitones
            
            v1_stepwise = abs(v1_semitones) <= 2
            v2_stepwise = abs(v2_semitones) <= 2
            
            # Excepción 1: Partes extremas (B-S) - MÁS ESTRICTA
            if 'B' in [v1, v2] and 'S' in [v1, v2]:
                # Determinar quién es soprano y quién es bajo
                if v1 == 'S':
                    soprano_semitones = v1_semitones
                    bajo_semitones = v2_semitones
                else:
                    soprano_semitones = v2_semitones
                    bajo_semitones = v1_semitones
                
                # Permitir SI:
                # - Soprano sube 1 semitono (+1, sensible→tónica)
                # - Bajo sube 5 semitonos (+5, 4ª justa ascendente)
                if soprano_semitones == 1 and bajo_semitones == 5:
                    continue  # Excepción aplicada
            
            # Excepción 2: Partes intermedias (igual que quintas)
            else:
                # Permitir si UNA hace grado conjunto (pero NO ambas)
                if (v1_stepwise and not v2_stepwise) or (v2_stepwise and not v1_stepwise):
                    continue
            
            # NO se cumple ninguna excepción → ERROR
            return {
                'chord_index': 0,
                'voices': [v1, v2],
                'upper_voice': v1
            }
        
        return None
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        Calcula confianza según severidad del par de voces.
        
        Mismo sistema que DirectFifthsRule.
        """
        violation = self._detect_violation(chord1, chord2)
        if not violation:
            return 0
        
        voices = violation['voices']
        
        if 'B' in voices and 'S' in voices:
            return ConfidenceLevel.CERTAIN.value  # 100%
        elif 'B' in voices:
            return 90  # HIGH
        elif ('T' in voices or 'A' in voices) and 'S' in voices:
            return 80  # MEDIUM-HIGH
        else:
            return 70  # MEDIUM


# =============================================================================
# REGLA #5: QUINTAS DESIGUALES (d5→P5)
# =============================================================================

class UnequalFifthsRule(HarmonicRule):
    """
    Detecta quintas desiguales: paso de quinta disminuida a quinta justa
    cuando el bajo está involucrado.
    
    Regla: Prohibir d5 → P5 si el bajo es una de las voces del par.
    
    Excepción:
        - 10as paralelas en B-S (permite d5→P5 en otras voces)
    
    Severidad:
        - Con Bajo: HIGH (90%)
    
    Color: ORANGE (advertencia seria, menos que paralelas)
    """
    
    def __init__(self):
        super().__init__(
            name='unequal_fifths',
            tier=RuleTier.CRITICAL,
            color='#FFA500',  # ORANGE
            short_msg='Quintas desiguales',
            full_msg='Paso de quinta disminuida a quinta justa con bajo. Evita: movimiento armónico inadecuado.'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta quintas desiguales (d5→P5) con bajo.
        
        Condiciones:
        1. Intervalo inicial = d5 (quinta disminuida)
        2. Intervalo final = P5 (quinta justa)
        3. Bajo involucrado en el par
        4. NO cumple excepción 10as paralelas B-S
        
        Returns:
            Dict con información del error o None
        """
        # Solo pares que involucran al bajo
        bass_pairs = [
            ('B', 'S'),
            ('B', 'A'),
            ('B', 'T')
        ]
        
        for v1, v2 in bass_pairs:
            note1_v1 = chord1.get(v1)
            note1_v2 = chord1.get(v2)
            note2_v1 = chord2.get(v1)
            note2_v2 = chord2.get(v2)
            
            if not all([note1_v1, note1_v2, note2_v1, note2_v2]):
                continue
            
            # Condición 1: Intervalo inicial debe ser d5
            is_dim_fifth_initial = VoiceLeadingUtils.is_diminished_fifth(note1_v1, note1_v2)
            if not is_dim_fifth_initial:
                continue
            
            # Condición 2: Intervalo final debe ser P5
            is_perf_fifth_final = VoiceLeadingUtils.is_perfect_fifth(note2_v1, note2_v2)
            if not is_perf_fifth_final:
                continue
            
            # Condición 3: Verificar excepción 10as paralelas B-S
            if self._has_parallel_tenths_BS(chord1, chord2):
                continue  # Excepción aplicada
            
            # TODAS las condiciones se cumplen → ERROR
            return {
                'chord_index': 0,
                'voices': [v1, v2],
                'upper_voice': v2 if v1 == 'B' else v1
            }
        
        return None
    
    def _has_parallel_tenths_BS(self, chord1: Dict, chord2: Dict) -> bool:
        """
        Verifica si Bajo-Soprano forman 10as paralelas.
        
        Una 10ª puede ser M10, m10, o sus equivalentes simples M3, m3.
        Deben moverse en movimiento paralelo.
        
        Returns:
            True si hay 10as paralelas en B-S
        """
        note1_B = chord1.get('B')
        note1_S = chord1.get('S')
        note2_B = chord2.get('B')
        note2_S = chord2.get('S')
        
        if not all([note1_B, note1_S, note2_B, note2_S]):
            return False
        
        # Obtener intervalos B-S en ambos acordes
        interval1 = VoiceLeadingUtils.get_interval_object(note1_B, note1_S)
        interval2 = VoiceLeadingUtils.get_interval_object(note2_B, note2_S)
        
        if not interval1 or not interval2:
            return False
        
        # Verificar si son 10as (o 3as, que son 10as simples)
        tenth_names = ['M10', 'm10', 'M3', 'm3', 'A10', 'd10', 'A3']
        is_tenth_1 = interval1.simpleName in tenth_names
        is_tenth_2 = interval2.simpleName in tenth_names
        
        if not (is_tenth_1 and is_tenth_2):
            return False
        
        # Verificar movimiento paralelo
        motion = VoiceLeadingUtils.get_motion_type(
            note1_B, note2_B,
            note1_S, note2_S
        )
        
        return motion == 'parallel'
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        Calcula confianza.
        
        Siempre HIGH (90%) ya que solo detectamos con bajo.
        """
        violation = self._detect_violation(chord1, chord2)
        if not violation:
            return 0
        
        return 90  # HIGH - con bajo siempre


# =============================================================================
# REGLA #6: RESOLUCIÓN DE SENSIBLE (Leading Tone)
# =============================================================================

class LeadingToneResolutionRule(HarmonicRule):
    """
    Regla: La sensible en función dominante (V, VII) debe resolver a la Tónica.
    
    Definición precisa:
        - La sensible es la 3ª mayor del acorde de V.
        - En el acorde de vii (diminismo de V sin fundamental), la sensible actúa como fundamental aparente.
        - En otros grados (ej: iii), la nota sensible (VII grado escala) es la 5ª del acorde y NO funciona como sensible activa.
    
    Excepciones Pedagógicas:
        1. Voz Interior (Alto/Tenor): Permite salto de 3ª descendente a la 5ª del acorde final (Leading Tone Drop)
           para completar la sonoridad del acorde de resolución.
        2. Tónica no presente (Cadencia Rota V-vi/V-VI):
           - Estándar: La sensible DEBE resolver a la tónica (que es la 3ª del acorde vi/VI).
           - Excepción real: Si el acorde destino NO contiene la nota tónica (ej: modulación lejana), no obliga.
        3. Cambio de disposición (V-VII): Entre funciones dominantes, movimiento libre.
        
    Color: #CD853F (Peru - Marrón claro)
    """
    
    def __init__(self):
        super().__init__(
            name='leading_tone_resolution',
            tier=RuleTier.CRITICAL,
            color='#CD853F',  # Peru (Light Brown) - "Correcto" es verde, esto es error.
            short_msg='Sensible sin resolver',
            full_msg='La sensible en función dominante debe resolver en tónica (o su octava).'
        )
        
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si la sensible NO resuelve correctamente.
        Abarca:
        1. Sensible de la tonalidad (Grado 7).
        2. Sensible secundaria (3ª de un Dominante local).
        """
        key = chord1.get('key', 'C major') 
        
        # Analizar cada voz en Chord1
        for voice_name, note1 in chord1.items():
            if voice_name not in ['S', 'A', 'T', 'B']:
                continue
                
            is_sensible_candidate = False
            is_local_sensible = False
            
            # --- CHEQUEO 1: Sensible Tonal (Grado 7) ---
            if key:
                info = VoiceLeadingUtils.get_scale_degree_info(note1, key)
                if info['is_leading_tone']:
                    # FIX: Solo si está en acorde de función dominante
                    # La sensible solo exige resolución en acordes dominantes (V, vii°)
                    # En otros acordes (ej: iii7 donde es la 5ª), NO es sensible activa
                    chord_degree = VoiceLeadingUtils.get_degree_from_chord(chord1, key)
                    
                    # Grados dominantes (igual para mayor y menor)
                    # CORREGIDO: Usar startswith para incluir V7, V7,+, etc.
                    is_dominant_chord = (
                        chord_degree.startswith('V') or  # V, V7, V7,+, V6, etc.
                        chord_degree.startswith('vii°') or  # vii°, vii°7
                        chord_degree.startswith('viiø')  # viiø7
                    )
                    
                    if is_dominant_chord:
                        is_sensible_candidate = True
                    # Si no es dominante, NO marcar como sensible activa
            
            # --- CHEQUEO 2: Sensible Local (3ª de Dominante Secundaria) ---
            # Si no es sensible tonal, verificamos si actúa como sensible local.
            # Criterio ESTRICTO:
            # - Chord1 es Major o Dominant7
            # - La nota es la 3ª de Chord1
            # - Chord1 -> Chord2 es movimiento V -> I (Fundamental baja 5ta justa / sube 4ta justa)
            # - NUEVO: El movimiento NO es una progresión diatónica normal
            #   (I→V no cuenta, pero D7→G sí, cuando D7 no es el V de la tonalidad)
            
            if not is_sensible_candidate:
                root1 = chord1.get('root')
                root2 = chord2.get('root')
                
                # Solo considerar sensible local si hay movimiento de fundamentales V-I
                if root1 and root2:
                    # Verificar si es movimiento V-I (P5 descendente / P4 ascendente)
                    interval_roots = VoiceLeadingUtils.get_interval_object(root1 + '4', root2 + '4')
                    
                    if interval_roots and interval_roots.simpleName in ['P4', 'P5']:
                        # CRITICAL FIX: Usar degree del analizador en lugar de recalcular
                        # VoiceLeadingUtils.get_degree_from_chord() pierde información de secundarias
                        # (ej: V7/V se convierte en 'ii' diatónico)
                        chord1_degree = chord1.get('degree', '?')
                        
                        # Verificar si es dominante secundaria (contiene '/')
                        # O si es un acorde cromático (contiene '#' o 'b' pero no es diatónico)
                        is_secondary_dominant = '/' in chord1_degree
                        
                        # Grados diatónicos comunes (no son dominantes secundarias)
                        diatonic_degrees = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°',
                                            'i', 'II°', 'III', 'iv', 'VII', 'VI']
                        
                        # Marcar como sensible local si:
                        # 1. Es dominante secundaria (V/x, vii°/x)
                        # 2. O NO es un grado diatónico simple
                        if is_secondary_dominant or chord1_degree not in diatonic_degrees:
                            # Verificar si note1 es la 3ª Mayor (Sensible local)
                            try:
                                p_root = music21.pitch.Pitch(root1)
                                p_note = music21.pitch.Pitch(note1)
                                diff = (p_note.pitchClass - p_root.pitchClass) % 12
                                if diff == 4:  # M3 = 4 semitonos
                                    is_sensible_candidate = True
                                    is_local_sensible = True
                            except:
                                pass

            if not is_sensible_candidate:
                continue
            
            # --- VALIDACIÓN DE RESOLUCIÓN ---
            
            # FILTRO: En iii (III), la nota sensible es la 5ª y no tiene obligación de resolver.
            # (Solo aplica si fue detectada por Grado 7 tonal)
            # NOTA: Con el fix arriba, esto ya no debería activarse, pero lo mantenemos como seguridad
            if key:
                chord_degree = VoiceLeadingUtils.get_degree_from_chord(chord1, key)
                if chord_degree in ['III', 'iii']:
                    continue
 

            # Identificar nota destino
            note2 = chord2.get(voice_name)
            if not note2: 
                continue
            
            # 1. Chequeo: ¿Resolvió a Tónica Tonal? (Solo si era sensible tonal)
            if key:
                info2 = VoiceLeadingUtils.get_scale_degree_info(note2, key)
                if info2['degree'] == 1:
                    continue # Resolvió a Tónica Global

            # 2. Chequeo: ¿Resolvió ascendiendo semitono? (Criterio General)
            semitones = 0
            interval_obj = VoiceLeadingUtils.get_interval_object(note1, note2)
            if interval_obj:
                semitones = interval_obj.semitones
            
            if semitones == 1:
                continue # Resolvió subiendo semitono (F# -> G, B -> C)
            
            # Excepción Cadencia Rota (V-vi).
            if key:
                chord2_degree = VoiceLeadingUtils.get_degree_from_chord(chord2, key)
                
                # Si no podemos determinar el grado ('?'), asumimos que podría ser tónica
                if chord2_degree == '?':
                    # No permitir excepción, continuar validando
                    pass
                else:
                    is_dest_submediant = (chord2_degree in ['vi', 'VI', 'VIb', 'bVI'])
                    
                    if is_dest_submediant:
                        pass 
                    else:
                        if chord2_degree not in ['I', 'i'] and not is_local_sensible:
                              continue
            
            # Excepción: V-VII (misma función)
            if key and ContextAnalyzer.is_V_VII_pair(chord1, chord2, key):
                continue
            
            # Excepción: V6 → vi (Cadencia Rota en 1ª inversión - SOLO modo mayor)
            # En V6 (1ª inversión), la sensible está en el bajo
            # Puede bajar a la fundamental del vi sin resolver a tónica
            # Condiciones:
            # 1. Solo sensible TONAL (no secundarias)
            # 2. Voz Bajo
            # 3. Modo mayor
            # 4. Acorde destino es vi
            if key and voice_name == 'B' and not is_local_sensible:
                # Verificar que es modo mayor
                if 'major' in key.lower():
                    chord2_degree = VoiceLeadingUtils.get_degree_from_chord(chord2, key)
                    # Si el acorde destino es vi (submediante)
                    if chord2_degree == 'vi':
                        # Verificar que note2 es la fundamental del vi
                        root2 = chord2.get('root')
                        if root2:
                            try:
                                factor2 = VoiceLeadingUtils.get_chord_factor(note2, root2)
                                if factor2 == '1':
                                    # Cadencia rota V6 → vi válida
                                    continue
                            except:
                                pass
                
            # Excepción: Resolución Indirecta (Voz Interna)
            # Aplica para TODAS las sensibles (tonales y locales)
            # 
            # Condiciones para resolución indirecta válida:
            # 1. La sensible baja a la 5ª del acorde de resolución
            # 2. La voz inmediatamente superior contiene la tónica (resolución cubierta)
            if voice_name in ['A', 'T']:
                # Obtener fundamental del acorde destino (tónica esperada)
                root2 = chord2.get('root')
                if root2:
                    try:
                        # Verificar condición 1: ¿note2 es la 5ª del acorde destino?
                        factor2 = VoiceLeadingUtils.get_chord_factor(note2, root2)
                        is_fifth = (factor2 == '5')
                        
                        if is_fifth:
                            # Verificar condición 2: ¿La voz superior tiene la tónica?
                            # A → verificar S, T → verificar A
                            upper_voice = 'S' if voice_name == 'A' else 'A'
                            upper_note = chord2.get(upper_voice)
                            
                            if upper_note:
                                upper_factor = VoiceLeadingUtils.get_chord_factor(upper_note, root2)
                                has_tonic_above = (upper_factor == '1')
                                
                                if has_tonic_above:
                                    # Resolución indirecta válida
                                    continue
                    except:
                        pass 
            
            return {
                'chord_index': 0,
                'voices': [voice_name], 
                'upper_voice': voice_name
            }
            
        return None

# =============================================================================
# REGLA #7: RESOLUCIÓN DE SÉPTIMA DE DOMINANTE
# =============================================================================

class SeventhResolutionRule(HarmonicRule):
    """
    Regla: La séptima de un acorde (especialmente dominante) debe resolver 
    descendiendo por grado conjunto (1 o 2 semitonos).
    
    Excepciones:
        1. Mismo acorde (cambio de inversión/disposición).
        2. Resolución diferida/ornamental (No implementada en fase 1, se marca strict).
        3. Transferencia de la séptima (otra voz toma la resolución) - Pedagogía estricta prefiere evitarlo.
        
    Color: #FF0000 (RED)
    """
    
    def __init__(self):
        super().__init__(
            name='seventh_resolution',
            tier=RuleTier.CRITICAL,
            color='#FF0000',
            short_msg='Séptima sin resolver',
            full_msg='La séptima del acorde es una disonancia obligada y debe resolver descendiendo por grado.'
        )
        
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si la 7ª del acorde NO resuelve correctamente.
        
        Refactorizado para usar Chord class con fallback completo.
        """
        # Intentar usar Chord (método nuevo)
        chord1_obj = _dict_to_chord_safe(chord1)
        
        if chord1_obj:
            return self._detect_violation_chord(chord1_obj, chord2)
        else:
            return self._detect_violation_legacy(chord1, chord2)
    
    def _detect_violation_chord(self, chord1_obj, chord2: Dict) -> Optional[Dict]:
        """Método refactorizado usando Chord class."""
        from chord_knowledge import Chord
        
        # Reconstruir chord1 dict para compatibilidad con is_voicing_change
        chord1 = chord1_obj.voices.copy()
        chord1['root'] = chord1_obj.root
        chord1['quality'] = chord1_obj.quality
        chord1['key'] = chord1_obj.key
        chord1['inversion'] = chord1_obj.inversion
        
        # Excepción: cambio de disposición
        if ContextAnalyzer.is_voicing_change(chord1, chord2):
            return None
        
        # Usar Chord para encontrar voces con 7ª - MÁS SIMPLE
        voices_with_7th = chord1_obj.get_voices_with_factor('7')
        
        for voice in voices_with_7th:
            note1 = chord1_obj.voices[voice]
            note2 = chord2.get(voice)
            if not note2: continue
            
            iv = VoiceLeadingUtils.get_interval_object(note1, note2)
            if not iv: continue
            
            semitones = iv.semitones
            
            # REGLA: Debe bajar -1 o -2 semitonos
            if semitones == -1 or semitones == -2:
                continue
            
            return {'chord_index': 0, 'voices': [voice], 'upper_voice': voice}
        
        return None
    
    def _detect_violation_legacy(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """Método original SIN CAMBIOS (fallback)."""
        root1 = chord1.get('root')
        if not root1: return None
        
        if ContextAnalyzer.is_voicing_change(chord1, chord2):
            return None
            
        for voice, note1 in chord1.items():
            if voice not in ['S','A','T','B']: continue
            
            factor = VoiceLeadingUtils.get_chord_factor(note1, root1)
            if factor != '7': continue
            
            note2 = chord2.get(voice)
            if not note2: continue
            
            iv = VoiceLeadingUtils.get_interval_object(note1, note2)
            if not iv: continue
            
            semitones = iv.semitones
            
            if semitones == -1 or semitones == -2:
                continue
            
            return {'chord_index': 0, 'voices': [voice], 'upper_voice': voice}
            
        return None



# =============================================================================
# MOTOR DE REGLAS
# =============================================================================

# =============================================================================
# REGLA #8: CRUZAMIENTO DE VOCES (VOICE CROSSING)
# =============================================================================

class VoiceCrossingRule(HarmonicRule):
    """
    Detecta cruzamiento de voces (voice crossing).
    
    Regla:
        Las voces deben mantener su orden natural de grave a agudo:
        Bajo < Tenor < Alto < Soprano
        
        Si una voz grave está por encima de una voz aguda → Error
    
    Migrada desde: app.py (líneas 66-71)
    
    Pedagogía:
        - El cruzamiento dificulta la independencia de las voces
        - Crea confusión auditiva sobre qué voz hace qué
        - Es un error CRÍTICO en escritura a 4 voces
    
    Excepciones (futuras):
        - Intercambio temporal de voces (no implementada)
        - Cruce momentáneo en paso (no implementada)
    """
    
    def __init__(self):
        super().__init__(
            name='voice_crossing',
            tier=RuleTier.CRITICAL,
            color='#FF0000',  # RED - Error grave
            short_msg='Cruzamiento de voces',
            full_msg='Las voces se cruzan: una voz grave está por encima de una voz aguda, '
                     'violando el orden natural Bajo < Tenor < Alto < Soprano'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si las voces se cruzan en chord1.
        
        Verificamos 3 pares de voces adyacentes:
        - B-T: Bajo debe estar por debajo del Tenor
        - T-A: Tenor debe estar por debajo del Alto
        - A-S: Alto debe estar por debajo de la Soprano
        
        Returns:
            Dict con voices cruzadas o None si no hay cruces
        """
        voice_pairs = [('B', 'T'), ('T', 'A'), ('A', 'S')]
        
        for lower_voice, upper_voice in voice_pairs:
            note_lower = chord1.get(lower_voice)
            note_upper = chord1.get(upper_voice)
            
            # Si falta alguna nota, no podemos validar este par
            if not note_lower or not note_upper:
                continue
            
            try:
                # Convertir a pitch space (ps)
                p_lower = music21.pitch.Pitch(note_lower)
                p_upper = music21.pitch.Pitch(note_upper)
                
                # Verificar cruzamiento: voz grave > voz aguda
                if p_lower.ps > p_upper.ps:
                    return {
                        'chord_index': 0,
                        'voices': [lower_voice, upper_voice],
                        'upper_voice': upper_voice
                    }
            
            except Exception as e:
                logger.warning(f"Error analizando cruce {lower_voice}-{upper_voice}: {e}")
                continue
        
        return None
    
    def _calculate_confidence(self, chord1, chord2, context):
        """
        Cruzamiento de voces es INEQUÍVOCO.
        """
        return ConfidenceLevel.CERTAIN.value  # 100%




# =============================================================================
# REGLA #9: DISTANCIA MÁXIMA ENTRE VOCES (MAXIMUM DISTANCE)
# =============================================================================

class MaximumDistanceRule(HarmonicRule):
    """
    Detecta separación excesiva (>8ª) entre voces contiguas.
    
    Regla:
        Las voces superiores no deben separarse más de una octava (12 semitonos):
        - Soprano-Alto: máximo 12 semitonos
        - Alto-Tenor: máximo 12 semitonos
        - Tenor-Bajo: SIN LÍMITE (puede ser >8ª)
    
    Migrada desde: app.py (líneas 74-79)
    
    Pedagogía:
        - Separación excesiva crea "vacío" armónico
        - Dificulta sonoridad homogénea del conjunto
        - El bajo tiene más libertad por función armónica
    
    Excepciones (futuras):
        - Contextos donde la separación es obligada (no implementada)
    """
    
    def __init__(self):
        super().__init__(
            name='maximum_distance',
            tier=RuleTier.IMPORTANT,
            color='#FFFF00',  # YELLOW - Advertencia importante
            short_msg='Distancia excesiva entre voces',
            full_msg='La separación entre voces contiguas supera la octava (12 semitonos), '
                     'creando un vacío armónico no recomendado'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si voces contiguas están separadas >8ª en chord1.
        
        Solo verificamos voces superiores:
        - S-A: Soprano y Alto
        - T-A: Tenor y Alto
        
        NO verificamos T-B (permitido >8ª)
        
        Returns:
            Dict con voices afectadas o None si distancias válidas
        """
        # Pares a verificar (voz_inferior, voz_superior)
        voice_pairs = [
            ('A', 'S'),  # Alto-Soprano
            ('T', 'A')   # Tenor-Alto
        ]
        
        for lower_voice, upper_voice in voice_pairs:
            note_lower = chord1.get(lower_voice)
            note_upper = chord1.get(upper_voice)
            
            # Si falta alguna nota, no podemos validar
            if not note_lower or not note_upper:
                continue
            
            try:
                # Convertir a pitch space
                p_lower = music21.pitch.Pitch(note_lower)
                p_upper = music21.pitch.Pitch(note_upper)
                
                # Calcular distancia absoluta
                distance = abs(p_upper.ps - p_lower.ps)
                
                # Verificar si excede octava (12 semitonos)
                if distance > 12:
                    return {
                        'chord_index': 0,
                        'voices': [lower_voice, upper_voice],
                        'upper_voice': upper_voice,
                        'distance_semitones': distance
                    }
            
            except Exception as e:
                logger.warning(f"Error analizando distancia {lower_voice}-{upper_voice}: {e}")
                continue
        
        return None
    
    def _calculate_confidence(self, chord1, chord2, context):
        """
        Distancia excesiva es clara pero no tan grave como cruzamiento.
        """
        return ConfidenceLevel.HIGH.value  # 80%




# =============================================================================
# REGLA #10: INVASIÓN/SUPERPOSICIÓN DE VOCES (VOICE OVERLAP)
# =============================================================================

class VoiceOverlapRule(HarmonicRule):
    """
    Detecta invasión de voces entre acordes consecutivos (voice overlap).
    
    Regla:
        Una voz no debe invadir el registro que ocupaba otra voz en el acorde anterior:
        - Invasión descendente: voz superior baja más que donde estaba voz inferior
        - Invasión ascendente: voz inferior sube más que donde estaba voz superior
    
    Migrada desde: app.py (líneas 94-101)
    
    Pedagogía:
        - Crea confusión sobre identidad de voces
        - Dificulta seguimiento auditivo de líneas melódicas
        - Puede causar cruces momentáneos no deseados
    
    Excepciones (futuras):
        - Intercambio intencional de voces (no implementada)
    """
    
    def __init__(self):
        super().__init__(
            name='voice_overlap',
            tier=RuleTier.IMPORTANT,
            color='#FFFF00',  # YELLOW - Advertencia importante
            short_msg='Invasión de voces',
            full_msg='Una voz invade el registro que ocupaba otra voz en el acorde anterior, '
                     'creando confusión en la conducción de voces'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta invasiones entre chord1 y chord2.
        
        Para cada par de voces adyacentes (B-T, T-A, A-S):
        - Invasión descendente: chord2[superior] < chord1[inferior]
        - Invasión ascendente: chord2[inferior] > chord1[superior]
        
        Returns:
            Dict con voices afectadas o None si no hay invasiones
        """
        voice_pairs = [('B', 'T'), ('T', 'A'), ('A', 'S')]
        
        for lower_voice, upper_voice in voice_pairs:
            note1_lower = chord1.get(lower_voice)
            note1_upper = chord1.get(upper_voice)
            note2_lower = chord2.get(lower_voice)
            note2_upper = chord2.get(upper_voice)
            
            # Necesitamos las 4 notas para validar
            if not all([note1_lower, note1_upper, note2_lower, note2_upper]):
                continue
            
            try:
                # Convertir a pitch space
                p1_lower = music21.pitch.Pitch(note1_lower).ps
                p1_upper = music21.pitch.Pitch(note1_upper).ps
                p2_lower = music21.pitch.Pitch(note2_lower).ps
                p2_upper = music21.pitch.Pitch(note2_upper).ps
                
                # Invasión descendente: voz superior baja más que inferior estaba
                if p2_upper < p1_lower:
                    return {
                        'chord_index': 0,
                        'voices': [lower_voice, upper_voice],
                        'upper_voice': upper_voice,
                        'invasion_type': 'descending'
                    }
                
                # Invasión ascendente: voz inferior sube más que superior estaba
                if p2_lower > p1_upper:
                    return {
                        'chord_index': 0,
                        'voices': [lower_voice, upper_voice],
                        'upper_voice': lower_voice,  # La que invade (lower sube)
                        'invasion_type': 'ascending'
                    }
            
            except Exception as e:
                logger.warning(f"Error analizando overlap {lower_voice}-{upper_voice}: {e}")
                continue
        
        return None
    
    def _calculate_confidence(self, chord1, chord2, context):
        """
        Invasión de voces es clara pero menos grave que cruzamiento.
        """
        return ConfidenceLevel.HIGH.value  # 80%




# =============================================================================
# REGLA #11: DUPLICACIÓN DE SENSIBLE (DUPLICATED LEADING TONE)
# =============================================================================

class DuplicatedLeadingToneRule(HarmonicRule):
    """
    Detecta duplicación de la sensible en acordes de función dominante.
    
    Regla:
        La sensible NO debe aparecer en más de una voz simultáneamente.
        
        Contexto: Solo aplica en acordes dominantes (V, vii°)
        
        Razón pedagógica:
        - La sensible tiene fuerte tendencia resolutiva a la tónica
        - Si está duplicada, ambas voces quieren resolver → quintas/octavas paralelas
        - Desequilibra la sonoridad del acorde
    
    Detección:
        En V: La sensible es la 3ª Mayor (4 semitonos sobre la fundamental)
        En vii°: La sensible es la fundamental
    
    Color: #FF0000 (RED) - Error crítico
    """
    
    def __init__(self):
        super().__init__(
            name='duplicated_leading_tone',
            tier=RuleTier.CRITICAL,
            color='#FF0000',  # RED
            short_msg='Sensible duplicada',
            full_msg='La sensible está duplicada en múltiples voces, '
                     'lo cual crea problemas de resolución y desequilibra el acorde'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si la sensible está duplicada en chord1 O chord2.
        
        CAMBIO CRÍTICO: Debemos checkear CADA acorde independientemente,
        SIN retorno temprano. La duplicación de sensible es un error INTERNO
        del acorde, no de la progresión.
        
        Retorna la PRIMERA violación encontrada (chord1 tiene prioridad).
        Si chord1 NO tiene error, chequea chord2.
        
        Returns:
            Dict con voces que tienen la sensible duplicada, o None
        """
        # Primero checkear chord1
        result = self._check_chord_for_duplicated_leading_tone(chord1)
        if result:
            return result
        
        # Solo si chord1 NO tiene error, checkear chord2
        result = self._check_chord_for_duplicated_leading_tone(chord2)
        if result:
            # IMPORTANTE: marcar que el error es en chord2, no chord1
            result['chord_index'] = 1  # Indicar que es el segundo acorde
            return result
        
        return None
    
    def _check_chord_for_duplicated_leading_tone(self, chord: Dict) -> Optional[Dict]:
        """
        Verifica si UN acorde tiene sensible duplicada.
        
        ARQUITECTURA BASADA EN FACTORES (Principio del Usuario):
        1. Sistema conoce factores de acordes
        2. En dominantes, sensible = factor '3' (3ª Mayor)
        3. Detectar cuántas voces tienen factor '3'
        4. Si > 1 → duplicación
        """
        # 1. Verificar si es acorde dominante
        chord_degree = chord.get('degree')
        
        is_dominant = False
        if chord_degree:
            is_dominant = (
                chord_degree in ['V', 'vii°'] or
                chord_degree.startswith('V/') or
                chord_degree.startswith('vii') and '/' in chord_degree
            )
        
        if not is_dominant:
            return None  # No es dominante, no aplica
        
        # 2. Obtener la fundamental del acorde
        root = chord.get('root')
        
        if not root:
            # Fallback: usar bajo
            bass_note = chord.get('B')
            if bass_note:
                try:
                    root = music21.pitch.Pitch(bass_note).name
                except:
                    return None
            else:
                return None
        
        # 3. Identificar cuáles notas son el factor '3' (sensible en dominantes)
        voices_with_third = []
        
        for voice in ['S', 'A', 'T', 'B']:
            note = chord.get(voice)
            if not note:
                continue
            
            try:
                # Usar el conocimiento de factores del sistema
                factor = VoiceLeadingUtils.get_chord_factor(note, root)
                
                if factor == '3':  # Esta nota es la 3ª del acorde = sensible
                    voices_with_third.append(voice)
            except Exception as e:
                logger.warning(f"Error obteniendo factor de {note} en {root}: {e}")
                continue
        
        # 4. Si hay más de una voz con el factor '3' → Sensible duplicada
        if len(voices_with_third) > 1:
            return {
                'chord_index': 0,
                'voices': voices_with_third,
                'upper_voice': voices_with_third[0]
            }
        
        return None
    
    def _calculate_confidence(self, chord1, chord2, context):
        """
        Duplicar la sensible es un error inequívoco en pedagogía estricta.
        """
        return 100  # Confianza máxima


class DuplicatedSeventhRule(HarmonicRule):
    """
    Regla: Prohibir duplicación de la séptima en acordes de 7ª.
    
    Pedagogía:
    - Las disonancias (7ª, 9ª, alteraciones) NO deben duplicarse
    - Duplicar la 7ª aumenta tensión excesivamente
    - Problemas en resolución (dos 7as descendiendo)
    
    Arquitectura basada en factores (igual que DuplicatedLeadingToneRule):
    1. Sistema conoce factores de acordes
    2. En acordes de 7ª, el factor '7' es la disonancia
    3. Detectar cuántas voces tienen factor '7'
    4. Si > 1 → Error
    
    Aplicable a: V7, ii7, I7, cualquier acorde con 7ª
    """
    
    def __init__(self):
        super().__init__(
            name='duplicated_seventh',
            tier=RuleTier.CRITICAL,
            color='#DC143C',  # Crimson
            short_msg='Séptima duplicada',
            full_msg='La séptima está duplicada en múltiples voces, '
                     'lo cual es incorrecto para disonancias que deben resolverse'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si la 7ª está duplicada en chord1 O chord2.
        
        Misma estrategia que DuplicatedLeadingToneRule:
        - Checkear chord1 primero
        - Solo si OK, checkear chord2
        - Evitar early return que impida analizar chord2
        
        Returns:
            Dict con voces que tienen la 7ª duplicada, o None
        """
        # Primero checkear chord1
        result = self._check_chord_for_duplicated_seventh(chord1)
        if result:
            return result
        
        # Solo si chord1 NO tiene error, checkear chord2
        result = self._check_chord_for_duplicated_seventh(chord2)
        if result:
            # Indicar que el error es en chord2
            result['chord_index'] = 1
            return result
        
        return None
    
    def _check_chord_for_duplicated_seventh(self, chord: Dict) -> Optional[Dict]:
        """
        Verifica si UN acorde tiene 7ª duplicada.
        
        Arquitectura basada en factores:
        1. Obtener root del acorde
        2. Identificar voces con factor '7'
        3. Si > 1 → Error
        """
        if not chord or len(chord) < 2:
            return None
        
        # 1. Obtener la fundamental del acorde
        root = chord.get('root')
        
        if not root:
            # Fallback: usar bajo
            bass_note = chord.get('B')
            if bass_note:
                try:
                    root = music21.pitch.Pitch(bass_note).name
                except:
                    return None
            else:
                return None
        
        # 2. Identificar cuáles notas son el factor '7' (séptima del acorde)
        voices_with_seventh = []
        
        for voice in ['S', 'A', 'T', 'B']:
            note = chord.get(voice)
            if not note:
                continue
            
            try:
                # Usar el conocimiento de factores del sistema
                factor = VoiceLeadingUtils.get_chord_factor(note, root)
                
                if factor == '7':  # Esta nota es la 7ª del acorde
                    voices_with_seventh.append(voice)
            except Exception as e:
                logger.warning(f"Error obteniendo factor de {note} en {root}: {e}")
                continue
        
        # 3. Si hay más de una voz con el factor '7' → Séptima duplicada
        if len(voices_with_seventh) > 1:
            return {
                'chord_index': 0,
                'voices': voices_with_seventh,
                'upper_voice': voices_with_seventh[0]
            }
        
        return None
    
    def _calculate_confidence(self, chord1, chord2, context):
        """
        Duplicar la 7ª es un error inequívoco.
        """
        return 100  # Confianza máxima


# =============================================================================
# REGLA #13: MOVIMIENTO MELÓDICO EXCESIVO (EXCESSIVE MELODIC MOTION)
# =============================================================================

class ExcessiveMelodicMotionRule(HarmonicRule):
    """
    Detecta saltos melódicos excesivos (mayores a una octava) en cualquier voz.
    
    Regla:
        En una misma voz, el movimiento melódico no debe superar una 8ª justa.
        Saltos mayores a la octava dificultan la audición de líneas melódicas
        y son antiidiomáticos en escritura coral SATB.
        
    Umbral: > 12 semitonos (mayor que 8ª justa)
    
    Excepciones:
        - Arpegios del mismo acorde (muy raro en SATB estricto)
        - En el Bajo: tolerancia ligeramente mayor (hasta 10ª en casos especiales)
        
    Detección:
        Para cada voz (S, A, T, B):
            Calcular |pitch2 - pitch1| en semitonos
            Si > 12 → violación
    
    Color: #FF8C00 (Dark Orange) - Tier 2
    """
    
    # Umbral en semitonos: 12 = octava justa (P8)
    OCTAVE_SEMITONES = 12
    
    def __init__(self):
        super().__init__(
            name='excessive_melodic_motion',
            tier=RuleTier.IMPORTANT,
            color='#FF8C00',  # Dark Orange
            short_msg='Salto melódico excesivo',
            full_msg='El movimiento melódico supera una octava. Los saltos mayores '
                     'a la 8ª dificultan la percepción de la línea melódica y son '
                     'excepcionales en escritura coral.'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si alguna voz tiene un salto mayor a una octava.
        
        Proceso:
            1. Para cada voz (S, A, T, B)
            2. Calcular intervalo en semitonos entre chord1[voz] y chord2[voz]
            3. Si |intervalo| > 12 semitonos → violación
        
        Returns:
            Dict con la primera violación encontrada, o None
        """
        voices_with_excessive_leap = []
        
        for voice in ['S', 'A', 'T', 'B']:
            note1 = chord1.get(voice)
            note2 = chord2.get(voice)
            
            # Ambas notas deben existir para analizar el movimiento
            if not note1 or not note2:
                continue
            
            try:
                # Calcular intervalo en semitonos
                p1 = music21.pitch.Pitch(note1)
                p2 = music21.pitch.Pitch(note2)
                
                # Diferencia absoluta en semitonos (pitch space)
                semitones = abs(p2.ps - p1.ps)
                
                # Si supera la octava justa (12 semitonos)
                if semitones > self.OCTAVE_SEMITONES:
                    voices_with_excessive_leap.append(voice)
                    logger.debug(f"Salto excesivo en {voice}: {note1} → {note2} ({semitones} semitonos)")
                    
            except Exception as e:
                logger.warning(f"Error calculando salto melódico en {voice}: {e}")
                continue
        
        # Reportar la primera voz con salto excesivo
        if voices_with_excessive_leap:
            return {
                'chord_index': 1,  # El error se muestra en el acorde destino
                'voices': voices_with_excessive_leap,
                'upper_voice': voices_with_excessive_leap[0]
            }
        
        return None
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        El salto excesivo es un error claro y cuantificable.
        
        Confianza alta pero no máxima: hay excepciones estilísticas.
        """
        return 90  # Alta confianza, pero no 100% por posibles excepciones estilísticas


# =============================================================================
# REGLA #14: OMISIÓN IMPROPIA DE FACTORES (IMPROPER OMISSION)
# =============================================================================

class ImproperOmissionRule(HarmonicRule):
    """
    Detecta omisión impropia de factores críticos en acordes.
    
    Regla:
        Los acordes en escritura SATB deben contener sus factores esenciales:
        - La 3ª: Define la calidad (mayor/menor) - MUY crítica
        - La 7ª: En acordes de séptima, es característica del acorde
        
    La 5ª puede omitirse (es prescindible en triadas)
    La fundamental puede duplicarse pero no omitirse.
    
    Excepciones:
        1. Acorde final de cadencia: puede omitir 3ª para sonoridad "arcaica"
        2. Acordes de cuarta y sexta: estructura predeterminada
        
    Severity diferenciada:
        - Omisión de 3ª: ERROR (crítico)
        - Omisión de 7ª en V7: WARNING (importante pero tolerable)
    
    Color: #FF8C00 (Dark Orange) - Tier 2
    """
    
    def __init__(self):
        super().__init__(
            name='improper_omission',
            tier=RuleTier.IMPORTANT,
            color='#FF8C00',  # Dark Orange
            short_msg='Factor omitido',
            full_msg='El acorde omite un factor esencial. La tercera define la calidad '
                     'mayor/menor del acorde y no debe omitirse excepto en cadencias finales arcaicas.'
        )
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta si algún acorde omite factores esenciales.
        
        Proceso:
            1. Convertir dict a Chord object (chord_knowledge.py)
            2. Usar get_missing_factors() para detectar omisiones
            3. Filtrar: la 5ª puede omitirse, pero la 3ª no
            4. Reportar violación si falta la 3ª
        
        IMPORTANT: Solo valida chord1 para evitar duplicación.
        chord2 será validado en el siguiente par como chord1.
        
        Returns:
            Dict con información de la primera violación, o None
        """
        # Solo verificar chord1 (chord2 se validará en el siguiente par)
        result = self._check_chord_for_omissions(chord1, chord_index=0)
        if result:
            return result
        
        # NO validar chord2 aquí - causa duplicación
        # El sistema valida pares solapados:
        # Par 1: A → B (B con chord_index=1)
        # Par 2: B → C (B con chord_index=0) ← DUPLICADO
        
        return None
    
    def _is_chromatic_chord(self, chord_obj) -> bool:
        """
        Detecta si un acorde es cromático (como 6ª Aumentada).
        
        Los acordes cromáticos tienen estructuras no-triádicas con
        intervalos aumentados característicos. Se exentan de la
        validación de "factores omitidos" porque no siguen la
        morfología estándar 1-3-5(-7).
        
        Criterios de detección:
            - Contiene intervalo de 6ª Aumentada (10 semitonos)
            - Contiene intervalo de 4ª Aumentada/Tritono (6 st) con
              al menos 3 factores (para distinguir de V7)
        
        Returns:
            True si es acorde cromático, False si es diatónico
        
        Examples:
            6ª Aug Alemana: [0, 4, 6, 10] → True (tiene 6ª Aug)
            6ª Aug Italiana: [0, 4, 10] → True (tiene 6ª Aug)
            V7: [0, 4, 7, 10] → False (no tiene tritono aislado)
        """
        try:
            # CRITICAL FIX: Validar que chord_obj y su root existan
            # music21 no siempre puede identificar la raíz de acordes cromáticos
            if not chord_obj:
                return False
            
            # Si chord_obj.root es None, get_intervals_from_root() retornará []
            # pero validamos explícitamente para evitar AttributeError
            if not hasattr(chord_obj, 'root') or chord_obj.root is None:
                logger.debug("Acorde sin raíz identificada, no se puede validar como cromático")
                return False
            
            intervals = chord_obj.get_intervals_from_root()
            
            if not intervals:
                return False  # No se pudo calcular
            
            # Intervalo de 6ª Aumentada = 10 semitonos
            AUGMENTED_SIXTH = 10
            
            # 4ª Aumentada (tritono) = 6 semitonos
            AUGMENTED_FOURTH = 6
            
            # Si contiene 6ª Aumentada, es claramente cromático
            if AUGMENTED_SIXTH in intervals:
                return True
            
            # Si contiene tritono Y tiene al menos 3 factores distintos,
            # probablemente es acorde cromático (no V7 normal)
            if AUGMENTED_FOURTH in intervals and len(intervals) >= 3:
                # Verificar que NO sea simplemente un V7 diatónico
                # V7 typical: [0, 4, 7, 10] (1, 3, 5, m7)
                # 6ª Aug Francesa: [0, 2, 4, 10] (contiene 2ª, no 5ª)
                if 7 not in intervals:  # No tiene 5ª justa
                    return True  # Probablemente cromático
            
            return False
            
        except Exception as e:
            logger.debug(f"Error detectando acorde cromático: {e}")
            return False
    
    def _check_chord_for_omissions(self, chord_dict: Dict, chord_index: int) -> Optional[Dict]:
        """
        Verifica si un acorde específico tiene omisiones impropias.
        
        Args:
            chord_dict: Diccionario del acorde
            chord_index: 0 para chord1, 1 para chord2
        
        Returns:
            Dict con información de violación, o None
        """
        # ========== CLÁUSULA DE GUARDA #1: Acordes cromáticos pre-identificados ==========
        # Si analizador_tonal.py YA marcó el acorde como cromático (tipo_especial),
        # exentarlo INMEDIATAMENTE sin validar factores
        tipo_especial = chord_dict.get('tipo_especial')
        
        if tipo_especial:
            # Tipos cromáticos conocidos: +6it, +6fr, +6al, N (Napolitana)
            acordes_cromaticos_validos = ['+6it', '+6fr', '+6al', 'N', 'dominante_secundaria', 'prestamo_menor']
            
            if tipo_especial in acordes_cromaticos_validos:
                logger.debug(f"Acorde cromático detectado por tipo_especial='{tipo_especial}', exento de validación de omisión")
                return None  # Acorde cromático válido, no aplicar reglas
        
        # ========== CONVERSIÓN A OBJETO CHORD ==========
        chord_obj = _dict_to_chord_safe(chord_dict)
        
        # ========== CLÁUSULA DE GUARDA #2: Detección de cromáticos por intervalos ==========
        # Si el acorde tiene intervalos cromáticos característicos (6ª Aug, etc.),
        # exentarlo aunque tipo_especial no esté presente (fallback robusto)
        if chord_obj and self._is_chromatic_chord(chord_obj):
            logger.debug(f"Acorde cromático detectado por intervalos, exento de validación")
            return None  # Acorde cromático válido, no aplicar reglas de omisión
        
        # ========== VALIDACIÓN NORMAL: Acordes diatónicos ==========
        # Si no se puede crear el objeto Chord O si chord_type es None/unknown,
        # usar método legacy que funciona solo con root + notas SATB
        if chord_obj is None or chord_obj.chord_type is None or chord_obj.chord_type == 'unknown':
            return self._legacy_check_omissions(chord_dict, chord_index)
        
        # Si tenemos chord_type válido, usar chord_knowledge
        missing = chord_obj.get_missing_factors()
        
        if not missing:
            return None  # Acorde completo
        
        # Filtrar: la 5ª puede omitirse (es tolerable)
        critical_missing = [f for f in missing if f in ['3', '7']]
        
        if not critical_missing:
            return None  # Solo falta la 5ª, que es aceptable
        
        # La 3ª es más crítica que la 7ª
        if '3' in critical_missing:
            # Omisión de 3ª: error crítico
            return {
                'chord_index': chord_index,
                'voices': ['?'],  # No sabemos qué voz debería tenerla
                'missing_factor': '3',
                'severity': 'critical'
            }
        elif '7' in critical_missing:
            # Verificar si es un acorde de 7ª
            chord_quality = chord_dict.get('quality', '')
            if 'seventh' in chord_quality or chord_dict.get('degree', '').startswith('V'):
                # Es un acorde de 7ª que omite la 7ª
                return {
                    'chord_index': chord_index,
                    'voices': ['?'],
                    'missing_factor': '7',
                    'severity': 'warning'
                }
        
        return None
    
    def _legacy_check_omissions(self, chord_dict: Dict, chord_index: int) -> Optional[Dict]:
        """
        Método fallback si chord_knowledge no está disponible.
        
        Usa VoiceLeadingUtils.get_chord_factor() directamente.
        """
        root = chord_dict.get('root')
        if not root:
            return None  # Sin root no podemos analizar
        
        # Calcular factores de cada voz
        factors_present = set()
        
        for voice in ['S', 'A', 'T', 'B']:
            note = chord_dict.get(voice)
            if note:
                factor = VoiceLeadingUtils.get_chord_factor(note, root)
                if factor != '?':
                    factors_present.add(factor)
        
        # Verificar si falta la 3ª
        if '3' not in factors_present:
            return {
                'chord_index': chord_index,
                'voices': ['?'],
                'missing_factor': '3',
                'severity': 'critical'
            }
        
        # Verificar si falta la 7ª en acordes de séptima
        degree = chord_dict.get('degree', '')
        quality = chord_dict.get('quality', '')
        
        is_seventh_chord = (
            'V7' in degree or 
            'vii°7' in degree or
            'seventh' in quality.lower()
        )
        
        if is_seventh_chord and '7' not in factors_present:
            return {
                'chord_index': chord_index,
                'voices': ['?'],
                'missing_factor': '7',
                'severity': 'warning'
            }
        
        return None
    
    def _calculate_confidence(self, chord1: Dict, chord2: Dict, context: Dict) -> int:
        """
        La omisión de factores es detectable con alta confianza,
        pero hay excepciones estilísticas.
        """
        return 85  # Alta confianza, pero hay excepciones arcaicas


# NOTA: TritonResolutionRule fue ELIMINADA
# La resolución del tritono en V7 → I ya está cubierta por:
# - LeadingToneResolutionRule: sensible → tónica
# - SeventhResolutionRule: 7ª → grado conjunto descendente


class RulesEngine:
    """
    Motor principal que coordina todas las reglas armónicas.
    
    Gestiona:
        - Registro de reglas
        - Validación de progresiones
        - Filtrado por tier (críticas, importantes, avanzadas)
        - Habilitación/deshabilitación de reglas
    
    Uso:
        engine = RulesEngine(key="C", mode="major")
        engine.register_rule(ParallelFifthsRule())
        errors = engine.validate_progression(chord1, chord2)
    """
    
    def __init__(self, key: str = "C", mode: str = "major"):
        """
        Inicializa el motor de reglas.
        
        Args:
            key: Tonalidad ('C', 'D', 'Eb', etc.)
            mode: Modo ('major' o 'minor')
        """
        self.key = key
        self.mode = mode
        self.rules: List[HarmonicRule] = []
        
        # Registrar reglas Tier 1 por defecto
        self._register_default_rules()
        
        logger.info(f"RulesEngine inicializado en {key} {mode}")
    
    def _register_default_rules(self):
        """Registra las reglas Tier 1 por defecto"""
        # Por ahora solo quintas paralelas
        self.register_rule(ParallelFifthsRule())
        
        # REGLA #2: Octavas Paralelas/Consecutivas (FASE 2: Testing dual)
        self.register_rule(ParallelOctavesRule())
        
        # REGLA #3: Quintas Directas (ocultas)
        self.register_rule(DirectFifthsRule())
        
        # REGLA #4: Octavas Directas (ocultas)
        self.register_rule(DirectOctavesRule())
        
        # REGLA #5: Quintas Desiguales (d5→P5)
        self.register_rule(UnequalFifthsRule())
        
        # REGLA #6: Resolución de Sensible (Leading Tone)
        self.register_rule(LeadingToneResolutionRule())
        
        # REGLA #7: Resolución de Séptima de Dominante
        self.register_rule(SeventhResolutionRule())

        # REGLA #8: Cruzamiento de Voces (migrada desde app.py)
        self.register_rule(VoiceCrossingRule())
        self.register_rule(MaximumDistanceRule())
        self.register_rule(VoiceOverlapRule())
        self.register_rule(DuplicatedLeadingToneRule())
        self.register_rule(DuplicatedSeventhRule())
        
        # REGLA #13: Saltos melódicos excesivos (> 8ª)
        self.register_rule(ExcessiveMelodicMotionRule())
        
        # REGLA #14: Omisión impropia de factores (3ª, 7ª)
        self.register_rule(ImproperOmissionRule())
        
        # NOTA: TritonResolutionRule fue eliminada (redundante)
        # Sus casos ya están cubiertos por:
        # - LeadingToneResolutionRule (sensible → tónica)
        # - SeventhResolutionRule (7ª → grado conjunto descendente)
    
    def register_rule(self, rule: HarmonicRule):
        """
        Registra una nueva regla en el motor.
        
        Args:
            rule: Instancia de una regla armónica
        """
        self.rules.append(rule)
        logger.info(f"Regla '{rule.name}' registrada (Tier {rule.tier.value})")
    
    def validate_progression(
        self,
        chord1: Dict,
        chord2: Dict,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Valida una progresión de dos acordes contra todas las reglas.
        
        Args:
            chord1, chord2: Análisis de acordes
            context: Contexto armónico adicional
            
        Returns:
            Lista de errores encontrados (puede estar vacía)
        """
        if context is None:
            context = {}
        
        # Añadir tonalidad al contexto si no está
        if 'key' not in context:
            context['key'] = f"{self.key} {self.mode}"
        
        errors = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            error = rule.validate(chord1, chord2, context)
            if error:
                errors.append(error)
        
        return errors
    
    def enable_rule(self, rule_name: str):
        """Habilita una regla específica"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"Regla '{rule_name}' habilitada")
                return
        logger.warning(f"Regla '{rule_name}' no encontrada")
    
    def disable_rule(self, rule_name: str):
        """Deshabilita una regla específica"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"Regla '{rule_name}' deshabilitada")
                return
        logger.warning(f"Regla '{rule_name}' no encontrada")
    
    def get_active_rules(self, tier: Optional[RuleTier] = None) -> List[HarmonicRule]:
        """
        Obtiene las reglas activas, opcionalmente filtradas por tier.
        
        Args:
            tier: Si se especifica, solo retorna reglas de ese tier
            
        Returns:
            Lista de reglas habilitadas
        """
        active = [r for r in self.rules if r.enabled]
        
        if tier:
            active = [r for r in active if r.tier == tier]
        
        return active
    
    def format_errors_for_app(
        self,
        errors: List[Dict],
        compas: int,
        tiempo_index: int
    ) -> List[Dict]:
        """
        Convierte errores del motor al formato esperado por app.py.
        
        Formato app.py esperado:
        {
            'id': 'err-{tiempo_index}',
            'mensaje': 'Compás X, TY: Mensaje',
            'mensaje_corto': 'Mensaje',
            'tiempo_index': int,
            'voces': ['S', 'A']
        }
        
        Args:
            errors: Lista de errores del motor
            compas: Número de compás
            tiempo_index: Índice global del tiempo (del PRIMER acorde del par)
            
        Returns:
            Lista de errores formateados para app.py
        """
        formatted = []
        
        nombres_voces = {
            'S': 'Soprano',
            'A': 'Contralto',
            'T': 'Tenor',
            'B': 'Bajo'
        }
        
        # Orden de voces de grave a agudo (convención pedagógica)
        voice_order = {'B': 0, 'T': 1, 'A': 2, 'S': 3}
        
        for error in errors:
            # CRITICAL FIX: Ajustar tiempo_index según chord_index
            # chord_index=0 → error en chord1 (tiempo_index)
            # chord_index=1 → error en chord2 (tiempo_index + 1)
            chord_idx = error.get('chord_index', 0)
            actual_tiempo_index = tiempo_index + chord_idx
            
            # Calcular tiempo dentro del compás
            t_compas = (actual_tiempo_index % 4) + 1
            actual_compas = (actual_tiempo_index // 4) + 1
            
            # Ordenar voces de grave a agudo (Bajo → Tenor → Alto → Soprano)
            voices = error.get('voices', [])
            sorted_voices = sorted(voices, key=lambda v: voice_order.get(v, 999))
            
            # Construir descripción de voces en orden correcto
            voces_str = '-'.join([nombres_voces.get(v, v) for v in sorted_voices])
            
            # Construir mensaje corto con voces ordenadas
            mensaje_corto = error['short_msg']
            if voces_str:
                mensaje_corto = f"{error['short_msg']} ({voces_str})"
            
            formatted.append({
                'id': f"err-{actual_tiempo_index}",
                'mensaje': f"Compás {actual_compas}, T{t_compas}: {mensaje_corto}",
                'mensaje_corto': mensaje_corto,
                'tiempo_index': actual_tiempo_index,
                'voces': sorted_voices,  # También ordenar en la lista de voces
                'confidence': error.get('confidence', 100),
                'color': error.get('color', '#FF0000'),
                'rule': error.get('rule', 'unknown')
            })
        
        return formatted


# =============================================================================
# EJEMPLO DE USO (TESTING)
# =============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Ejemplo de uso del motor
    engine = RulesEngine(key="C", mode="major")
    
    # Simular dos acordes
    chord1 = {
        'S': 'G4', 'A': 'C4', 'T': 'E3', 'B': 'C3',
        'root': 'C', 'quality': 'major', 'inversion': 0,
        'degree_num': 1, 'function': 'T'
    }
    
    chord2 = {
        'S': 'A4', 'A': 'D4', 'T': 'F3', 'B': 'D3',
        'root': 'D', 'quality': 'minor', 'inversion': 0,
        'degree_num': 2, 'function': 'S'
    }
    
    # Validar progresión
    errors = engine.validate_progression(chord1, chord2)
    
    if errors:
        print(f"\n🚨 Se encontraron {len(errors)} errores:")
        for error in errors:
            print(f"  - {error['short_msg']} ({error['confidence']}% confianza)")
            print(f"    Voces: {error['voices']}")
            print(f"    Mensaje: {error['full_msg']}")
    else:
        print("\n✅ No se encontraron errores")
# =============================================================================
# REGLA #8: CRUZAMIENTO DE VOCES (VOICE CROSSING)
# =============================================================================

