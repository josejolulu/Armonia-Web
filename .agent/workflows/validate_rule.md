---
description: Validar nueva regla implementada
---

# Validate Rule Workflow

Este workflow valida que una regla armónica recién implementada funciona correctamente.

// turbo-all

## 1. Verificar Importación

```bash
cd /Users/joseluissanchez/Documents/Proyectos/Armonia-Web\ antigravity
python3 -c "from harmonic_rules import [NOMBRE_REGLA]; print('✅ Regla importa correctamente')"
```

## 2. Crear Instancia y Test Básico

```bash
python3 << 'PYEOF'
from harmonic_rules import [NOMBRE_REGLA], RulesEngine

# Crear instancia
rule = [NOMBRE_REGLA]()
print(f"✅ Regla: {rule.name}")
print(f"✅ Tier: {rule.tier}")
print(f"✅ Color: {rule.color}")

# Verificar que está registrada
engine = RulesEngine('C', 'major')
rule_names = [r.name for r in engine.rules]
if rule.name in rule_names:
    print(f"✅ Regla registrada en RulesEngine")
else:
    print(f"❌ ERROR: Regla NO registrada")
PYEOF
```

## 3. Ejecutar Tests JSON (si existen)

```bash
# Ajustar nombre del archivo de tests
python3 << 'PYEOF'
import json
import sys
from harmonic_rules import RulesEngine

try:
    with open('tests/test_[NOMBRE_REGLA].json') as f:
        tests = json.load(f)
    
    engine = RulesEngine('C', 'major')
    passed = 0
    
    for test in tests:
        errors = engine.validate_progression(test['chord1'], test['chord2'])
        rule_errors = [e for e in errors if e['rule'] == '[NOMBRE_REGLA]']
        has_error = len(rule_errors) > 0
        
        if has_error == test['should_have_error']:
            passed += 1
        else:
            print(f"❌ FAIL: {test['name']}")
    
    print(f"✅ Tests: {passed}/{len(tests)} pasando")
    sys.exit(0 if passed == len(tests) else 1)
    
except FileNotFoundError:
    print("⚠️ No hay archivo de tests JSON")
PYEOF
```

## 4. Validar Confidence

```bash
python3 -c "from harmonic_rules import [NOMBRE_REGLA]; r = [NOMBRE_REGLA](); conf = r._calculate_confidence({}, {}, {}); print(f'✅ Confidence: {conf}'); assert conf == 100, 'Debe ser 100'"
```

## 5. Verificar en RulesEngine

```bash
python3 << 'PYEOF'
from harmonic_rules import RulesEngine

engine = RulesEngine('C', 'major')
print(f"✅ Total reglas: {len(engine.rules)}")

# Mostrar reglas de la misma familia/tier
target_tier = 1  # Ajustar según regla
tier_rules = [r.name for r in engine.rules if r.tier.value == target_tier]
print(f"✅ Reglas Tier {target_tier}: {len(tier_rules)}")
for r in tier_rules:
    print(f"   - {r}")
PYEOF
```

## Instrucciones de Uso

**Antes de ejecutar:**

1. Reemplazar `[NOMBRE_REGLA]` con el nombre de la clase (ej: `DuplicatedSeventhRule`)
2. Reemplazar `[nombre_regla]` con el identificador (ej: `duplicated_seventh`)
3. Ajustar nombre del archivo de tests si existe

**Ejecutar con:** `/validate_rule` o menciona este workflow

Los comandos se ejecutarán automáticamente gracias a `// turbo-all`.

## Checklist de Validación

Después de ejecutar el workflow, verifica:

- [ ] ✅ Regla importa sin errores
- [ ] ✅ Instancia se crea correctamente
- [ ] ✅ Registrada en RulesEngine
- [ ] ✅ Tests JSON pasando (si existen)
- [ ] ✅ Confidence = 100
- [ ] ✅ Tier correcto
- [ ] ✅ Color definido

**Si todos pasan:** Regla lista para validación en navegador 🌐
