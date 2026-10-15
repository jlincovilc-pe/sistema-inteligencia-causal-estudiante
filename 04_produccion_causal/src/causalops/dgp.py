"""Generador de datos sintéticos con verdad conocida.

Sirve para tres cosas: (1) comprobar que el estimador recupera el efecto verdadero,
(2) inyectar violaciones de supuestos y ver si los diagnósticos las detectan, y
(3) simular semanas de producción con drift.

Estructura:
  X ~ N(0, I)            covariables observadas (x1 puede desplazarse: drift)
  U ~ N(0, 1)            confusor NO observado (fuerza = gamma_u)
  T ~ Bernoulli(e)       tratamiento; logit(e) depende de x0, x1, x2 y U
  Y = mu(X) + tau(X) T + gamma_u U + ruido        tau(x) = ate + het * x0
  NC = 0.7 x0 + 0.5 x1 + gamma_u U + ruido        control negativo: T no lo afecta
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def _sigmoide(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


@dataclass(frozen=True)
class Escenario:
    ate: float = 1.0           # efecto promedio verdadero (E[x0] = 0)
    het: float = 0.5           # pendiente de tau(x) en x0 (heterogeneidad)
    gamma_u: float = 0.0       # fuerza del confusor no observado; 0 = ignorabilidad se cumple
    positividad: float = 0.0   # 0 = solapamiento sano; 1 = casi determinista a lo largo de x2
    drift_x1: float = 0.0      # desplazamiento de la media de x1 (covariate shift)
    sigma: float = 1.0         # desvío del ruido
    p: int = 5                 # número de covariables


def generar(
    n: int,
    esc: Escenario = Escenario(),
    semilla: int = 0,
    fraccion_holdout: float = 0.0,
) -> pd.DataFrame:
    """Devuelve un DataFrame con x0..x{p-1}, t, y, nc, holdout y las columnas de verdad.

    `fraccion_holdout` > 0 marca esa parte de las unidades como asignadas al azar
    (tratamiento ~ Bernoulli(0.5), independiente de X y de U): es el holdout aleatorizado.
    Las columnas `tau_verdadero`, `e_verdadero` y `u` son solo para evaluar: no son covariables.
    """
    rng = np.random.default_rng(semilla)
    X = rng.normal(size=(n, esc.p))
    X[:, 1] += esc.drift_x1
    U = rng.normal(size=n)

    logit = 0.8 * X[:, 0] - 0.5 * X[:, 1] + esc.gamma_u * U + 3.0 * esc.positividad * X[:, 2]
    e = _sigmoide(logit)
    h = rng.random(n) < fraccion_holdout
    t = np.where(h, rng.random(n) < 0.5, rng.random(n) < e).astype(int)

    mu = X[:, 0] + 0.5 * X[:, 1] ** 2 + 0.3 * X[:, 3]
    tau = esc.ate + esc.het * X[:, 0]
    y = mu + tau * t + esc.gamma_u * U + esc.sigma * rng.normal(size=n)
    nc = 0.7 * X[:, 0] + 0.5 * X[:, 1] + esc.gamma_u * U + esc.sigma * rng.normal(size=n)

    df = pd.DataFrame(X, columns=[f"x{j}" for j in range(esc.p)])
    df["t"] = t
    df["y"] = y
    df["nc"] = nc
    df["holdout"] = h.astype(int)
    df["tau_verdadero"] = tau
    df["e_verdadero"] = e
    df["u"] = U
    return df


def columnas_x(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("x") and c[1:].isdigit()]
