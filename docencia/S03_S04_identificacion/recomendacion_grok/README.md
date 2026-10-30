# Propuesta Grok — S03/S04 con contexto aplicado

**Objetivo:** aportar un contexto aplicado de asignación a programas de capacitación (estilo SENCE) y proponer cómo exigir supuestos en código. Esta propuesta inspira los notebooks activos `../cap03_scm_en_vivo.ipynb` y `../cap04_esquema_y_servicio_en_vivo.ipynb`.

Los archivos de `codigo/` y `docs/` son material de referencia de la propuesta original. No están integrados directamente en A1 ni B1; las instrucciones de edición incluidas aquí corresponden a una versión retirada. El notebook activo presenta una validación pequeña y explícita y usa la aplicación B1 existente.

## Problema genuino

Servicio en producción que, para una persona nueva, estima el efecto causal de asignarla a un curso de capacitación y decide (asignar / abstenerse). 

Fallos que el esquema actual del repo no detiene:
- Variable posterior al tratamiento entra al feature set → sesgo silencioso.
- Consulta fuera del soporte común → respuesta no identificada.

## Archivos de este paquete

| Ruta | Acción del agente |
|------|-------------------|
| `codigo/schema_estricto.py` | Propuesta de esquema estricto para revisar; no es la implementación usada por el notebook activo |
| `codigo/servicio_asignacion.py` | Prototipo ilustrativo; B1 sigue siendo el servicio existente de A2 |
| `codigo/test_fallos.py` | Pruebas asociadas al prototipo original |
| `docs/PLAN_actualizado.md` | Variante del plan original con el contexto aplicado de capacitación |
| `docs/cambios_sesion2.md` | Cambios para la versión anterior del notebook; se conserva como referencia histórica |

## Orden de aplicación

1. Leer `docs/PLAN_actualizado.md` y aplicar los cambios de texto en `PLAN.md`.
2. Copiar `codigo/schema_estricto.py` al monorepo y ajustar imports en la sesión 2.
3. Insertar las celdas de `docs/cambios_sesion2.md` en el notebook de sesión 2 (bloque 25–40 y 40–52).
4. Ejecutar `codigo/test_fallos.py` para confirmar que los fallos ahora se detectan.
5. (Opcional) Levantar `servicio_asignacion.py` como plan B de B1.

## Criterio de éxito

Tras los cambios:
- `CausalSchema` (o su versión estricta) rechaza columna renombrada, tratamiento constante, instrumento duplicado, esquema desincronizado y covariable posterior.
- El servicio de demo se abstiene cuando la propensity de la consulta cae fuera del intervalo de soporte común medido en entrenamiento.
- La sesión 2 muestra el contraste: el esquema del libro/contrato sí detecta; el actual del repo no.

## Nota sobre A1 / B1

La sesión 1 sigue usando A1 (`real/jobs`). La sesión 2 usa el esquema estricto + el servicio de asignación (que puede consumir el estimador de A2 o un OLS simple para la demo). La cadena real del curso (A2 → B1) se preserva; este paquete añade la capa de exigencia que faltaba.
