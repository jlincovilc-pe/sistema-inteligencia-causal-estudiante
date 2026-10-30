# Cambios concretos para sesion2_exigir.ipynb

## Reemplazar bloque 8–25 (construcción del esquema)

En la celda que construye `CausalSchema`, cambiar a:

```python
# EN VIVO
from schema_estricto import CausalSchemaEstricto  # o ajustar import según ubicación

bundle = load_scenario(SCENARIO_A1)
meta = bundle.meta
esquema = CausalSchemaEstricto(
    treatment=bundle.treatment_name,
    outcome=bundle.outcome_name,
    covariates=list(bundle.covariate_names),
    instruments=[],
    post_treatment=[],  # se declara explícitamente vacío
    scenario_id=bundle.scenario_id,
)
esquema.validate(bundle.df)
print(esquema.summary())
```

## Insertar después del bloque 25–40 (romper el contrato)

Añadir celda que demuestre el rechazo de post-tratamiento:

```python
# EN VIVO — fallo silencioso ahora es ruidoso
df_post = bundle.df.copy()
df_post["trabajo_78"] = (df_post["re78"] > 0).astype(int)  # posterior
esquema_mal = CausalSchemaEstricto(
    treatment=esquema.treatment,
    outcome=esquema.outcome,
    covariates=esquema.covariates + ["trabajo_78"],
    post_treatment=["trabajo_78"],
)
try:
    esquema_mal.validate(df_post)
except ValueError as e:
    print("Rechazado:", e)
```

## Reemplazar llamadas a B1 (bloque 52–70) por el servicio de asignación

```python
# EN VIVO — servicio que se abstiene
from servicio_asignacion import ServicioAsignacion
# (entrenar modelo_ps y soporte_lo/hi con los datos de train, como en RESULTADOS.md)
servicio = ServicioAsignacion(esquema=esquema, modelo_ps=ps_model, soporte_lo=lo, soporte_hi=hi, ate=ate_ols, supuestos=["conditional_ignorability", "overlap", "SUTVA"])
print(servicio.metadata())
# consulta dentro
print(servicio.predict(df_dentro))
# consulta fuera
print(servicio.predict(df_fuera))  # debe devolver abstiene=True
```

## Producto de la sesión 2

Serializar el esquema estricto y una fila de bitácora que registre si el servicio se abstuvo o no.
