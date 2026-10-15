# Guía del proyecto final (S29–S32)

**Peso:** 70% de la nota final · **Calendario:** [`../CALENDARIO.md`](../CALENDARIO.md)
**Contrato vigente:** [`ADENDA_CONTRATOS_EVALUACION.md`](./ADENDA_CONTRATOS_EVALUACION.md)

## Objetivo

Entregar un **sistema de inteligencia causal en producción local** que pueda
ser ejecutado por otra persona sin cuentas externas ni servicios de nube. El
proyecto debe integrar:

1. Pregunta causal, estimando y supuestos.
2. Estimación ATE, CATE o valor de política, con incertidumbre y una declaración explícita del objeto que cubre el intervalo.
3. Puerta causal con estados `pasa`, `alerta` y `falla`.
4. Model card validada contra un schema.
5. Registro de versiones con hashes y alias `champion`.
6. Servicio HTTP o CLI equivalente que devuelva efecto/policy, su incertidumbre y se abstenga fuera de soporte.
7. Monitoreo con una acción operativa: continuar, alertar, revisar, abstenerse o reentrenar. Las señales orientan una revisión; no prueban por sí solas la causa del cambio.
8. Comparación opcional entre ranking predictivo y política causal bajo el mismo presupuesto; no es requisito del prototipo base.

**No es suficiente** con que un endpoint responda: el sistema debe demostrar que
no promueve ni sirve silenciosamente una versión con supuestos incumplidos.

<!-- OPS:EVA-01:inicio -->
## Filtro técnico y recuperación

El filtro no da puntos y bloquea la rúbrica completa. Debe informar la ruta exacta del problema y distinguir:

- `FORMATO`: schema, ruta, nombre, comando o hash que puede corregirse sin cambiar cifras, estimandos ni decisiones;
- `SUSTANCIA`: falta pregunta, estimando, puerta o abstención; o aparecen `truth`, `y0`, `y1` o `tau` en el entrenamiento o bundle.

Un error de `FORMATO` abre 48 horas para corregir solo la forma. Un error de `SUSTANCIA` no tiene esa ventana. Si el formato no se corrige, pero el cierre y la defensa sostienen pregunta, estimando, incertidumbre y supuesto, se pueden puntuar los criterios 1 y 2 de la rúbrica, que actualmente suman 6/20 puntos del proyecto; el resto queda en cero. No hay reentrega de código para cambiar el resultado causal.

HTTP y CLI son equivalentes y no hay puntos por elegir uno u otro. El filtro no
convierte una ruta de transporte en criterio de integridad: la autoría y la
comprensión se comprueban con los artefactos entregados y la defensa.
<!-- OPS:EVA-01:fin -->

<!-- OPS:EVA-04:inicio -->
## Defensa final

La defensa dura 15 minutos: 10 de exposición y 5 de preguntas. Las preguntas fijas son:

1. Muestra el artefacto, log o fila que justifica la abstención o el estado de la puerta.
2. Nombra un supuesto no observable y explica cómo lo acotaste o por qué no pudiste hacerlo.
3. ¿Qué cambio mínimo en la evidencia, la población o el umbral de decisión haría que dejaras de recomendar esta intervención?

Si falla el equipo, se usa la evidencia ya entregada y el video de respaldo solo como constancia. No se depura ni se cambian cifras durante la defensa.
<!-- OPS:EVA-04:fin -->

## Datos

Usar `data_benchmark_causal/causal_benchmark_synthetic/datasets/` o una
extensión documentada del mismo esquema. Es obligatorio declarar:

- `scenario_id`;
- qué datos son observados y cuáles son `truth`;
- semilla y split;
- hash del dataset usado para entrenar;
- que `truth` no entra al entrenamiento ni al bundle de servicio;
- qué objeto cubre cada intervalo y qué afirmaciones no están respaldadas.
- qué sensibilidad es compatible con el estimando y la escala; si no existe, registra `sin_cuantificacion_valida` y la limitación.

## Actividades de preparación y entrega final

P1 y P2 son actividades formativas. Ayudan a preparar el trabajo, pero no se entregan ni se califican por separado.

| ID | Momento | Actividad |
|---|---|---|
| **P1** | Trabajo autónomo | Definir repo, pregunta causal, estimando, datos, baseline y límites |
| **P2** | Revisión formativa | Revisar 2–3 proyectos y recibir observaciones sobre la puerta causal |
| **Entrega final** | Fecha única del cronograma | Presentar el prototipo local completo, su evidencia y la defensa final |

## Estructura de repo sugerida

```text
proyecto_<apellido>/
  README.md
  model_card.json
  model_card.md
  schemas/
    causal-model-card.json
  src/
    causal_service/
  service/
    api.py o cli.py
  scripts/
    demo.py
    monitor.py
    validate_release.py
  artifacts/
    v0001/
    alias_champion.json
  tests/
    test_humo.py
    test_gate.py
    test_support.py
    test_registry.py
```

## Definición de terminado

El proyecto debe poder ejecutar desde su raíz:

```bash
make ci
make demo
make monitor
```

El resultado debe incluir una demostración de tres situaciones:

1. escenario sano: se registra y promueve;
2. positividad o soporte insuficiente: se bloquea o abstiene;
3. cambio de identificación o confusor oculto en el escenario de prueba: se alerta o bloquea. Esta demostración verifica el comportamiento del prototipo bajo un DGP conocido; no prueba que un monitor descubra toda confusión en datos reales.

El escenario con verdad conocida sirve para comprobar el comportamiento del
prototipo durante la práctica. La conclusión del proyecto debe sostenerse con
datos observados y evidencia disponible para el estudiante; no se puede usar
PEHE, `tau` ni la verdad reservada para justificar una decisión de producción.

## Reutilización del curso

Se pueden reutilizar artefactos de las prácticas guiadas y del prototipo abierto,
pero se debe declarar:

- qué código se reutiliza;
- qué parte es original;
- qué supuestos se mantienen;
- qué cambios se hicieron en el bundle, la política o el servicio.

El proyecto es docente y no puede presentar datos sintéticos como datos clínicos
reales.
