"""Holdout aleatorizado permanente: la única vía de contraste directo para lo no observable.

Una fracción pequeña del tráfico recibe el tratamiento al azar. Con ella se estima el efecto
SIN depender de ignorabilidad, y se compara con la estimación observacional. La diferencia es una
estimación del sesgo por confusión no medida (en la población del holdout).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm

from .estimador import Z95


def efecto_experimental(t: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Diferencia de medias y su error estándar en el holdout aleatorizado."""
    t = np.asarray(t)
    y = np.asarray(y, dtype=float)
    y1, y0 = y[t == 1], y[t == 0]
    return float(y1.mean() - y0.mean()), float(math.sqrt(y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0)))


def sesgo_vs_experimento(ate_obs: float, se_obs: float, t_h: np.ndarray, y_h: np.ndarray) -> dict:
    """Sesgo = ATE observacional - ATE experimental. Supone muestras independientes."""
    ate_exp, se_exp = efecto_experimental(t_h, y_h)
    sesgo = ate_obs - ate_exp
    se = math.sqrt(se_obs**2 + se_exp**2)
    z = sesgo / se
    return {
        "ate_experimental": ate_exp,
        "se_experimental": se_exp,
        "sesgo": sesgo,
        "se_sesgo": se,
        "ic95_sesgo": [sesgo - Z95 * se, sesgo + Z95 * se],
        "z": z,
        "distinto_de_cero": abs(z) > Z95,
    }


def n_holdout_para_sesgo(delta: float, sigma: float, alpha: float = 0.05, potencia: float = 0.8) -> int:
    """Tamaño total del holdout (asignación 50/50) para detectar un sesgo de tamaño `delta`.

    n = 4 sigma^2 (z_{1-alpha/2} + z_{potencia})^2 / delta^2. Ignora la incertidumbre de la
    estimación observacional, así que es una cota inferior.
    """
    z = norm.ppf(1 - alpha / 2) + norm.ppf(potencia)
    return int(math.ceil(4 * sigma**2 * z**2 / delta**2))
