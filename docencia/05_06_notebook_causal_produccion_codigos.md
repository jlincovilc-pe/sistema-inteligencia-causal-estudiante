# Contenido fuente del notebook causal de producción

Este documento reproduce las celdas del notebook original en su orden: las celdas Markdown aparecen como Markdown y las celdas Python como bloques copiables.

---

## Celda original 1 — Markdown

# Prototipo causal de extremo a extremo — Jobs/LaLonde real (NSW)

Estimando: ATE de la participación sobre `re78` (ingresos de 1978, USD), en la muestra experimental NSW. Usa el CSV real de LaLonde/Dehejia-Wahba y guarda resultados en `artefactos_notebook_causal_real/`.
Fuente: datos públicos NBER; citar a Lalonde (1986) y Dehejia-Wahba. El uso está sujeto a las condiciones de atribución y no comercial indicadas por la fuente.

---

## Celda original 2 — Markdown

## 1. Setup y datos

Se usa la muestra experimental real NSW/LaLonde (tratados y controles asignados aleatoriamente), en `data_benchmark_causal/causal_benchmark_zoo/benchmarks/lalonde_nsw/processed/lalonde_nsw.csv`. La muestra tiene 445 observaciones. Solo se observa el resultado factual `re78`: no hay `y0`, `y1` ni un **ATE** matemáticamente conocido por unidad.

---

## Celda original 3 — Python

```python
import hashlib, json, time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import t as t_dist
from doubleml import DoubleMLData, DoubleMLPLR
from econml.metalearners import TLearner
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LassoCV, LinearRegression, LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler

SEED = 42  # semilla para validación cruzada y learners; los datos no se generan
TRAT, RES = "treat", "re78"
BASE = ["age", "educ", "black", "hispan", "married", "nodegree", "re74", "re75"]
RUTA_RELATIVA_DATOS = Path(
    "data_benchmark_causal/causal_benchmark_zoo/benchmarks/lalonde_nsw/processed/lalonde_nsw.csv"
)
# Busca el CSV desde el directorio actual hacia sus padres, sin fijar una ubicación absoluta.
CANDIDATAS_DATOS = [raiz / RUTA_RELATIVA_DATOS for raiz in (Path.cwd(), *Path.cwd().parents)]
ARCHIVO_DATOS = next((p.resolve() for p in CANDIDATAS_DATOS if p.is_file()), None)
if ARCHIVO_DATOS is None:
    raise FileNotFoundError(
        "No se encontró el CSV real de LaLonde/NSW. Se buscó hacia arriba desde "
        f"{Path.cwd()} con la ruta {RUTA_RELATIVA_DATOS}"
    )

SALIDA = Path("artefactos_notebook_causal_real")
SALIDA.mkdir(exist_ok=True)
print("Datos:", ARCHIVO_DATOS)
print("Artefactos:", SALIDA.resolve())
```

---

## Celda original 4 — Python

```python
# El CSV es una copia procesada del experimento NSW público; no se generan datos ni verdad contrafactual.
df = pd.read_csv(ARCHIVO_DATOS)
df.head(3)
```

---

## Celda original 5 — Python

