# Notas para facilitar S03/S04 con el contrato integrado

Se conservan los 75 min de actividades y 5 de margen de cada notebook, las preguntas de predicción y la distinción entre datos simulados, estimación y supuestos. El capítulo 3 permanece byte a byte igual al ZIP de entrada. Las coincidencias de diferencia de medias, OLS y PDS se interpretan como resultados, no se fuerza su desacuerdo.

## Qué cambia al pasar de clase a producción

CausalSchemaEstricto es la única implementación operacional de validación de roles. El alias histórico CausalSchema y los ejercicios L04 delegan en ella. El notebook de capítulo 4 importa el mismo módulo; no contiene otra clase docente. Sus cambios de roles se hacen con `replace`, dejando intacto el objeto original. La clase del paquete es mutable; el servicio toma una copia del esquema y de los supuestos al construirse, para que una modificación del objeto de entrada no cambie el contrato servido.

La validación de entrenamiento exige columnas declaradas, covariables no vacías, roles únicos y tratamiento con variación. Rechaza columnas extra no registradas y controles que se hayan declarado posteriores. Los identificadores auxiliares deben declararse por separado. La excepción de columnas ausentes es ValueError y conserva compatibilidad con los consumidores históricos que capturaban KeyError.

La validación de inferencia exige únicamente las covariables, en el orden declarado y con valores numéricos finitos. No pide el resultado futuro ni variación de tratamiento en una consulta individual. Los campos extra se rechazan. Así se corrige el prototipo, que validaba una consulta como si fuera una muestra de entrenamiento.

## Puntos pedagógicos que permanecen

- En el capítulo 3, U y las perturbaciones son privilegios de la simulación. Los contrafactuales reutilizan las exógenas de la persona; el efecto es 0.4 por construcción.
- Dos SCM pueden tener la misma tabla y distinto efecto de intervención. Un mejor predictor no resuelve esa ambigüedad.
- La independencia de la cadena debe derivarse del grafo antes del contraste. El grafo con collider no implica esa independencia; no rechazar no confirma un grafo.
- En A1 las estimaciones quedan próximas y el soporte común por rangos es un diagnóstico muestral, no una prueba de positividad poblacional.
- En el caso de escolaridad, experiencia contiene al tratamiento. Los coeficientes distintos persisten con más datos; dos esquemas estructuralmente válidos no garantizan dos ajustes causalmente legítimos.
- trabajo_78 se conoce como posterior por su construcción a partir de re78. El ejemplo diagnóstico de coeficientes se conserva, pero ese ajuste no se entrena para servir: el contrato lo rechaza cuando se declara en post_treatment. Sin declaración temporal, no existe detección automática de causalidad.

## Bloque 56–72

Conservar la auditoría original de artefactos B1/A2, con 400 filas de validación de ihdp_medium. Su unión de límites marginales puede excluir muchas filas y no garantiza soporte conjunto aunque una consulta pase. No recalcular límites sobre validación.

ServicioAsignacion se consulta en el mismo bloque, con real/jobs. El modelo de propensity, el ATE OLS y los límites comunes se fijan con train. El lote de validación solo mide abstención. Una fila fuera produce abstiene=True y ate=None; un lote mixto se abstiene de forma conservadora, y la tasa por consultas se calcula llamando por fila.

Los dos porcentajes pertenecen a contratos diferentes. Ningún ATE del ejemplo es un ranking de beneficios individuales ni una política para distribuir cupos. La API app.asignacion es independiente de B1/A2; no se modifica su auditoría ni sus artefactos.

## Preparación

Entregar módulos e importaciones escritos. No transcribir infraestructura en clase. El notebook ya no necesita un servidor para consultar ServicioAsignacion; las pruebas verifican además su API y un artefacto recargado. La API desplegable se inicia después de entrenar y configurar ASIGNACION_BUNDLE, como indica PLAN.md.

VERIFICACION.md lista archivos, comandos, pruebas y comprobaciones de conservación. RESULTADOS.md distingue las mediciones previas de las nuevas. No se guardan notebooks ejecutados ni una segunda solución de S03/S04 en la entrega.
