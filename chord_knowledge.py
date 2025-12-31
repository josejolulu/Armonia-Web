"""
================================================================================
CHORD KNOWLEDGE - Definiciones y Abstracción de Acordes
================================================================================

Proporciona conocimiento centralizado sobre acordes del sistema tonal.

Componentes:
    - ChordDefinitions: Tabla estática con morfología de todos los tipos de acordes
    - Chord: Clase que representa un acorde SATB con análisis automático de factores
    - Progression: Clase que analiza movimientos entre acordes

Basado en:
    - "Tabla de acordes e inversiones.pdf"
    - Sistema de cifrado barroco (bajo cifrado)
    - Armonía tonal funcional bimodal

Autor: Aula de Armonía
Versión: 1.1 (Expandido con tipos cromáticos)
Fecha: 2025-12-28
================================================================================
"""

# =============================================================================
# NOTAS SOBRE DETECCIÓN DE ACORDES CROMÁTICOS
# =============================================================================
#
# Los siguientes tipos de acordes están DEFINIDOS en ChordDefinitions pero
# su DETECCIÓN es responsabilidad de analizador_tonal.py:
#
# - secondary_dominant, secondary_leading_tone_*:
#     → DetectorFunciones.detectar_dominante_secundaria()
# - neapolitan_sixth:
#     → DetectorAcordesEspeciales.detectar_napolitana()
# - *_augmented_sixth:
#     → DetectorAcordesEspeciales.detectar_sexta_aumentada()
#
# Esta separación es intencional:
# - ChordDefinitions: Conocimiento teórico (morfología, sintaxis, referencias)
# - analizador_tonal.py: Detección práctica (requiere music21.chord.Chord)
#
# Si en el futuro se necesita detectar estos tipos desde harmonic_rules.py,
# se deberá crear un adapter que convierta Dict SATB → music21.chord.Chord
# y llame a los detectores apropiados de analizador_tonal.py.
#
# =============================================================================

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import music21
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CHORD DEFINITIONS - Conocimiento Estático
# =============================================================================

