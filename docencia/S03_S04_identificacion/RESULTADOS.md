# Resultados del ensayo de los notebooks activos

Mediciones de las celdas actuales, no de las recomendaciones originales. Son ejemplos sintéticos; no constituyen evidencia empírica sobre un programa público real. Las salidas quedan vacías en los notebooks para construirlos en clase.

## Capítulo 3

| Ejercicio | Medición |
|---|---|
| SCM canónico, semilla 7, n=50 000 | Diferencia observada 1.4255 |
| Descomposición | Efecto 0.4 + selección 1.0197 + desequilibrio del ruido 0.0059 |
| Intervención con exógenas compartidas | 0.4000 |
| Dos mundos con idéntica tabla | ATE bajo do: 1 en A y 0 en B |
| Contrafactual del primer participante | Observado 0.6767 aprox.; sin programa 0.2767 aprox.; efecto 0.4 |
| Cadena sin confusión, n=2000, semilla 12 | Correlación parcial 0.0087; p=0.6971 |
| Mundo con confusión no observada | Correlación parcial −0.2685; p<0.0001; esa independencia no está implicada por su grafo |
| A1 real/jobs train, n=1033 | Diferencia 1600.77; OLS 1596.04; PDS 1595.84 |
| Rango común de propensity entre tratados y controles | 4 observaciones fuera |

## Capítulo 4

| Ejercicio | Medición |
|---|---|
| Caso canónico, n=5000, semilla 4 | Padres/edad: 1.010; padres/experiencia: 1.518 |
| Esquema JSON | Ida y vuelta igual; proyección conserva el orden |
| Cinco fallos estructurales (ensayo de entrada) | Rechazados con mensaje de columnas o covariables requeridas |
| Cambio de esquema | El original permanece intacto; el esquema alternativo valida y conserva el coeficiente diferente |
| OLS real/jobs sin trabajo_78 | 1596.04 |
| OLS incluyendo trabajo_78 | 1147.16; comparación diagnóstica previa; ahora se rechaza al declararla posterior |
| Lote de validación ihdp_medium | 400 consultas; 177 fuera de al menos un intervalo de B1 (44.25%) |

La auditoría del soporte usa `support.json`, `feature_list.json` y `training_meta.json` reales de B1, no respuestas inventadas. No verifica soporte conjunto ni reestima límites sobre validación.

## Alcance del ensayo de entrada

Las celdas analíticas se ejecutaron en orden sin errores. El primer ensayo completo tomó aproximadamente 2.5 s para el capítulo 3 y 0.14 s para el capítulo 4; incluyen importaciones y, en el capítulo 3, un gráfico con backend no interactivo. Esas duraciones no estiman el tiempo de aula.

En el ensayo de entrada, las llamadas HTTP de B1 no se completaron por restricciones locales. La integración conserva la auditoría de sus artefactos y sustituye esas llamadas por ServicioAsignacion. El ensayo actual se documenta a continuación; no se presenta el ensayo de entrada como verificación HTTP de B1.

## Mediciones de integración 100

Pruebas ejecutadas contra los módulos del monorepo; los cuatro tests originales del paquete se conservan sin cambios de lógica.

| Fallo | Resultado medido |
|---|---|
| origen renombrado | ValueError: "Columnas requeridas ausentes: ['edad']" |
| filtro sin variación | ValueError: Tratamiento constante: educacion |
| tratamiento entre controles | ValueError: Columna con doble rol: ['educacion'] |
| instrumento entre controles | ValueError: Columna con doble rol: ['padres'] |
| esquema desincronizado | ValueError: Columnas no declaradas en el esquema: ['sin_declarar'] |
| sin covariables | ValueError: Falta el conjunto de covariables |
| trabajo_78 posterior declarado | ValueError: Covariable posterior al tratamiento declarada como pre: ['trabajo_78'] |

Tests: **27 aprobados**, 0 fallos, 0 errores, 0 omitidos.

| Contrato / lote | Consultas | Abstenciones | Porcentaje |
|---|---:|---:|---:|
| B1/A2, ihdp_medium validation; auditoría conservada | 400 | 177 | 44.250000% |
| ServicioAsignacion, real/jobs validation | 344 | 1 | 0.290698% |

Soporte común fijado en las 1033 filas de entrenamiento: **[0.110999262912, 0.495631318372]**. Propensity de la consulta externa observada: **0.500673941259**; devuelve `abstiene=True`, `ate=None`. El ATE OLS servido es **1596.04221438**.

La tasa se mide por consulta individual; un lote mixto provoca abstención agregada conservadora. Validación no ajusta propensity ni límites. Las dos filas de la tabla usan distintas poblaciones y reglas y no son comparables como calidad del modelo.

La API integrada se comprobó con solicitudes HTTP sobre transporte ASGI y un artefacto serializado recargado. No se afirma haber abierto un puerto TCP en este entorno ni haber verificado HTTP de B1/A2; su auditoría de artefactos permanece idéntica.
