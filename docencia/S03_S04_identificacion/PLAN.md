# Plan S03/S04 · Contrato de producción integrado

Dos sesiones de **75 min de trabajo y 5 min de margen**. Se conserva el minutado de final_03_04 y sus preguntas de predicción. Las importaciones y los módulos se entregan escritos; se construyen los análisis y se cambian entradas. El tiempo de CPU no mide tiempo de aula.

## 1. La idea

Las dos sesiones construyen el contrato de un servicio de apoyo a la evaluación de asignación a programas de capacitación, siguiendo `docs/PLAN_actualizado.md` del paquete de recomendaciones.

- Sesión 1: declarar el estimando ATE y los supuestos sobre real/jobs.
- Sesión 2: exigir ese contrato en código con CausalSchemaEstricto y ServicioAsignacion; rechazar entradas inválidas y abstenerse fuera del soporte común medido en entrenamiento.

La implementación devuelve un ATE ajustado por OLS, no beneficios individuales, un ranking ni una asignación de cupos. La expresión «asignación prioritaria» de la recomendación requiere heterogeneidad, presupuesto y una política adicional. Los datos del ejemplo son sintéticos. El contrato verifica estructura y declaraciones; no demuestra ignorabilidad ni SUTVA.

## 2. Integración que ejecuta el monorepo

- `03_notebooks_caso_estudio/lib/schema_estricto.py`: implementación compartida. `lib/schema.py::CausalSchema` hereda su validación para conservar imports existentes. L04 también hereda esta implementación.
- `04_produccion_causal/B1_servicio_dml/app/servicio_asignacion.py`: entrenamiento solo con train, soporte común de propensity y consultas de covariables sin resultado ni tratamiento.
- `app/asignacion.py`: API independiente que carga un artefacto ya entrenado. No cambia las rutas ni los artefactos de B1/A2.
- Los imports cortos de la recomendación son adaptadores que reexportan esas implementaciones, sin otra lógica de validación.

La recomendación no especifica una ruta absoluta para sus módulos y usa `bundle.df`, que no existe en el cargador. Se adoptan las rutas compartidas anteriores y un alias de preparación del notebook para ejecutar literalmente sus celdas de rechazo y consulta. `row_id` solo se admite cuando está declarado como auxiliar; no entra al modelo.

## 3. Sesión 1 · Declarar

El encuadre de servicio explicita para qué se declaran los supuestos; se conserva íntegramente el notebook del capítulo 3, incluidos su código, minutado y preguntas. Su producto sigue siendo ignorabilidad, overlap y SUTVA escritos y defendidos. No se atribuye al código la verificación de esos supuestos.


| Minutos | Trabajo concreto | Para qué sirve |
|---|---|---|
| 0–5 | Formular población, intervención y resultado | Distinguir efecto de predicción |
| 5–17 | Simular y descomponer la diferencia observada | Separar efecto, selección y desequilibrio del ruido |
| 17–27 | Intervenir y comparar dos SCM con la misma tabla | Mostrar no identificación a partir de asociación |
| 27–37 | Abducción, acción y predicción para una persona | Construir un contrafactual preservando exógenas |
| 37–50 | Contrastar una implicación de la cadena y abrir un collider | Derivar la independencia del grafo antes de probarla |
| 50–70 | Diagnosticar balance y soporte; comparar diferencia, OLS y PDS | Interpretar A1 bajo supuestos explícitos |
| 70–75 | Entregar una afirmación causal condicionada | Explicitar límites y amenaza concreta |
| 75–80 | Retomar una variación y resolver dudas | Absorber diferencias de ritmo |

**Trabajo guiado:** cambiar umbral de selección; calcular el contrafactual de un no participante; añadir una vía directa de Z a Y; justificar una covariable de A1. Las variaciones sustituyen parte de la discusión de cada bloque, no se suman como clases adicionales.

La correlación parcial se entrega implementada. Se interpreta un contraste gaussiano, sin programar 300 simulaciones ni presentar una sola realización como tasa de rechazo. Do-calculus formal y sensibilidad avanzada quedan para capítulos posteriores.

## 4. Sesión 2 · Exigir


