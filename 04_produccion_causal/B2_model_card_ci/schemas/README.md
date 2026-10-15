# Contratos de model card

`causal-model-card-v1.schema.json` es el contrato didáctico de ejemplo para la
ficha ATE del apéndice G. El contrato que usa el runtime de Serie B es
`../../esquemas/causal-model-card.local.schema.json`, versión `local-0.2`.
La adenda del proyecto explica la autoridad y las equivalencias entre ambos.

- `causal-model-card-v1.schema.json` — el esquema (JSON Schema, Draft 2020-12).
- `ejemplo_valido.json` — instancia de ejemplo basada en los valores reales de
  `model_card/MODEL_CARD.md` (ATE, IC, n, spec del estimador de B1/A2).

La ficha local `local-0.2` exige que cada supuesto no observable declare una
sensibilidad compatible (`cuantificada`) o `sin_cuantificacion_valida` con su
limitación. Los tests de CI validan el contrato local; el esquema v1 no debe
usarse para afirmar que el endpoint real tiene exactamente su misma forma.

## Validar a mano

```bash
python3 -c "
import json, jsonschema
from jsonschema import Draft202012Validator
schema = json.load(open('causal-model-card-v1.schema.json'))
instance = json.load(open('ejemplo_valido.json'))
Draft202012Validator(schema).validate(instance)
print('OK')
"
```

## Qué NO incluye esta pasada (a propósito)

- El esquema v1 sigue siendo un ejemplo de lectura y no se presenta como contrato
  HTTP completo. El endpoint `/metadata` se valida por sus campos operativos;
  la ficha local y la model card son la autoridad documental.
- No se modificó `model_card/MODEL_CARD.md` (Markdown, para personas) — el schema
  es el contrato para la versión machine-readable, no un reemplazo de la card.
