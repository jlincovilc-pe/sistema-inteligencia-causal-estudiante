# Plan actualizado — S03 y S04 (ingeniería real)

**Curso:** ECO-490 / ECON-540 · Sistema de Inteligencia Causal · Edición 2026

## 1. La idea (reemplazo)

Las dos sesiones construyen el contrato de un **servicio de asignación prioritaria a programas de capacitación** (estilo SENCE). 

- Sesión 1: se declara el estimando (ATE de asignar a un curso) y los supuestos que lo identifican sobre `real/jobs`.
- Sesión 2: se exige ese contrato en código (esquema estricto + servicio que se abstiene fuera de soporte).

El producto no es una oración en markdown. Es un servicio que rechaza esquemas inválidos y se abstiene cuando el overlap no se sostiene.

## 3. Sesión 1 · Declarar (sin cambios de código, solo de encuadre)

El encuadre pasa de «qué nos falta para hablar de efecto» a «qué tendría que ser cierto para que un servicio de asignación entregue un número que signifique algo».

El producto sigue siendo la declaración de ignorabilidad, overlap y SUTVA, pero ahora se escribe sabiendo que el jueves un programa la va a exigir.

## 4. Sesión 2 · Exigir (cambios principales)

- El esquema se construye con `CausalSchemaEstricto`.
- Los cuatro fallos del plan ahora se rechazan (más el post-tratamiento).
- En lugar de (o además de) B1, se usa el servicio de asignación que se abstiene fuera del soporte común medido en entrenamiento.
- El cierre es: la frase del martes es el motivo por el que el servicio se niega a responder.

## 7. Entregable del estudiante (reemplazo)

1. Declaración de supuestos para el servicio de asignación.
2. Esquema estricto serializado de `real/jobs`.
3. Prueba de que el servicio se abstiene en al menos una consulta fuera de soporte.
4. Fila de bitácora por sesión.

Queda fuera de clase: la tabla comparativa de estimadores y la justificación de por qué el servicio se abstiene.