```python
def validar_esquema(df):
    faltan = [c for c in [TRAT, RES, *BASE] if c not in df.columns]
    if faltan:
        raise ValueError(f"columnas ausentes: {faltan}")
    nulos = df[[TRAT, RES, *BASE]].isna().sum()
    if nulos.any():
        raise ValueError(f"nulos: {nulos[nulos > 0].to_dict()}")
    # Exige que ambos niveles de tratamiento estén presentes, no solo que la variable sea binaria.
    if set(df[TRAT].unique()) != {0, 1}:
        raise ValueError("treat debe ser binario con ambos niveles")
    binarias = ["black", "hispan", "married", "nodegree"]
    if any(not set(df[c].unique()).issubset({0, 1}) for c in binarias):
        raise ValueError("las covariables binarias deben contener solo 0/1")
    if (df[[RES, "re74", "re75"]] < 0).to_numpy().any():
        raise ValueError("ingresos negativos")
    return True


validar_esquema(df)
DATOS = {
    "dataset_id": "lalonde_nsw",
    "n": int(len(df)),
    "tratados": int((df[TRAT] == 1).sum()),
    "controles": int((df[TRAT] == 0).sum()),
    "tasa_tratamiento": round(float(df[TRAT].mean()), 4),
    # Huella del archivo para trazabilidad y reproducibilidad; no es un mecanismo de seguridad.
    "sha256_datos": hashlib.sha256(ARCHIVO_DATOS.read_bytes()).hexdigest(),
    "diseño": "muestra experimental aleatorizada NSW; covariables pretratamiento",
    "limites": "solo resultados factuales; sin contrafactuales individuales; validez externa limitada",
    "fuente": "NBER; Lalonde (1986), Dehejia-Wahba; atribución y uso no comercial según fuente",
}
DATOS
```

---

## Celda original 6 — Markdown

## 2. Pregunta causal y estimando

Cap. 5: el estimando es causal, no un score predictivo. Los supuestos de identificación se declaran aquí y viajan con el modelo.

---

## Celda original 7 — Python

```python
ESPECIFICACION = {
    "pregunta": "¿Cuánto cambian en promedio los ingresos de 1978 por participar en el programa?",
    "estimando": "ATE = E[Y(1) - Y(0)] sobre re78, en dólares de 1978, para la muestra experimental NSW",
    "no_es": "un efecto individual ni un score predictivo",
    "poblacion": "participantes y controles de la muestra experimental NSW/LaLonde disponible (445 unidades)",
    "conjunto_ajuste": BASE,
    "estimador_principal": "diferencia de medias por asignación aleatoria; Welch para el IC",
    "supuestos": [
        {"nombre": "no_confusion_condicional", "clase": "no_observable",
         "detalle": "la asignación aleatoria documentada apoya intercambiabilidad; el cumplimiento del protocolo no se verifica solo con el CSV"},
        {"nombre": "soporte_comun", "clase": "observable",
         "detalle": "ambos niveles de treat están presentes; la puerta diagnostica solapamiento observado"},
        {"nombre": "SUTVA", "clase": "no_observable",
         "detalle": "sin interferencia entre unidades y una sola versión del programa"},
        {"nombre": "efecto_homogeneo_PLR", "clase": "no_observable",
         "detalle": "solo para la estimación secundaria Double ML parcialmente lineal; no es requisito para la diferencia de medias"},
        {"nombre": "esparsidad_aproximada", "clase": "no_observable",
         "detalle": "supuesto de los learners Post-LASSO usados en la sensibilidad Double ML"},
    ],
}
print(ESPECIFICACION["estimando"], "|", len(ESPECIFICACION["supuestos"]), "supuestos declarados")
```

---

## Celda original 8 — Markdown

## 3. Estimación

La diferencia de medias es el estimador principal por el diseño aleatorizado; se reporta un IC de Welch. Como análisis ajustados secundarios se comparan post-LASSO y Double ML parcialmente lineal con cross-fitting. Los controles pretratamiento se incluyen como candidatos en las features. No hay verdad contrafactual para calcular error o cobertura sobre individuos.

---

## Celda original 9 — Python

```python
def construir_features(df):
    """Función pura: mismas columnas y mismo orden en entrenamiento y en servicio."""
    b = df[BASE].astype(float)
    X = b.assign(
        age2=b.age ** 2, educ2=b.educ ** 2,
        # log1p evita log(0), relevante porque muchos ingresos previos son cero en esta muestra.
        log_re74=np.log1p(b.re74), log_re75=np.log1p(b.re75),
        # Señala ausencia de ingresos previos: puede representar un régimen distinto a un ingreso bajo.
        cero74=(b.re74 == 0).astype(float), cero75=(b.re75 == 0).astype(float),
    )
    return X.assign(
        log74_log75=X.log_re74 * X.log_re75, black_educ=X.black * X.educ,
        nodeg_age=X.nodegree * X.age, black_nodeg=X.black * X.nodegree,
        educ_age=X.educ * X.age, re75_age=X.re75 * X.age / 1000, re75_educ=X.re75 * X.educ / 1000,
    )


X = construir_features(df)
y = df[RES].to_numpy(float)
d = df[TRAT].to_numpy(float)
FEATURES = list(X.columns)
len(FEATURES), FEATURES[:8]
```