| Minutos | Trabajo concreto | Para qué sirve |
|---|---|---|
| 0–5 | Decidir qué debe viajar con los datos | Plantear la deriva semántica |
| 5–18 | Estimar con padres/edad y padres/experiencia | Cuantificar el costo de elegir mal X |
| 18–30 | Proyectar y serializar un esquema estricto | Respetar orden, identidad y transporte de roles |
| 30–43 | Provocar cinco errores y comparar dos esquemas válidos | Distinguir aceptación estructural de legitimidad causal |
| 43–56 | Añadir un control derivado de re78 y revisar su origen | Mostrar una fuga declarada que el contrato estricto rechaza |
| 56–72 | Conservar la auditoría de 400 consultas B1 y consultar ServicioAsignacion sobre real/jobs | Medir abstención y revisar el contrato del servicio |
| 72–75 | Entregar una ficha operativa | Elegir responsable y acción ante el fallo |
| 75–80 | Discusión y recuperación de ritmo | Proteger el cierre |

**Trabajo guiado:** aumentar la muestra del caso canónico; invertir las columnas físicas; predecir errores antes de validar; justificar la exclusión de trabajo_78; explicar la unión de 25 límites de soporte.


Se reemplaza la definición docente por el import de CausalSchemaEstricto. Los cinco casos originales se mantienen y se añade desincronización por columna no declarada; trabajo_78 se rechaza por su declaración explícita de post-tratamiento. Si se omite esa declaración, el esquema no puede descubrir su origen causal.

En el bloque 56–72 se conserva el código exacto de la auditoría de B1: 400 filas de ihdp_medium contra sus intervalos marginales. Se sustituye la antigua llamada HTTP por la celda literal de ServicioAsignacion y se mide también su abstención en validación de real/jobs. Son poblaciones y reglas distintas; no se equiparan sus porcentajes.

Distribución dentro de los mismos 16 minutos: 5 min para interpretar la auditoría B1 ya preparada, 7 min para soporte común y consultas al servicio integrado, 4 min para medir abstención y justificar la decisión. El soporte es `[max(min(e|D=0),min(e|D=1)), min(max(e|D=0),max(e|D=1))]`, calculado solo en train con un modelo de propensity entrenado en train.

## 5. Medición y aceptación

RESULTADOS.md contiene los valores previos conservados y las mediciones nuevas obtenidas al ejecutar las pruebas y los notebooks. Se exige ValueError ante los fallos estructurales y ante controles explícitamente posteriores; al menos una consulta fuera del soporte devuelve abstiene=True y ate=None. Se comprueban persistencia, orden y rutas HTTP de la API integrada sin abrir sockets, mediante transporte ASGI.

## 6. Reproducción

Desde la raíz del monorepo:

```bash
python final_03_04_100/verificar.py
```

Para entrenar un artefacto y servirlo, sin entrenar durante consultas:

```bash
python 04_produccion_causal/B1_servicio_dml/scripts/train_asignacion.py --out final_03_04_100/artefactos/asignacion
```

Desde `04_produccion_causal/B1_servicio_dml`, con la ruta absoluta al artefacto:

```bash
ASIGNACION_BUNDLE=/ruta/absoluta/final_03_04_100/artefactos/asignacion/servicio.joblib uvicorn app.asignacion:app --host 127.0.0.1 --port 8001
```

La API expone `/health`, `/metadata` y `/predict` con `features`. Requiere las dependencias de B1 y de Serie A. El directorio de entrega conserva las rutas relativas de los módulos para aplicar los cambios sobre el mismo monorepo; no duplica el benchmark ni los artefactos originales de B1.

## 7. Entregable del estudiante

1. Declaración de supuestos para el servicio de apoyo a asignación.
2. Esquema estricto serializado de real/jobs, incluidas las exclusiones temporales.
3. Prueba de una abstención fuera del soporte común y su medición en el lote de validación.
4. Fila de bitácora por sesión que identifique el fallo, el supuesto y la decisión.

Se mantiene la comparación de estimadores de A1 dentro del bloque ya previsto. La tabla ampliada con intervalos y la justificación escrita completa quedan para fuera de clase. El servicio aplica la regla de soporte declarada, no verifica la verdad de toda la declaración causal.
