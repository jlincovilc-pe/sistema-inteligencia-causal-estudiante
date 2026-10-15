# L16 · Guía de la defensa de avance (sesión 16)

> **Estado:** checkpoint formativo. No es una evaluación oficial ni una entrega calificada. L16 se mantiene como guía Markdown y no requiere `solution.ipynb`.

<!-- OPS:ENS-02:inicio -->
## Producto de S16 (necesario para llegar bien a S29)

Escribe en la bitácora estas tres líneas y nada más:

1. Pregunta: ¿Debo hacer X para lograr Y?
2. Estimando: `ATE` | `CATE` | `valor_politica`.
3. Por qué este caso no es uno guiado de los labs, o qué benchmark autorizado usarás.

Si no tienes datos propios autorizados, elige un escenario del benchmark y decláralo. Llegar a S29 sin estas líneas significa que S29 no alcanza para elegir el caso, integrar la puerta, preparar el servicio y configurar el monitor desde cero.

Esto no se califica. Es la condición práctica para no empezar de cero.
<!-- OPS:ENS-02:fin -->

**Qué es.** Una conversación de 10–12 minutos por grupo sobre el **hilo A1→A3** del proyecto (Caps. 1–15), con los artefactos delante. No hay código nuevo: se defiende lo que ya existe. El objetivo es comprobar que el grupo **entiende los supuestos de su propio resultado**, no que lo recita.

## 1. Qué trae el grupo (antes de entrar)
- [ ] `artefactos/a2.json` (estimación A2) y el notebook que lo produce, ejecutable de arriba abajo.
- [ ] Su **mapa de supuestos** (el de L15): por capítulo, qué supuesto aparece, si es observable / falsificable / no observable y cómo se trató (medido · contrastado · declarado y acotado).
- [ ] Su **bitácora** de los labs L01–L15 (las filas de seis campos).
- [ ] Una versión de **tres capas** del resultado (como la de L28), aunque sea borrador.

## 2. Lista de verificación del evaluador (sí / no, 1 minuto)
| # | Verificación | Sí / No |
|---|---|---|
| 1 | El notebook corre completo sin editar rutas ni ejecutar celdas fuera de orden | |
| 2 | El estimando está dicho con palabras (¿ATE, ATT, CATE? ¿en qué población?) | |
| 3 | El resultado trae **intervalo** y la población de validez | |
| 4 | Hay al menos un supuesto **no observable** nombrado, con su tratamiento (declarado y acotado, p. ej. con E-value) | |
| 5 | El conjunto de ajuste está justificado con un grafo o con una regla de roles (sin controlar por descendientes ni colisionadores) | |
| 6 | Las características **no tienen fuga** (nada medido después del tratamiento ni derivado del resultado) | |
| 7 | La validación no es solo «el RMSE baja»: hay balance, placebo o equivalente | |
| 8 | Dice cuándo **se abstendría** (soporte insuficiente, solapamiento pobre) | |
| 9 | El artefacto A2 tiene hash de los datos y semilla | |
| 10 | La capa 1 del resumen no tiene jerga y lleva población + rango | |

## 3. Preguntas para el grupo (elige 4–5; una por bloque)
**Bloque 1 — Pregunta causal y jerarquía (Caps. 1–3)**
1. ¿Qué parte de su pregunta es asociativa, cuál intervencional y cuál contrafactual? ¿Qué le falta a sus datos para responder la que no es asociativa?
2. Dibujen en el pizarrón el grafo de su problema. ¿Qué nodo omitieron y qué haría su resultado si existiera?

**Bloque 2 — Ingeniería y datos (Caps. 4, 6)**
3. Muestren el esquema de roles de sus columnas. ¿Qué columna podría ser un colisionador o un mediador? ¿Qué pasaría si la agregaran al ajuste?
4. ¿Cómo comprobaron que la regularización no apartó una covariable que ajustaba la confusión? (Pregunta de «doble selección».)

**Bloque 3 — Identificación y balance (Caps. 7–9)**
5. ¿Qué diferencia hay entre «el SMD quedó bajo 0,1» y «la no confusión se cumple»?
6. Su conjunto de ajuste, ¿cierra la puerta trasera? ¿Cómo lo saben, no solo lo creen?
7. Nombren una característica de su conjunto que sea sospechosa de fuga y expliquen cómo la descartaron.

**Bloque 4 — Estimación (Caps. 10–15)**
8. ¿Por qué el *cross-fitting*? ¿Qué cambiaría en su estimación si lo quitaran? (Esperen una respuesta con sesgo de sobreajuste, no solo «lo dice el libro».)
9. ¿Qué mostraría su placebo si el efecto fuera falso? ¿Y si hubiera un confusor no medido?
10. Les doy un E-value de 1,8. ¿Qué le dirían a quien decide?
11. Entre el estimador de A2 y un meta-learner: ¿qué diferencia habría en el CATE y en qué población importaría?
12. ¿Cuándo no servirían este estimador? (Pista: soporte, tamaño de muestra, efecto muy heterogéneo.)

**Cierre (siempre)**
13. Si mañana les quitaran una prueba de su informe, ¿cuál sería la que más lamentarían perder y por qué?

## 4. Señales de que el grupo no entiende su propio resultado
- Cita el valor del E-value o del SMD pero no sabe decir qué supuesto protege.
- Dice «el modelo controla por todo» (no distingue entre ajustar y causar).
- No puede decir cuándo se **abstendría**.
- Todas sus respuestas están en el notebook y ninguna en un argumento.
- La capa 1 es una frase con «ATE», «DML» o «ortogonal».

## 5. Rúbrica sugerida (20 puntos; ajusta los pesos)
| Criterio | Puntos | Qué se premia |
|---|---|---|
| Estimando y población dichos con claridad | 3 | Una oración sin jerga que un tercero entiende |
| Supuestos nombrados y tratados | 5 | Al menos uno no observable, con su tratamiento y su límite |
| Diagnósticos usados con criterio | 4 | Balance, placebo, solapamiento: sabe qué detecta y qué no |
| Intervalo y abstención | 3 | Reporta incertidumbre y sabe cuándo no debe decidir |
| Reproducibilidad del artefacto | 2 | Hash, semilla, ejecuta de arriba abajo |
| Respuestas a las preguntas del grupo | 3 | Argumenta, no recita |

**Nota de uso.** Este archivo no se ejecuta y no tiene verificación automática: la evaluación es oral. Si prefieren una versión escrita, las preguntas 5–12 sirven como examen de respuesta corta.
