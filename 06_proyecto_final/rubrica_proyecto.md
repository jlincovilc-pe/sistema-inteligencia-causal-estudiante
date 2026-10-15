# Rúbrica del trabajo final (100 pts → 70% del curso)

**Enfoque:** se evalúa un prototipo causal local, reproducible y auditable, alineado con `04_produccion_causal/`. No se premia una plataforma externa por sí misma.

| Criterio | Pts | Evidencia esperada |
|---|---:|---|
| Pregunta causal + estimando + supuestos | 12 | Pregunta de decisión, DAG o estrategia defendible, población de validez y condición que obligaría a revisar |
| Datos y transparencia | 8 | Escenario, datos observados/datos de evaluación reservados, hash, semilla, split y límites |
| Estimación correcta | 15 | ATE, CATE o valor de política reproducible; incertidumbre cuyo objeto se declara; variante DML si corresponde, cross-fitting o validación equivalente y sin fuga de datos de evaluación reservados |
| Decisión, abstención y comunicación | 15 | Interpretación del efecto, soporte, umbral/coste de decisión, qué cambiaría la recomendación, límites y comunicación clara |
| Servicio local y humo | 10 | Servicio local o CLI equivalente: estimando elegido, incertidumbre, metadatos, abstención y pruebas de humo |
| Puerta causal y registro | 10 | Estados `pasa/alerta/falla`, hashes, versiones, bloqueo y alias `champion` |
| Model card | 10 | Esquema válido, estimando, supuestos registrados como `observable`/`no_observable`, evidencia falsificable, población, soporte y límites |
| Monitoreo y falsificación | 8 | Control negativo, deriva, relación de asignación cuando aplique, overlap/balance, umbrales declarados y acción operativa |
| Defensa y claridad | 7 | README, cierre y defensa reproducible y acotada |
| Evidencia y reproducibilidad | 5 | Comandos, salidas, manifiestos y relación entre artefactos |
| **Total** | **100** | |

### Descriptor de la defensa: suficiente frente a limítrofe

La respuesta de defensa se contrasta con los artefactos entregados y se puntúa
con los criterios anteriores; esta tabla solo hace observable la diferencia y
no añade puntos ni una entrega.

| Nivel | Evidencia mínima que debe aparecer | Lectura para la rúbrica |
|---|---|---|
| **Suficiente** | Nombra la decisión y el estimando (ATE, CATE o valor de política), la población, el objeto de la incertidumbre, un supuesto no observable y un cambio mínimo que detendría la recomendación; enlaza cada afirmación con un artefacto. | Puede satisfacer los descriptores de pregunta/estimando, decisión y defensa si los artefactos son coherentes. |
| **Limítrofe** | Dice “hay drift/reentreno” o “puede haber confusión”, pero omite el estimando, la población, qué cubre el intervalo o el umbral que detiene la decisión. | Solo recibe el crédito parcial que corresponda a la evidencia mostrada; no se trata como respuesta suficiente por fluidez verbal. |

**No aprueba** si el humo falla, si el bundle contiene `datos de evaluación reservados` usado en
entrenamiento, si una versión con puerta `falla` se promueve, si el servicio o CLI no
se abstiene fuera del soporte o si no se puede reconstruir la versión servida. Un
monitor puede emitir señales de revisión, pero no debe presentarlas como una prueba
automática de que identificó la causa del cambio.

---

## Sección opcional — Predictivo vs causal

La comparación entre un ranking predictivo y una política causal puede enriquecer el trabajo, pero no es un requisito del prototipo base ni una condición de aprobación. Si se incluye, debe responder:

1. **Ranking predictivo:** ordenar por `Y_hat`, riesgo u otro score predictivo y
   tratar al top-B%.
2. **Policy causal:** ordenar por `tau_hat(x)` o valor causal agregado con el
   mismo presupuesto B.
3. **Comparación cuantitativa:** welfare, Qini, uplift, subgrupos u otra métrica
   defendible.
4. **Implicación de negocio:** explicar en 5–10 líneas quién cambia, qué valor
   cambia y qué riesgo permanece.

| Subcriterio | Evidencia esperada |
|---|---|
| Baseline predictivo | Ranking reproducible y presupuesto claro |
| Política causal | Comparación 1:1 con el baseline, si el proyecto la implementa |
| Métrica | Números, tabla o figura con interpretación |
| Narrativa | Concreta y limitada por los supuestos |

Esta sección no suma puntos adicionales; se valora dentro de la claridad de la decisión si aporta evidencia útil.

## Puerta causal y registro (10 pts)

| Subcriterio | Pts |
|---|---:|
| Diagnósticos observables y estados `pasa/alerta/falla` | 3 |
| Versiones inmutables, hashes y `manifest.json` | 3 |
| Promoción segura y alias `champion` | 2 |
| Prueba de integridad y bloqueo de una versión fallida | 2 |

## Monitoreo operativo (8 pts)

| Subcriterio | Pts |
|---|---:|
| Deriva de covariables (PSI/KS) y cambio de distribución | 2 |
| Solapamiento, ESS, SMD o señal equivalente | 2 |
| Control negativo, relación entre asignación y covariables, y diferencia entre proxy y efecto identificado | 2 |
| Regla de acción, abstención y límites documentados | 2 |

## Alineación con el prototipo

La implementación debe seguir los contratos de
`04_produccion_causal/`: tarjeta causal, puerta, registro local, servicio,
abstención y monitor. Puede reutilizar código de `04_produccion_causal/`, pero
debe declarar qué se reutiliza y qué se modifica. Docker, MLflow y DVC son
extensiones opcionales; no reemplazan la validación local. La elección entre ATE,
CATE o policy debe determinar qué devuelve la interfaz y qué cubre su incertidumbre.
