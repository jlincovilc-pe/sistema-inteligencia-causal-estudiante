"""Falsificación: pruebas con consecuencias observables si el supuesto vale.

Control negativo de resultado: una variable que, por conocimiento del dominio, el tratamiento NO
afecta. Si tras ajustar por X el "efecto" sobre ella es distinto de cero, algo falla: confusión
no medida, fuga de información o mal ajuste.

Límite que conviene decir en voz alta: NO rechazar no prueba que el supuesto valga (la prueba
puede tener poca potencia, o el confusor oculto puede no afectar al control negativo).
"""

from __future__ import annotations

import numpy as np

from .estimador import Z95, ajustar_irm


def control_negativo(X: np.ndarray, t: np.ndarray, nc: np.ndarray, **kw) -> dict:
    """Estima el efecto de t sobre el control negativo con el mismo estimador que el efecto principal."""
    r = ajustar_irm(X, t, nc, **kw)
    z = r.ate / r.se
    return {
        "efecto_nc": float(r.ate),
        "se": float(r.se),
        "ic95": [float(r.ate - Z95 * r.se), float(r.ate + Z95 * r.se)],
        "z": float(z),
        "p_aprox": float(2 * (1 - _cdf_normal(abs(z)))),
    }


def _cdf_normal(x: float) -> float:
    from scipy.stats import norm

    return float(norm.cdf(x))
