"""Diagnósticos de supuestos OBSERVABLES: se miden directamente en los datos.

Los umbrales por defecto (puerta.py) son convenciones de trabajo, no teoremas:
hay que recalibrarlos para cada caso.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def frac_ps_extremo(e_hat: np.ndarray, eps: float = 0.05) -> float:
    """Proporción de unidades con propensity fuera de [eps, 1-eps] (indicio de violar positividad)."""
    e_hat = np.asarray(e_hat)
    return float(np.mean((e_hat < eps) | (e_hat > 1 - eps)))


def ess_relativo(e_hat: np.ndarray, t: np.ndarray) -> float:
    """Tamaño efectivo de muestra de los pesos IPW, relativo al tamaño del brazo; mínimo de los dos brazos.

    Vale 1 si los pesos son iguales y cae hacia 0 cuando pocas unidades dominan la estimación.
    """
    e_hat = np.asarray(e_hat)
    t = np.asarray(t)
    valores = []
    for brazo, w in ((1, 1.0 / e_hat), (0, 1.0 / (1.0 - e_hat))):
        w = w[t == brazo]
        valores.append(float(w.sum() ** 2 / (w**2).sum() / len(w)))
    return min(valores)


def smd_max(X: np.ndarray, t: np.ndarray, e_hat: np.ndarray | None = None) -> float:
    """Máxima diferencia estandarizada de medias entre tratados y controles.

    Con `e_hat` los brazos se ponderan por IPW: así se comprueba el balance que logra el ajuste.
    """
    X = np.asarray(X, dtype=float)
    t = np.asarray(t)
    if e_hat is None:
        w1 = np.ones((t == 1).sum())
        w0 = np.ones((t == 0).sum())
    else:
        e_hat = np.asarray(e_hat)
        w1 = 1.0 / e_hat[t == 1]
        w0 = 1.0 / (1.0 - e_hat[t == 0])
    X1, X0 = X[t == 1], X[t == 0]
    m1 = (w1[:, None] * X1).sum(0) / w1.sum()
    m0 = (w0[:, None] * X0).sum(0) / w0.sum()
    sd = np.sqrt((X1.var(0, ddof=1) + X0.var(0, ddof=1)) / 2.0)
    return float(np.max(np.abs(m1 - m0) / np.where(sd > 0, sd, 1.0)))


def calibracion_ps(e_hat: np.ndarray, t: np.ndarray, bins: int = 10, minimo: int = 30) -> float:
    """Brecha máxima entre propensity predicho y frecuencia observada de tratamiento, por deciles."""
    e_hat = np.asarray(e_hat)
    t = np.asarray(t)
    cortes = np.quantile(e_hat, np.linspace(0, 1, bins + 1)[1:-1])
    celda = np.searchsorted(cortes, e_hat, side="right")
    brechas = [
        abs(t[celda == c].mean() - e_hat[celda == c].mean())
        for c in range(bins)
        if (celda == c).sum() >= minimo
    ]
    return float(max(brechas)) if brechas else float("nan")


def calibracion_ps_z(e_hat: np.ndarray, t: np.ndarray, bins: int = 10, minimo: int = 30) -> float:
    """Brecha de calibración del propensity ESTANDARIZADA por su error muestral (máximo sobre bins).

    Por bin: |frecuencia de tratamiento - propensity medio| / sqrt(p (1 - p) / m), con m unidades en el bin.
    A diferencia de la brecha cruda, no depende del tamaño de la ventana: con bins de ~150 unidades
    el ruido puro de la brecha ya es ~0.04, y un umbral fijo de 0.10 daba falsas alarmas.
    """
    e_hat = np.asarray(e_hat)
    t = np.asarray(t)
    cortes = np.quantile(e_hat, np.linspace(0, 1, bins + 1)[1:-1])
    celda = np.searchsorted(cortes, e_hat, side="right")
    zs = []
    for c in range(bins):
        m = int((celda == c).sum())
        if m < minimo:
            continue
        p = float(e_hat[celda == c].mean())
        se = float(np.sqrt(max(p * (1 - p), 1e-3) / m))
        zs.append(abs(float(t[celda == c].mean()) - p) / se)
    return float(max(zs)) if zs else float("nan")


def psi_drift(ref: np.ndarray, nuevo: np.ndarray, bins: int = 10, eps: float = 1e-4) -> float:
    """Population Stability Index de una covariable (cortes por cuantiles de la referencia).

    Convención habitual: < 0.1 estable, 0.1-0.25 cambio moderado, > 0.25 cambio grande.
    Es una convención de la práctica (origen: scoring de crédito), no un test con p-valor.
    """
    ref = np.asarray(ref, dtype=float)
    nuevo = np.asarray(nuevo, dtype=float)
    cortes = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)[1:-1]))
    pr = np.bincount(np.searchsorted(cortes, ref, side="right"), minlength=len(cortes) + 1) / len(ref)
    pn = np.bincount(np.searchsorted(cortes, nuevo, side="right"), minlength=len(cortes) + 1) / len(nuevo)
    pr = np.clip(pr, eps, None)
    pn = np.clip(pn, eps, None)
    return float(np.sum((pn - pr) * np.log(pn / pr)))


def ks_drift(ref: np.ndarray, nuevo: np.ndarray) -> tuple[float, float]:
    """Estadístico y p-valor de Kolmogorov-Smirnov de dos muestras."""
    res = stats.ks_2samp(np.asarray(ref, dtype=float), np.asarray(nuevo, dtype=float))
    return float(res.statistic), float(res.pvalue)


def drift_covariables(ref: np.ndarray, nuevo: np.ndarray, columnas: list[str]) -> dict:
    """PSI y KS por covariable, más el PSI máximo."""
    por_col = {}
    for j, c in enumerate(columnas):
        ks, p = ks_drift(ref[:, j], nuevo[:, j])
        por_col[c] = {"psi": psi_drift(ref[:, j], nuevo[:, j]), "ks": ks, "ks_p": p}
    return {"por_covariable": por_col, "psi_max": max(v["psi"] for v in por_col.values())}
