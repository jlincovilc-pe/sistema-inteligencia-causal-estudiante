"""lab_assumptions — versiones de referencia de las métricas de supuestos.
Impleméntalas primero tú en el lab que corresponda; después reutiliza estas."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats


def e_value(rr: float) -> float:
    """E-value de VanderWeele y Ding (2017) para una razón de riesgos RR (o su inverso si RR<1)."""
    rr = float(rr)
    if rr < 1:
        rr = 1 / rr
    return rr + np.sqrt(rr * (rr - 1))


def rr_from_d(d: float) -> float:
    """Aproximación RR ≈ exp(0,91·d) para un resultado continuo con diferencia estandarizada d."""
    return float(np.exp(0.91 * d))


def ess_relative(w) -> float:
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / (w ** 2).sum() / len(w))


def smd(x, t, w=None) -> float:
    x = np.asarray(x, float); t = np.asarray(t)
    w = np.ones(len(x)) if w is None else np.asarray(w, float)
    m1 = np.average(x[t == 1], weights=w[t == 1]); m0 = np.average(x[t == 0], weights=w[t == 0])
    v1 = np.average((x[t == 1] - m1) ** 2, weights=w[t == 1]); v0 = np.average((x[t == 0] - m0) ** 2, weights=w[t == 0])
    s = np.sqrt((v1 + v0) / 2)
    return float((m1 - m0) / s) if s > 0 else 0.0


def asmd(a, b) -> float:
    a = np.asarray(a, float); b = np.asarray(b, float)
    s = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float(abs(a.mean() - b.mean()) / s) if s > 0 else 0.0


def psi(a, b, bins: int = 10) -> float:
    """Population Stability Index con bins definidos por cuantiles de la muestra de referencia `a`."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    edges = np.unique(np.quantile(a, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    p = np.histogram(a, edges)[0] / len(a); q = np.histogram(b, edges)[0] / len(b)
    p, q = np.clip(p, 1e-6, None), np.clip(q, 1e-6, None)
    return float(((p - q) * np.log(p / q)).sum())


def ks_stat(a, b) -> float:
    return float(stats.ks_2samp(a, b).statistic)


def ks_null_threshold(n_ref, n_win, k_covs=3, q=0.99, reps=400, seed=0) -> float:
    """Cuantil q del máximo de KS bajo la nula (misma distribución) para k covariables."""
    rng = np.random.default_rng(seed)
    mx = [max(ks_stat(rng.normal(size=n_ref), rng.normal(size=n_win)) for _ in range(k_covs)) for _ in range(reps)]
    return float(np.quantile(mx, q))


def estabilidad_efecto(theta_ref, se_ref, theta_rec, se_rec, alpha=0.05):
    """Test z de dos estimaciones independientes (ec. 30.105 del libro)."""
    z = (theta_rec - theta_ref) / np.sqrt(se_rec ** 2 + se_ref ** 2)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return {"z": float(z), "p": float(p), "alerta": bool(p < alpha)}


def auc_score(y, s):
    y = np.asarray(y); s = np.asarray(s, float)
    r = stats.rankdata(s)
    n1 = (y == 1).sum(); n0 = (y == 0).sum()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def drift_asignacion(model_ref, X_rec, t_rec, X_ref, t_ref):
    """Puntúa el propensity de REFERENCIA en la ventana reciente (versión recomendada).
    Devuelve AUC en referencia, AUC en ventana y su diferencia."""
    a_ref = auc_score(t_ref, model_ref.predict_proba(X_ref)[:, 1])
    a_rec = auc_score(t_rec, model_ref.predict_proba(X_rec)[:, 1])
    return {"auc_ref": a_ref, "auc_rec": a_rec, "delta": a_rec - a_ref}
