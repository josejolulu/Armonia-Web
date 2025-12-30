---
description: Ejecutar suite completa de tests del proyecto
---

# Test Suite - Armonía Web

Este workflow ejecuta todos los tests del proyecto.

// turbo-all

## Tests Unitarios

```bash
cd /Users/joseluissanchez/Documents/Proyectos/Armonia-Web\ antigravity
python3 -m pytest tests/ -v
```

## Verificación de Imports

```bash
python3 -c "from harmonic_rules import RulesEngine; from chord_knowledge import Chord; print('✅ Imports OK')"
```

## Conteo de Reglas

```bash
python3 -c "from harmonic_rules import RulesEngine; e = RulesEngine('C', 'major'); print(f'Reglas activas: {len(e.rules)}')"
```

## Uso

Ejecuta con: `/run_tests` o menciona este workflow.

Los comandos se ejecutarán automáticamente gracias a `// turbo-all`.