---

## Celda original 10 — Python

```python
def ols_hc1(y, d, X):
    """OLS con errores estándar robustos HC1, vía statsmodels (antes: álgebra de sándwich manual)."""
    Z = sm.add_constant(np.column_stack([d, np.asarray(X, float)]))
    fit = sm.OLS(y, Z).fit(cov_type="HC1")
    ic = fit.conf_int(alpha=0.05)[1]
    return {"ate": float(fit.params[1]), "se": float(fit.bse[1]), "ic95": [float(ic[0]), float(ic[1])]}


def seleccionar(X, objetivo, alpha=None):
    # LASSO penaliza según escala; estandarizar evita favorecer variables solo por sus unidades.
    Xs = StandardScaler().fit_transform(np.asarray(X, float))
    m = LassoCV(cv=5, random_state=SEED, max_iter=20000) if alpha is None else Lasso(alpha=alpha, max_iter=20000)
    m.fit(Xs, objetivo)
    return np.abs(m.coef_) > 1e-10, float(getattr(m, "alpha_", alpha))


def con_base(mascara, columnas):
    """Fuerza a True las columnas del conjunto de ajuste declarado (antes: bucle explícito)."""
    return np.asarray(mascara) | np.isin(np.asarray(columnas), BASE)


class PostLasso(RegressorMixin, BaseEstimator):
    """Selecciona con LassoCV y reajusta con OLS sin regularizar (mismo principio que
    seleccionar()+OLS de la doble selección manual). Se usa como nuisance learner de
    doble_seleccion: LassoCV "plano" deja sesgo de encogimiento en g(X) y m(X) que la
    ortogonalización de Neyman no cancela del todo con covariables tan colineales como
    las de construir_features; la sensibilidad entre especificaciones ayuda a evaluar su estabilidad."""
    def __init__(self, cv=5, random_state=SEED, max_iter=20000):
        self.cv, self.random_state, self.max_iter = cv, random_state, max_iter

    def fit(self, X, y):
        # LASSO penaliza según escala; estandarizar evita favorecer variables solo por sus unidades.
        Xs = StandardScaler().fit_transform(np.asarray(X, float))
        sel = LassoCV(cv=self.cv, random_state=self.random_state, max_iter=self.max_iter).fit(Xs, y)
        mascara = np.abs(sel.coef_) > 1e-10
        self.mascara_ = mascara if mascara.any() else np.ones_like(mascara, dtype=bool)
        self.ols_ = LinearRegression().fit(np.asarray(X, float)[:, self.mascara_], y)
        return self

    def predict(self, X):
        return self.ols_.predict(np.asarray(X, float)[:, self.mascara_])


def doble_seleccion(X, y, d, n_folds=5, ml_l=None, ml_m=None):
    """Double ML parcialmente lineal (Chernozhukov et al. 2018) con cross-fitting y
    nuisance learners post-Lasso. Reemplaza la doble selección LASSO + OLS post-selección:
    el estimador es Neyman-ortogonal por construcción y, al usar PostLasso (no LassoCV
    "plano") para g(X) y m(X), conserva la propiedad clave del procedimiento manual —el
    refit final sin regularización— que es la que evita el sesgo de encogimiento. El
    supuesto 'efecto_homogeneo_PLR' ya declarado en la sección 2 es precisamente el
    supuesto de esta especificación parcialmente lineal."""
    ml_l = ml_l if ml_l is not None else PostLasso()
    ml_m = ml_m if ml_m is not None else PostLasso()
    datos = pd.concat([pd.Series(y, name=RES), pd.Series(d, name=TRAT),
                       X.reset_index(drop=True)], axis=1)
    dml_data = DoubleMLData(datos, y_col=RES, d_cols=TRAT, x_cols=list(X.columns))
    modelo = DoubleMLPLR(dml_data, ml_l=clone(ml_l), ml_m=clone(ml_m), n_folds=n_folds)
    modelo.fit()
    ic = modelo.confint(level=0.95).to_numpy()[0]
    return {"ate": float(modelo.coef[0]), "se": float(modelo.se[0]),
            "ic95": [float(ic[0]), float(ic[1])], "n_folds": n_folds}
```