CHORD_DEFINITIONS = {
    # =========================================================================
    # TRIADAS DIATÓNICAS (3 sonidos)
    # =========================================================================
    
    'major': {
        'name': 'Acorde Mayor',
        'name_es': 'Mayor',
        'morphology': ['M3', 'P5'],  # Intervalos desde fundamental
        'num_factors': 3,  # 1, 3, 5
        'figured_bass': {
            0: '5/3',  # Estado fundamental (o sin cifrar)
            1: '6',     # 1ª inversión (bajo = 3ª)
            2: '6/4'    # 2ª inversión (bajo = 5ª)
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5']},
            1: {'bass': '3', 'upper': ['1', '5']},
            2: {'bass': '5', 'upper': ['1', '3']}
        },
        'syntax': 'universal',
        'category': 'diatonic_triad'
    },
    
    'minor': {
        'name': 'Acorde Menor',
        'name_es': 'menor',
        'morphology': ['m3', 'P5'],
        'num_factors': 3,
        'figured_bass': {
            0: '5/3',
            1: '6',
            2: '6/4'
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5']},
            1: {'bass': '3', 'upper': ['1', '5']},
            2: {'bass': '5', 'upper': ['1', '3']}
        },
        'syntax': 'universal',
        'category': 'diatonic_triad'
    },
    
    'diminished': {
        'name': 'Acorde Disminuido',
        'name_es': 'disminuido',
        'morphology': ['m3', 'd5'],
        'num_factors': 3,
        'figured_bass': {
            0: '5♭',
            1: '6',
            2: '+6/3'
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5']},
            1: {'bass': '3', 'upper': ['1', '5']},
            2: {'bass': '5', 'upper': ['1', '3']}
        },
        'syntax': 'VII-I',
        'category': 'diatonic_triad'
    },
    
    # =========================================================================
    # CUATRIADAS - ACORDES DE 7ª (4 sonidos)
    # =========================================================================
    
    'dominant_seventh': {
        'name': 'Acorde de 7ª de Dominante',
        'name_es': '7ª de Dominante',
        'morphology': ['M3', 'P5', 'm7'],
        'num_factors': 4,  # 1, 3, 5, 7
        'figured_bass': {
            0: '7/+',
            1: '6/5-',
            2: '+6',
            3: '+4'
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5', '7']},
            1: {'bass': '3', 'upper': ['1', '5', '7']},
            2: {'bass': '5', 'upper': ['1', '3', '7']},
            3: {'bass': '7', 'upper': ['1', '3', '5']}
        },
        'syntax': 'V-I',
        'special': {
            'leading_tone_factor': '3',
            'resolution_factor': '7',
            'has_tritone': True
        },
        'category': 'diatonic_seventh'
    },
    
    'diminished_seventh': {
        'name': 'Acorde de 7ª Disminuida',
        'name_es': '7ª disminuida',
        'morphology': ['m3', 'd5', 'd7'],
        'num_factors': 4,
        'figured_bass': {
            0: '7-',
            1: '6-/5-',
            2: '+6',
            3: '+4'
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5', '7']},
            1: {'bass': '3', 'upper': ['1', '5', '7']},
            2: {'bass': '5', 'upper': ['1', '3', '7']},
            3: {'bass': '7', 'upper': ['1', '3', '5']}
        },
        'syntax': 'VII-I',
        'special': {
            'leading_tone_factor': '1',
            'resolution_factor': '7',
            'symmetric': True
        },
        'category': 'diatonic_seventh'
    },
    
    'half_diminished': {
        'name': 'Acorde de 7ª de Sensible (Half-Diminished)',
        'name_es': '7ª de sensible',
        'morphology': ['m3', 'd5', 'm7'],
        'num_factors': 4,
        'figured_bass': {
            0: '7',
            1: '6/5♭',
            2: '+6',
            3: '+4'
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5', '7']},
            1: {'bass': '3', 'upper': ['1', '5', '7']},
            2: {'bass': '5', 'upper': ['1', '3', '7']},
            3: {'bass': '7', 'upper': ['1', '3', '5']}
        },
        'syntax': 'VII-I',
        'special': {
            'leading_tone_factor': '1',
            'resolution_factor': '7'
        },
        'category': 'diatonic_seventh'
    },
    
    'major_seventh': {
        'name': 'Acorde de 7ª Mayor',
        'name_es': '7ª Mayor',
        'morphology': ['M3', 'P5', 'M7'],
        'num_factors': 4,
        'figured_bass': {
            0: '7',
            1: '6/5',
            2: '4/3',
            3: '2'
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5', '7']},
            1: {'bass': '3', 'upper': ['1', '5', '7']},
            2: {'bass': '5', 'upper': ['1', '3', '7']},
            3: {'bass': '7', 'upper': ['1', '3', '5']}
        },
        'syntax': 'varies',
        'category': 'diatonic_seventh'
    },
    
    'minor_seventh': {
        'name': 'Acorde de 7ª menor',
        'name_es': '7ª menor',
        'morphology': ['m3', 'P5', 'm7'],
        'num_factors': 4,
        'figured_bass': {
            0: '7',
            1: '6/5',
            2: '4/3',
            3: '2'
        },
        'factors_in_inversion': {
            0: {'bass': '1', 'upper': ['3', '5', '7']},
            1: {'bass': '3', 'upper': ['1', '5', '7']},
            2: {'bass': '5', 'upper': ['1', '3', '7']},
            3: {'bass': '7', 'upper': ['1', '3', '5']}
        },
        'syntax': 'varies',
        'category': 'diatonic_seventh'
    },
    
    # =========================================================================
    # ACORDES CROMÁTICOS - SECUNDARIOS
    # =========================================================================
    # NOTA: detection.method = 'external' indica que se detectan en analizador_tonal.py
    
    'secondary_dominant': {
        'name': 'Dominante Secundaria',
        'name_es': 'V/x',
        'pattern': 'V/{target}',
        'morphology_base': ['M3', 'P5'],
        'morphology_with_7th': ['M3', 'P5', 'm7'],
        'num_factors': 'varies',
        'detection': {
            'method': 'external',
            'detector': 'DetectorFunciones.detectar_dominante_secundaria',
            'requires_chromaticism': True
        },
        'figured_bass': {
            0: {'triad': '', 'seventh': '7/+'},
            1: {'triad': '6', 'seventh': '6/5-'},
            2: {'triad': '6/4', 'seventh': '+6'},
            3: {'seventh': '+4'}
        },
        'syntax': 'V/x → x',
        'special': {
            'leading_tone_factor': '3',
            'resolution_factor': '7',
            'creates_tonicization': True
        },
        'category': 'chromatic_secondary'
    },
    
    'secondary_leading_tone_dim': {
        'name': 'Sensible Secundaria Disminuida',
        'name_es': 'vii°/x o vii°7/x',
        'pattern': 'vii°/{target}',
        'morphology_base': ['m3', 'd5'],
        'morphology_with_7th': ['m3', 'd5', 'd7'],
        'num_factors': 'varies',
        'detection': {
            'method': 'external',
            'detector': 'DetectorFunciones.detectar_dominante_secundaria'
        },
        'syntax': 'vii°/x → x',
        'special': {
            'leading_tone_factor': '1',
            'symmetric_intervals': True
        },
        'category': 'chromatic_secondary'
    },
    
    'secondary_leading_tone_half_dim': {
        'name': 'Sensible Secundaria Half-Diminished',
        'name_es': 'viiø7/x',
        'morphology': ['m3', 'd5', 'm7'],
        'num_factors': 4,
        'detection': {
            'method': 'external',
            'detector': 'DetectorFunciones.detectar_dominante_secundaria'
        },
        'syntax': 'viiø7/x → x',
        'category': 'chromatic_secondary'
    },
    
    # =========================================================================
    # ACORDES CROMÁTICOS - ALTERADOS
    # =========================================================================
    
    'neapolitan_sixth': {
        'name': 'Sexta Napolitana',
        'name_es': 'N6',
        'pattern': '♭II6',
        'morphology': ['M3', 'P5'],
        'num_factors': 3,
        'detection': {
            'method': 'external',
            'detector': 'DetectorAcordesEspeciales.detectar_napolitana',
            'root_degree': '♭II',
            'quality': 'major',
            'typical_inversion': 1
        },
        'figured_bass': {
            0: 'N',
            1: 'N6',
            2: 'N6/4'
        },
        'syntax': 'N6 → V',
        'special': {
            'characteristic_interval': 'm2 above tonic',
            'common_use': 'Subdominante alterada'
        },
        'category': 'chromatic_altered_chord'
    },
    
    # =========================================================================
    # ACORDES CROMÁTICOS - SEXTAS AUMENTADAS
    # =========================================================================
    
    'italian_augmented_sixth': {
        'name': 'Sexta Italiana',
        'name_es': '+6it',
        'pattern': '+6it',
        'morphology_degrees': ['♭6', '1', '#4'],
        'num_pitches': 3,
        'detection': {
            'method': 'external',
            'detector': 'DetectorAcordesEspeciales.detectar_sexta_aumentada',
            'contains_interval': 'A6'
        },
        'figured_bass': {
            0: '+6it'
        },
        'syntax': '+6it → V',
        'special': {
            'characteristic_interval': 'A6 (♭6 to #4)',
            'no_third': True
        },
        'category': 'chromatic_augmented_sixth'
    },
    
    'french_augmented_sixth': {
        'name': 'Sexta Francesa',
        'name_es': '+6fr',
        'pattern': '+6fr',
        'morphology_degrees': ['♭6', '1', '2', '#4'],
        'num_pitches': 4,
        'detection': {
            'method': 'external',
            'detector': 'DetectorAcordesEspeciales.detectar_sexta_aumentada'
        },
        'figured_bass': {
            0: '+6fr'
        },
        'syntax': '+6fr → V',
        'special': {
            'contains_tritone': True
        },
        'category': 'chromatic_augmented_sixth'
    },
    
    'german_augmented_sixth': {
        'name': 'Sexta Alemana',
        'name_es': '+6al',
        'pattern': '+6al',
        'morphology_degrees': ['♭6', '1', '♭3', '#4'],
        'num_pitches': 4,
        'detection': {
            'method': 'external',
            'detector': 'DetectorAcordesEspeciales.detectar_sexta_aumentada'
        },
        'figured_bass': {
            0: '+6al'
        },
        'syntax': '+6al → V',
        'special': {
            'sounds_like_dominant7': True,
            'parallel_fifths_danger': True
        },
        'category': 'chromatic_augmented_sixth'
    }
}


