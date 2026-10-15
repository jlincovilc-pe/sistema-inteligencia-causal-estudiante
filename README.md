# Sistema de Inteligencia Causal — repositorio del estudiante

Edición pública local del curso: 32 sesiones de 90 minutos, 27 labs formativos, cuatro casos Serie A y un proyecto final único. El recorrido no requiere nube, Docker ni credenciales externas.

## Instalación

Entorno validado: Linux x86_64 y Python 3.13.13.

```bash
python3 -m venv .venv-causal
. .venv-causal/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name sic-estudiante --display-name "Python (SIC estudiante)"
python scripts/doctor_minimo.py
python scripts/validate_student_repo.py
```

La guía completa de dependencias está en [`docs/REQUISITOS_NOTEBOOKS.md`](docs/REQUISITOS_NOTEBOOKS.md).

## Recorrido de notebooks

### Serie A

- `03_notebooks_caso_estudio/notebooks/A1_identificacion_jobs.ipynb`
- `03_notebooks_caso_estudio/notebooks/A2_dml_ihdp_medium.ipynb`
- `03_notebooks_caso_estudio/notebooks/A3_cate_meta_learners_ihdp.ipynb`
- `03_notebooks_caso_estudio/notebooks/A4_policy_uplift_ihdp.ipynb`

### Labs de sesión

Hay un notebook de estudiante por cada lab L01–L15 y L17–L28:

- `L01_causalidad_elemental/lab.ipynb`
- `L02_entorno_local/lab.ipynb`
- `L03_scm_jerarquia_causal/lab.ipynb`
- `L04_schema_roles_jobs/lab.ipynb`
- `L05_regularizacion_pds/lab.ipynb`
- `L06_balance_smd/lab.ipynb`
- `L07_puerta_trasera/lab.ipynb`
- `L08_features_sin_fuga/lab.ipynb`
- `L09_ortogonalidad_crossfitting/lab.ipynb`
- `L10_dml_plr_irm/lab.ipynb`
- `L11_validacion_qini_placebo_evalue/lab.ipynb`
- `L12_servir_estimador/lab.ipynb`
- `L13_meta_learners/lab.ipynb`
- `L14_arboles_bosques_causales/lab.ipynb`
- `L15_repaso_integrador/lab.ipynb`
- `L17_model_cards_registro_local/lab.ipynb`
- `L18_ci_local_estadistico/lab.ipynb`
- `L19_explicacion_causal_equidad_rutas/lab.ipynb`
- `L20_etica_interpretabilidad_comunicacion/lab.ipynb`
- `L21_decisiones_estructurales/lab.ipynb`
- `L22_politicas_optimas/lab.ipynb`
- `L23_uplift_app_local/lab.ipynb`
- `L24_transportabilidad/lab.ipynb`
- `L25_monitoreo_supuestos/lab.ipynb`
- `L26_descubrimiento_causal/lab.ipynb`
- `L27_aprendizaje_continuo_rl_causal/lab.ipynb`
- `L28_lado_humano/lab.ipynb`

L16 es una guía Markdown de preparación de la defensa y no tiene notebook.

## Orden recomendado

1. Lee el capítulo indicado en `01_silabo/lectura_por_sesion.md`.
2. Ejecuta el lab de la sesión y guarda tus respuestas y artefactos en tu copia local.
3. Trabaja A1–A4 como integración formativa.
4. Usa `04_produccion_causal/` para construir servicio, tarjeta, puerta, registro y monitor local.
5. Entrega solo el proyecto descrito en `06_proyecto_final/`; los labs y Serie A/B son formativos.

Los notebooks A1–A4 y los labs que señalan una sección de evaluación reservada terminan antes de las comparaciones con verdad sintética u oráculos. Esas secciones no forman parte de la evidencia pública del estudiante; las decisiones deben apoyarse en observables, incertidumbre, soporte y supuestos declarados.

## Qué no contiene este repositorio

No contiene soluciones, autograders, datos `truth`, claves de evaluación, guía del profesor, fuentes Typst, artefactos docentes ni credenciales.