---

## Celda original 11 — Python

```python
def t_learner_plugin(X, y, d):
    modelo = TLearner(models=RandomForestRegressor(n_estimators=300, min_samples_leaf=5,
                                                    random_state=SEED, n_jobs=-1))
    modelo.fit(y, d, X=np.asarray(X, float))
    return float(modelo.ate(np.asarray(X, float)))


def diferencia_medias_welch(y, d):
    tratados, controles = np.asarray(y)[np.asarray(d) == 1], np.asarray(y)[np.asarray(d) == 0]
    n1, n0 = len(tratados), len(controles)
    v1, v0 = np.var(tratados, ddof=1), np.var(controles, ddof=1)
    ate = float(np.mean(tratados) - np.mean(controles))
    se = float(np.sqrt(v1 / n1 + v0 / n0))
    grados_libertad = (v1 / n1 + v0 / n0) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v0 / n0) ** 2 / (n0 - 1)
    )
    # Cuantil t de Welch con grados de libertad ajustados; no supone varianzas iguales.
    margen = float(t_dist.ppf(0.975, grados_libertad) * se)
    return {"ate": ate, "se": se, "ic95": [ate - margen, ate + margen],
            "grados_libertad_welch": float(grados_libertad)}


ate_experimental = diferencia_medias_welch(y, d)
sel_y, _ = seleccionar(X, y)
ingenuo = ols_hc1(y, d, X.loc[:, con_base(sel_y, X.columns)])
doble = doble_seleccion(X, y, d)

comparacion = pd.DataFrame([
    {"procedimiento": "diferencia de medias (principal: asignación aleatoria)",
     "ate": ate_experimental["ate"], "se": ate_experimental["se"],
     "inferencia": "IC Welch; referencia experimental"},
    {"procedimiento": "T-learner plug-in con bosques (ajustado)",
     "ate": t_learner_plugin(X, y, d), "se": np.nan, "inferencia": "sin error estándar válido"},
    {"procedimiento": "post-LASSO (selección solo en Y)",
     "ate": ingenuo["ate"], "se": ingenuo["se"], "inferencia": "ajustado; inferencia post-selección"},
    {"procedimiento": "Double ML parcialmente lineal (ajustado)",
     "ate": doble["ate"], "se": doble["se"],
     "inferencia": f"cross-fitting, {doble['n_folds']} folds; efecto constante PLR"},
])
comparacion.round(1)
```

---

## Celda original 12 — Python

```python
VALIDACION = {
    "tipo": "comparación de estimadores en una muestra experimental real",
    "estimador_principal": "diferencia de medias con IC de Welch",
    "ate_referencia_muestral": ate_experimental["ate"],
    "ic95_referencia_muestral": ate_experimental["ic95"],
    "verdad_contrafactual_individual_disponible": False,
    "nota": "El valor de referencia es una estimación experimental con error de muestreo, no un ATE verdadero conocido. El CSV no contiene Y(0) y Y(1) para cada unidad.",
}
VALIDACION
```

---

## Celda original 13 — Python

