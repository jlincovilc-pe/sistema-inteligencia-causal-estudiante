"""Estimador doblemente robusto con cross-fitting (AIPW/IRM) y CATE lineal (DR-learner).

- ATE: media de la función de influencia psi, con error estándar sd(psi)/sqrt(n).
- CATE lineal: regresión MCO del pseudo-resultado psi sobre (1, x). Es serializable a JSON
  (coeficientes y covarianza), así que el servicio no necesita cargar un pickle.
- Las predicciones de los modelos auxiliares son siempre fuera de muestra (cross-fitting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.model_selection import KFold

Z95 = 1.959963984540054


def regresor_por_defecto(semilla: int):
    return HistGradientBoostingRegressor(max_iter=80, random_state=semilla)


def clasificador_por_defecto(semilla: int):
    # Regularizado a propósito: con los valores por defecto de HistGradientBoosting el propensity se
    # sobreajusta (pesos extremos y mal calibrados) y los diagnósticos de solapamiento salen falsamente
    # malos incluso con datos sanos. El propensity verdadero del DGP deja SMD y ESS dentro de umbral.
    return HistGradientBoostingClassifier(
        max_iter=100,
        learning_rate=0.05,
        min_samples_leaf=50,
        l2_regularization=1.0,
        max_leaf_nodes=8,
        random_state=semilla,
    )


@dataclass
class ResultadoIRM:
    ate: float
    se: float
    psi: np.ndarray = field(repr=False)
    e_hat: np.ndarray = field(repr=False)
    mu0: np.ndarray = field(repr=False)
    mu1: np.ndarray = field(repr=False)
    beta: np.ndarray = field(repr=False)        # coeficientes del CATE lineal: [intercepto, x0, x1, ...]
    beta_cov: np.ndarray = field(repr=False)    # covarianza robusta (HC0) de beta
    soporte: dict = field(repr=False)           # percentiles 1 y 99 de cada covariable
    n: int = 0
    k: int = 5
    semilla: int = 0
    recorte: float = 0.01
    columnas: list = field(default_factory=list)

    @property
    def ic95(self) -> tuple[float, float]:
        return (self.ate - Z95 * self.se, self.ate + Z95 * self.se)

    def a_dict(self) -> dict:
        """Resumen serializable a JSON (sin los vectores por unidad)."""
        lo, hi = self.ic95
        return {
            "estimando": "ATE",
            "metodo": "AIPW con cross-fitting (IRM) + DR-learner lineal",
            "ate": float(self.ate),
            "se": float(self.se),
            "ic95": [float(lo), float(hi)],
            "n": int(self.n),
            "k_folds": int(self.k),
            "semilla": int(self.semilla),
            "recorte_ps": float(self.recorte),
            "columnas": list(self.columnas),
            "cate_lineal": {
                "beta": [float(b) for b in self.beta],
                "beta_cov": [[float(v) for v in fila] for fila in self.beta_cov],
            },
            "soporte": self.soporte,
        }


def ajustar_irm(
    X: np.ndarray,
    t: np.ndarray,
    y: np.ndarray,
    columnas: list[str] | None = None,
    k: int = 5,
    semilla: int = 0,
    recorte: float = 0.01,
    fabrica_regresor: Callable[[int], object] = regresor_por_defecto,
    fabrica_clasificador: Callable[[int], object] = clasificador_por_defecto,
) -> ResultadoIRM:
    X = np.asarray(X, dtype=float)
    t = np.asarray(t, dtype=int)
    y = np.asarray(y, dtype=float)
    n = len(y)
    if X.shape[0] != n or t.shape[0] != n:
        raise ValueError("X, t e y deben tener el mismo número de filas")
    if set(np.unique(t)) - {0, 1}:
        raise ValueError("t debe ser binario (0/1)")
    if t.sum() < 20 or (1 - t).sum() < 20:
        raise ValueError("hacen falta al menos 20 unidades tratadas y 20 de control")

    mu0 = np.zeros(n)
    mu1 = np.zeros(n)
    e = np.zeros(n)
    for i, (tr, te) in enumerate(KFold(k, shuffle=True, random_state=semilla).split(X)):
        tr1 = tr[t[tr] == 1]
        tr0 = tr[t[tr] == 0]
        mu1[te] = fabrica_regresor(semilla + i).fit(X[tr1], y[tr1]).predict(X[te])
        mu0[te] = fabrica_regresor(semilla + i).fit(X[tr0], y[tr0]).predict(X[te])
        e[te] = fabrica_clasificador(semilla + i).fit(X[tr], t[tr]).predict_proba(X[te])[:, 1]
    e = np.clip(e, recorte, 1 - recorte)

    psi = mu1 - mu0 + t * (y - mu1) / e - (1 - t) * (y - mu0) / (1 - e)
    ate = float(psi.mean())
    se = float(psi.std(ddof=1) / np.sqrt(n))

    Z = np.column_stack([np.ones(n), X])
    ZtZ_inv = np.linalg.inv(Z.T @ Z)
    beta = ZtZ_inv @ Z.T @ psi
    resid = psi - Z @ beta
    beta_cov = ZtZ_inv @ (Z.T * resid**2) @ Z @ ZtZ_inv

    cols = columnas or [f"x{j}" for j in range(X.shape[1])]
    soporte = {
        c: [float(np.quantile(X[:, j], 0.01)), float(np.quantile(X[:, j], 0.99))]
        for j, c in enumerate(cols)
    }
    return ResultadoIRM(
        ate=ate, se=se, psi=psi, e_hat=e, mu0=mu0, mu1=mu1, beta=beta, beta_cov=beta_cov,
        soporte=soporte, n=n, k=k, semilla=semilla, recorte=recorte, columnas=cols,
    )