# Mapa inverso: music21 quality → chord_type
QUALITY_TO_CHORD_TYPE = {
    'major': 'major',
    'minor': 'minor',
    'diminished': 'diminished',
    'dominant-seventh': 'dominant_seventh',
    'diminished-seventh': 'diminished_seventh',
    'half-diminished-seventh': 'half_diminished',
    'major-seventh': 'major_seventh',
    'minor-seventh': 'minor_seventh'
}


# =============================================================================
# CHORD CLASS - Representación de un acorde SATB
# =============================================================================

@dataclass
class Chord:
    """
    Representa un acorde SATB con conocimiento completo de su estructura vertical.
    
    Conocimientos automáticos:
    - Qué factor tiene cada voz (1, 3, 5, 7)
    - Qué voces tienen qué factores (inverso)
    - Completitud del acorde (1-3-5 presentes)
    - Factores duplicados/omitidos
    - Tipo de acorde (Mayor, menor, V7, etc.)
    
    Attributes:
        voices: Dict con voces SATB {'S': 'G4', 'A': 'E4', 'T': 'C4', 'B': 'C3'}
        root: Fundamental del acorde (ej: 'C', 'D', 'E♭')
        quality: Calidad (ej: 'major', 'minor', 'dominant-seventh')
        key: Tonalidad actual ('C major', 'A minor', etc.)
        inversion: Inversión (0=fundamental, 1=primera, 2=segunda, 3=tercera)
    """
    
    voices: Dict[str, str]
    root: Optional[str] = None
    quality: Optional[str] = None
    key: Optional[str] = None
    inversion: int = 0
    
    # Análisis automático (calculado en __post_init__)
    voice_factors: Dict[str, str] = None
    chord_type: Optional[str] = None
    has_seventh: bool = False
    
    def __post_init__(self):
        """Analiza el acorde automáticamente al crearlo."""
        self.voice_factors = {}
        
        if not self.root and self.quality:
            logger.warning("Chord created without root - factor analysis will be incomplete")
            return
        
        # Determinar tipo de acorde
        if self.quality:
            self.chord_type = QUALITY_TO_CHORD_TYPE.get(self.quality)
            if not self.chord_type:
                logger.warning(f"Unknown quality: {self.quality}")
                self.chord_type = 'unknown'
        
        # Analizar factores de cada voz
        if self.root:
            self._analyze_factors()
        
        # Verificar si tiene séptima
        self.has_seventh = '7' in self.voice_factors.values()
    
    def _analyze_factors(self):
        """Calcula automáticamente qué factor tiene cada voz."""
        from harmonic_rules import VoiceLeadingUtils
        
        for voice in ['S', 'A', 'T', 'B']:
            note = self.voices.get(voice)
            if note and self.root:
                factor = VoiceLeadingUtils.get_chord_factor(note, self.root)
                self.voice_factors[voice] = factor
    
    # =========================================================================
    # CONSULTAS VERTICALES
    # =========================================================================
    
    def get_factor_for_voice(self, voice: str) -> Optional[str]:
        """Retorna qué factor tiene una voz específica."""
        return self.voice_factors.get(voice, '?')
    
    def get_voices_with_factor(self, factor: str) -> List[str]:
        """Retorna qué voces tienen un factor específico."""
        return [voice for voice, f in self.voice_factors.items() if f == factor]
    
    def has_factor(self, factor: str) -> bool:
        """Verifica si el acorde contiene un factor específico."""
        return factor in self.voice_factors.values()
    
    def is_complete(self) -> bool:
        """Verifica si el acorde está completo (tiene 1, 3, y 5)."""
        factors_present = set(self.voice_factors.values())
        required = {'1', '3', '5'}
        return required.issubset(factors_present)
    
    def get_doubled_factors(self) -> List[str]:
        """Retorna qué factores están duplicados."""
        factor_counts = {}
        for factor in self.voice_factors.values():
            if factor != '?':
                factor_counts[factor] = factor_counts.get(factor, 0) + 1
        return [f for f, count in factor_counts.items() if count > 1]
    
    def get_missing_factors(self) -> List[str]:
        """Retorna qué factores faltan (para triadas/cuatriadas)."""
        factors_present = set(self.voice_factors.values())
        
        if self.chord_type and self.chord_type in CHORD_DEFINITIONS:
            definition = CHORD_DEFINITIONS[self.chord_type]
            num_factors = definition['num_factors']
            
            if num_factors == 3:
                required = {'1', '3', '5'}
            elif num_factors == 4:
                required = {'1', '3', '5', '7'}
            else:
                return []
            
            missing = required - factors_present
            return list(missing)
        
        return []
    
    def get_intervals_from_root(self) -> List[int]:
        """
        Retorna intervalos en semitonos desde la fundamental.
        
        Usado para detectar acordes cromáticos como 6ª Aumentada
        que tienen intervalos característicos (ej: 10 semitonos = 6ª Aug).
        
        Returns:
            Lista de intervalos únicos en semitonos [0, 4, 7, 10]
            Ejemplo: 6ª Aug Alemana: [0, 4, 6, 10]
                     (root, 3ª Mayor, 4ª Aug, 6ª Aug)
        
        Example:
            >>> chord = Chord(root='Ab', notes=['Ab3', 'C4', 'Eb4', 'Gb4'])
            >>> chord.get_intervals_from_root()
            [0, 4, 7, 10]  # Ab-C-Eb-Gb
        """
        if not self.root or not self.notes:
            return []
        
        try:
            from music21 import interval
            
            # Encontrar la nota fundamental en la lista de notas
            root_pitch = next((n for n in self.notes if n.name == self.root.name), None)
            if not root_pitch:
                return []
            
            intervals_st = []
            for note in self.notes:
                if note == root_pitch:
                    intervals_st.append(0)  # La raíz misma
                else:
                    intv = interval.Interval(root_pitch, note)
                    # Normalizar a una octava (0-11 semitonos)
                    semitones = intv.semitones % 12
                    intervals_st.append(semitones)
            
            # Eliminar duplicados y ordenar
            return sorted(set(intervals_st))
            
        except Exception as e:
            logger.debug(f"Error calculando intervalos: {e}")
            return []

    
    def get_definition(self) -> Optional[Dict]:
        """Retorna la definición completa del tipo de acorde."""
        if self.chord_type and self.chord_type in CHORD_DEFINITIONS:
            return CHORD_DEFINITIONS[self.chord_type]
        return None
    
    def get_figured_bass(self) -> str:
        """Retorna el cifrado barroco según inversión."""
        definition = self.get_definition()
        if definition and 'figured_bass' in definition:
            return definition['figured_bass'].get(self.inversion, '?')
        return '?'
    
    def __repr__(self) -> str:
        """Representación legible del acorde."""
        type_name = self.chord_type or 'unknown'
        inv_str = f"inv{self.inversion}" if self.inversion > 0 else "root"
        factors_str = ', '.join([f"{v}:{f}" for v, f in self.voice_factors.items()])
        return f"Chord({self.root} {type_name} {inv_str}: {factors_str})"