```python
# Sensibilidad
filas = []
# Compara números de folds para comprobar la estabilidad del ATE ante esa elección.
for nf in (3, 5, 10):
    r = doble_seleccion(X, y, d, n_folds=nf)
    filas.append({"especificacion": f"PostLasso, {nf} folds", "ate": r["ate"], "se": r["se"]})
r_rf = doble_seleccion(X, y, d, n_folds=5,
                        ml_l=RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                                   random_state=SEED, n_jobs=-1),
                        ml_m=RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                                   random_state=SEED, n_jobs=-1))
filas.append({"especificacion": "Random Forest, 5 folds", "ate": r_rf["ate"], "se": r_rf["se"]})
sensibilidad = pd.DataFrame(filas)
sensibilidad.round(1)
```

---

## Celda original 14 — Python

```python
# Límites marginales p1–p99 usados como regla operativa de abstención; no describen el soporte conjunto.
SOPORTE = {c: [float(df[c].quantile(0.01)), float(df[c].quantile(0.99))] for c in BASE}
METADATA = {
    "modelo": "ate_rct_difference_in_means", "version": "3.0.0",
    "semilla_cv": SEED,
    "estimando": ESPECIFICACION["estimando"],
    "efecto": {k: ate_experimental[k] for k in ("ate", "se", "ic95")},
    "ajuste_doubleml_secundario": {k: doble[k] for k in ("ate", "se", "ic95", "n_folds")},
    "features": FEATURES, "conjunto_ajuste": BASE,
    "nuisance": {"ml_l": "PostLasso(cv=5)", "ml_m": "PostLasso(cv=5)", "n_folds": doble["n_folds"]},
    "soporte_p1_p99": SOPORTE, "datos": DATOS, "supuestos": ESPECIFICACION["supuestos"],
    "validacion": VALIDACION,
}
joblib.dump({"metadata": METADATA}, SALIDA / "modelo_ate.joblib")
(SALIDA / "metadata.json").write_text(json.dumps(METADATA, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"ATE experimental {ate_experimental['ate']:.1f} (EE {ate_experimental['se']:.1f}) "
      f"IC95 [{ate_experimental['ic95'][0]:.0f}, {ate_experimental['ic95'][1]:.0f}]")
print(f"Double ML ajustado {doble['ate']:.1f} (EE {doble['se']:.1f})")
```

---

## Celda original 15 — Markdown

## 4. Diagnóstico de soporte y puerta

El soporte común es el único supuesto observable de la sección 2. La puerta usa umbrales declarados y decide `pasa`/`alerta`/`falla`.

---

## Celda original 16 — Python

```python
UMBRALES = {"e_alerta": 0.05, "e_falla": 0.01, "ess_alerta": 0.50, "ess_falla": 0.20}


def propension(df, d):
    Xb = StandardScaler().fit_transform(df[BASE].to_numpy(float))
    return cross_val_predict(LogisticRegression(max_iter=2000), Xb, d.astype(int),
                             cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
                             method="predict_proba")[:, 1]


def puerta(e, d, umbrales=UMBRALES):
    # Pesos IPW para diagnosticar soporte; aquí no se usan para estimar el efecto.
    w = np.where(d == 1, 1 / e, 1 / (1 - e))
    met = {"e_min": float(e.min()), "e_max": float(e.max()),
           "ess_relativo": float(w.sum() ** 2 / (w ** 2).sum() / len(w)),
           # ESS de Kish normalizado por n; indica cuánto se reduce el tamaño efectivo por los pesos.
           "fuera_de_banda": float(np.mean((e < umbrales["e_alerta"]) | (e > 1 - umbrales["e_alerta"])))}
    cruza = lambda nivel: (met["e_min"] < umbrales[f"e_{nivel}"] or met["e_max"] > 1 - umbrales[f"e_{nivel}"]
                           or met["ess_relativo"] < umbrales[f"ess_{nivel}"])
    # Aplica la severidad en orden: primero falla, luego alerta y, si no, pasa.
    estado = "falla" if cruza("falla") else "alerta" if cruza("alerta") else "pasa"
    return {"estado": estado, "metricas": {k: round(v, 4) for k, v in met.items()}, "umbrales": umbrales}


# Propensity score fuera de muestra: cross_val_predict predice cada fila desde un fold no usado para ajustarla.
e = propension(df, d)
PUERTA = puerta(e, d)
(SALIDA / "puerta.json").write_text(json.dumps(PUERTA, indent=2, ensure_ascii=False), encoding="utf-8")
PUERTA
```

