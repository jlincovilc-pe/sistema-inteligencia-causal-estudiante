# Docencia: ejemplos semanales

Esta carpeta organiza notebooks de clase y materiales docentes que ejemplifican
conceptos de cada semana. No reemplaza el sílabo ni el plan general del curso,
cuyas fuentes canónicas permanecen en la raíz del repositorio.

## Estructura

Cada carpeta `SXX_SYY_tema/` reúne el ejemplo de una semana o bloque de sesiones:

```text
SXX_SYY_tema/
├── PLAN.md                 # propósito, conexión con la monografía y guion
├── sesion1_<verbo>.ipynb   # notebook de clase
├── sesion2_<verbo>.ipynb   # segundo notebook, si corresponde
├── NOTAS_PROFESOR.md       # preparación, riesgos y decisiones docentes
├── RESULTADOS.md           # resultados reproducidos y procedencia
├── recursos/               # materiales de apoyo específicos de la semana
└── recomendaciones/        # propuestas externas o alternativas, identificadas
```

Los archivos opcionales se incluyen solo cuando aportan a esa semana. Los
notebooks deben señalar qué componentes del repositorio ejemplifican y dejar
explícitas sus dependencias y límites.

## Ejemplo disponible

La entrega integrada está en [`final_03_04_100/`](../final_03_04_100/): los dos
notebooks S03/S04, su plan, notas, mediciones y verificación. Conserva los 80 minutos
por sesión y usa el mismo contrato estricto que ejecutan las bibliotecas del monorepo.

La propuesta original permanece como entrada de referencia en
[`recomendacion_grok/`](./S03_S04_identificacion/recomendacion_grok/). Sus módulos
se integraron en `03_notebooks_caso_estudio/lib/schema_estricto.py` y
`04_produccion_causal/B1_servicio_dml/app/servicio_asignacion.py`; B1/A2 conserva su
propia auditoría. El servicio de capacitación tiene una API independiente.

Las rutas semanales [`S03_S04_identificacion/`](./S03_S04_identificacion/) se
mantienen sincronizadas con la entrega. No contienen otra solución S03/S04 ni
copias ejecutadas. Los ZIP anteriores son entradas históricas, no la entrega integrada.

## Nueva semana

Usa [`_plantilla_semana/`](./_plantilla_semana/) como guía y crea una carpeta
con el patrón `SXX_SYY_tema`. Registra allí el plan semanal, los notebooks,
notas y resultados propios de ese bloque; conserva las referencias a los
componentes generales en vez de duplicar sus fuentes canónicas.