# =============================================================================
# PROGRESSION CLASS - Análisis Horizontal
# =============================================================================

@dataclass
class Progression:
    """
    Representa una progresión (chord1 → chord2) con conocimiento horizontal.
    
    Conocimientos:
    - Qué factor va a qué factor en cada voz
    - Qué voces hacen determinado movimiento de factor
    
    Attributes:
        chord1: Primer acorde (Chord)
        chord2: Segundo acorde (Chord)
    """
    
    chord1: Chord
    chord2: Chord
    
    def get_factor_movement(self, voice: str) -> Tuple[str, str]:
        """Retorna (factor_inicial, factor_final) para una voz."""
        factor1 = self.chord1.get_factor_for_voice(voice)
        factor2 = self.chord2.get_factor_for_voice(voice)
        return (factor1, factor2)
    
    def get_voices_with_movement(self, from_factor: str, to_factor: str) -> List[str]:
        """Retorna voces que hacen un movimiento específico de factor."""
        voices = []
        for voice in ['S', 'A', 'T', 'B']:
            movement = self.get_factor_movement(voice)
            if movement == (from_factor, to_factor):
                voices.append(voice)
        return voices
    
    def get_all_factor_movements(self) -> Dict[str, Tuple[str, str]]:
        """Retorna diccionario completo de movimientos."""
        movements = {}
        for voice in ['S', 'A', 'T', 'B']:
            movements[voice] = self.get_factor_movement(voice)
        return movements
    
    def __repr__(self) -> str:
        """Representación legible de la progresión."""
        movements = self.get_all_factor_movements()
        movements_str = ', '.join([f"{v}:{f1}→{f2}" for v, (f1, f2) in movements.items()])
        return f"Progression({movements_str})"
