# PARALLEL OCTAVES RULE - Para añadir a harmonic_rules.py después de ParallelFifthsRule

# =============================================================================
# REGLA #2: OCTAVAS PARALELAS/CONSECUTIVAS
# =============================================================================

class ParallelOctavesRule(HarmonicRule):
    """
    Detecta octavas paralelas y consecutivas entre pares de voces.
    
    Regla: Dos octavas justas consecutivas están prohibidas tanto en
    movimiento paralelo (directo) como contrario.
    
    Excepciones:
    - Por ahora ninguna implementada (más estricto que quintas)
    - TODO: Consultar con experto si existen excepciones pedagógicas
    """
    
    def __init__(self):
        super().__init__(
            name='parallel_octaves',
            tier=RuleTier.CRITICAL,
            color='#FF0000',
            short_msg='Octavas paralelas',
            full_msg='Dos octavas justas consecutivas. Prohibidas tanto en movimiento paralelo como contrario: debilitan la independencia de las voces y reducen la riqueza armónica.'
        )
        # Por ahora sin excepciones, implementar si es necesario
        # self._add_common_exceptions()
    
    def _add_common_exceptions(self):
        """
        Añade excepciones comunes de las octavas paralelas.
        
        TODO: Verificar con experto si las octavas tienen excepciones.
        Posibles candidatos:
        - V-VII (¿aplica para octavas?)
        - Cambio de disposición
        - Bajo-Soprano en cadencias específicas
        """
        # Por ahora vacío
        pass
    
    def _detect_violation(self, chord1: Dict, chord2: Dict) -> Optional[Dict]:
        """
        Detecta octavas paralelas o consecutivas entre todos los pares de voces.
        
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
        # En el futuro podríamos ajustar según contexto
        return 100
