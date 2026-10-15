"""Sensibilidad a confusión no medida: se ACOTA, no se testea.

- E-value (VanderWeele y Ding, 2017): fuerza mínima de asociación (en escala de razón de riesgos)
  que un confusor no medido necesitaría con tratamiento y resultado para anular el efecto.
  Para un resultado continuo se usa la aproximación RR ~ exp(0.91 d), con d = efecto / sd(Y).
- Valor de robustez RV_q (Cinelli y Hazlett, 2020, versión lineal): parte de la varianza residual
  de T y de Y que un confusor tendría que explicar para reducir el efecto en una fracción q.
  Aquí se aplica de forma aproximada sobre el estadístico t del ATE doblemente robusto.

Referencias de trabajo: VanderWeele y Ding (E-value); Cinelli y Hazlett (valor de robustez).
"""

from __future__ import annotations

import math

from .estimador import Z95


def e_value_rr(rr: float) -> float:
    """E-value de una razón de riesgos (VanderWeele y Ding, 2017)."""
    if rr <= 0:
        raise ValueError("rr debe ser positivo")
    rr = max(rr, 1.0 / rr)
    return rr + math.sqrt(rr * (rr - 1.0))


def e_value_continuo(ate: float, se: float, sd_y: float) -> dict:
    """E-value para el estimador puntual y para el extremo del IC más cercano al cero."""
    d = ate / sd_y
    punto = e_value_rr(math.exp(0.91 * abs(d)))
    extremo = (abs(ate) - Z95 * se) / sd_y
    if extremo <= 0:
        ic = 1.0  # el IC incluye al cero: nada que explicar
    else:
        ic = e_value_rr(math.exp(0.91 * extremo))
    return {"punto": punto, "ic": ic, "d_estandarizado": d}


def robustez_rv(t_stat: float, dof: int, q: float = 1.0) -> float:
    """RV_q = (sqrt(f^4 + 4 f^2) - f^2) / 2, con f = q * |t| / sqrt(dof)."""
    f = q * abs(t_stat) / math.sqrt(dof)
    return 0.5 * (math.sqrt(f**4 + 4 * f**2) - f**2)


def resumen_sensibilidad(ate: float, se: float, n: int, sd_y: float) -> dict:
    return {
        "e_value": e_value_continuo(ate, se, sd_y),
        "rv_anular": robustez_rv(ate / se, n - 1, q=1.0),
        "nota": "Aproximaciones sobre el ATE doblemente robusto; no sustituyen un análisis de sensibilidad formal.",
    }