---

## Celda original 17 — Python

```python
# Reasigna el tratamiento a propósito para forzar una falla de la puerta; df y el análisis real no se modifican.
degradado = df.assign(**{TRAT: ((df.re75 == 0) | (df.nodegree == 1)).astype(int)})
d_deg = degradado[TRAT].to_numpy(float)
puerta(propension(degradado, d_deg), d_deg)
```

---

## Celda original 18 — Markdown

## 5. Servicio mínimo

`predict` reporta el ATE promedio de la cohorte experimental, no un efecto individual. Aplica el mismo `construir_features` y se abstiene para consultas fuera del soporte p1–p99 o si la puerta está en `falla`.

---

## Celda original 19 — Python

```python
def cargar_bundle(ruta=SALIDA / "modelo_ate.joblib", puerta_estado=None):
    b = joblib.load(ruta)
    estado = puerta_estado or PUERTA["estado"]
    # Bloquea el servicio entero en estado de falla, no se limita a emitir una alerta.
    if estado == "falla":
        raise RuntimeError("puerta en falla: la versión no se sirve")
    b["gate_status"] = estado
    return b


def predict(consulta, bundle):
    meta = bundle["metadata"]
    # Comprueba que la consulta incluya todas las covariables necesarias antes de procesarla.
    faltan = [c for c in meta["conjunto_ajuste"] if c not in consulta]
    if faltan:
        return {"abstiene": True, "motivo": f"faltan covariables: {faltan}"}
    fila = pd.DataFrame([{c: float(consulta[c]) for c in meta["conjunto_ajuste"]}])
    if list(construir_features(fila).columns) != meta["features"]:
        return {"abstiene": True, "motivo": "desalineación de features entre entrenamiento y servicio"}
    fuera = [f"{c}={consulta[c]:g} fuera de [{lo:g}, {hi:g}]"
             for c, (lo, hi) in meta["soporte_p1_p99"].items() if not lo <= float(consulta[c]) <= hi]
    base = {"estimando": meta["estimando"], "version": meta["version"], "gate_status": bundle["gate_status"]}
    if fuera:
        return {**base, "abstiene": True, "motivo": "; ".join(fuera)}
    return {**base, "abstiene": False, "efecto_promedio": meta["efecto"]["ate"],
            "ic95": meta["efecto"]["ic95"]}


bundle = cargar_bundle()
dentro = {"age": 32, "educ": 11, "black": 1, "hispan": 0, "married": 0,
          "nodegree": 1, "re74": 3500, "re75": 4100}
fuera = {**dentro, "re74": 95000}
predict(dentro, bundle), predict(fuera, bundle)
```

---

## Celda original 20 — Python

```python
try:
    cargar_bundle(puerta_estado="falla")
except RuntimeError as err:
    print("bloqueo:", err)
```

---

## Celda original 21 — Markdown

## 6. Model card mínima

Se genera desde `METADATA`: estimando, supuestos clasificados, evidencia y límites. Ningún campo se escribe a mano.

---

## Celda original 22 — Python

