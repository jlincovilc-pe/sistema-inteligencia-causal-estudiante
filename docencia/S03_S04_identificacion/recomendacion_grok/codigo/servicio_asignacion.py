"""
Servicio mínimo de asignación a programa de capacitación.
Se abstiene cuando la consulta está fuera del soporte común.
Demo para sesión 2 (plan B o reemplazo de llamada a B1).
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


@dataclass
class ServicioAsignacion:
    esquema: object  # CausalSchemaEstricto
    modelo_ps: LogisticRegression
    soporte_lo: float
    soporte_hi: float
    ate: float
    supuestos: list[str]

    def predict(self, x: pd.DataFrame) -> dict:
        self.esquema.validate(x)  # rechaza esquema inválido antes de responder
        ps = self.modelo_ps.predict_proba(x[self.esquema.covariates])[:, 1]
        fuera = (ps < self.soporte_lo) | (ps > self.soporte_hi)
        if fuera.any():
            return {
                "abstiene": True,
                "motivo": f"overlap: propensity {ps[fuera][0]:.3f} fuera de [{self.soporte_lo:.3f}, {self.soporte_hi:.3f}]",
                "ate": None,
            }
        return {
            "abstiene": False,
            "ate": self.ate,
            "supuestos": self.supuestos,
            "ps": float(ps[0]),
        }

    def metadata(self) -> dict:
        return {
            "ate": self.ate,
            "supuestos": self.supuestos,
            "soporte": [self.soporte_lo, self.soporte_hi],
            "esquema": self.esquema.summary(),
        }