```python
EVIDENCIA = {
    "no_confusion_condicional": "asignación aleatoria documentada por el diseño; su cumplimiento no se verifica solo con el CSV",
    "soporte_comun": f"puerta {PUERTA['estado']}: e en [{PUERTA['metricas']['e_min']}, "
                     f"{PUERTA['metricas']['e_max']}], ESS {PUERTA['metricas']['ess_relativo']}",
    "SUTVA": "no verificable con estos datos; depende del diseño del programa",
    "efecto_homogeneo_PLR": "supuesto solo de la sensibilidad Double ML parcialmente lineal; el efecto servido es la diferencia de medias",
    "esparsidad_aproximada": f"supuesto de nuisance learners PostLasso sobre {len(FEATURES)} features derivadas",
}
MODEL_CARD = {
    "modelo": METADATA["modelo"], "version": METADATA["version"],
    "estimando": METADATA["estimando"], "poblacion": ESPECIFICACION["poblacion"],
    "metodo": ("Estimador principal: diferencia de medias de la muestra aleatorizada con IC de Welch. "
               f"Sensibilidad ajustada: Double ML parcialmente lineal con PostLasso y cross-fitting a "
               f"{METADATA['nuisance']['n_folds']} folds."),
    "efecto": METADATA["efecto"],
    "supuestos": [{**s, "evidencia": EVIDENCIA[s["nombre"]]} for s in METADATA["supuestos"]],
    "datos": METADATA["datos"],
    "puerta": PUERTA,
    "validacion": METADATA["validacion"],
    "limites": [
        "la estimación corresponde a la muestra experimental disponible; la validez externa a otras poblaciones es limitada",
        "solo se observa el resultado factual; no hay verdad contrafactual individual ni error/cobertura Monte Carlo",
        "el servicio comunica un ATE promedio, no efectos individuales (CATE)",
        "la sensibilidad Double ML parcialmente lineal impone un efecto constante",
        "el servicio se abstiene fuera del soporte p1–p99 y no sirve con la puerta en falla",
        "citar a Lalonde (1986) y Dehejia-Wahba; respetar las condiciones de atribución y uso no comercial de la fuente",
    ],
}
REQUERIDOS = ["modelo", "version", "estimando", "poblacion", "metodo", "efecto", "supuestos", "datos", "puerta", "limites"]
assert not [k for k in REQUERIDOS if k not in MODEL_CARD]
# Impide guardar la ficha si algún supuesto carece de clase admitida o de evidencia documentada.
assert all(s["clase"] in ("observable", "no_observable") and s["evidencia"] for s in MODEL_CARD["supuestos"])
(SALIDA / "model_card.json").write_text(json.dumps(MODEL_CARD, indent=2, ensure_ascii=False), encoding="utf-8")
pd.DataFrame(MODEL_CARD["supuestos"])[["nombre", "clase", "evidencia"]]
```

---

## Celda original 23 — Markdown

## 7. Cierre

---

## Celda original 24 — Python

```python
for p in sorted(SALIDA.iterdir()):
    print(f"{p.stat().st_size:>9,d}  {p.name}")
```

---

## Celda original 25 — Markdown

**Reproducción.** Desde `docencia`, ejecutar `jupyter nbconvert --to notebook --execute 05_06_notebook_causal_produccion.ipynb --inplace` (o ejecutar las celdas en orden). El CSV de entrada se busca en `../data_benchmark_causal/causal_benchmark_zoo/benchmarks/lalonde_nsw/processed/lalonde_nsw.csv`; los artefactos se guardan en `artefactos_notebook_causal_real/`.

**Relación con la rúbrica del trabajo final.**

| Criterio | Dónde | Artefacto |
|---|---|---|
| Pregunta causal + estimando + supuestos | §2 | `ESPECIFICACION`, `model_card.json` |
| Datos y transparencia | §1 | CSV real LaLonde/NSW, `DATOS` (hash, diseño, límites) |
| Estimación e inferencia | §3 | `comparacion`, `sensibilidad`, `metadata.json` |
| Servicio local y humo | §5 | `predict` con abstención y bloqueo por puerta |
| Puerta causal | §4 | `puerta.json` (umbrales declarados; `falla` bloquea) |
| Model card | §6 | `model_card.json` |

**Fuera de alcance.** Verdad contrafactual individual, CATE y política de asignación (Caps. 12-13 y 21-22), monitoreo longitudinal y registro de versiones con alias `champion`.
