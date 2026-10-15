"""Lógica de consulta del servicio, sin dependencia de FastAPI (así se prueba en cualquier entorno).

A diferencia del ejemplo v1 (que devolvía una etiqueta y copiaba un campo `do` sin usarlo), aquí la
respuesta es el EFECTO con su incertidumbre, o una ABSTENCIÓN explícita fuera del soporte.
"""

from __future__ import annotations

import math

import numpy as np
from pydantic import BaseModel, Field

from .estimador import Z95


class Consulta(BaseModel):
    x: list[float] = Field(..., min_length=1, description="Covariables, en el orden de `columnas`.")


def consultar(bundle: dict, x: list[float]) -> dict:
    est = bundle["estimacion"]
    cols = est["columnas"]
    if len(x) != len(cols):
        raise ValueError(f"se esperaban {len(cols)} covariables ({', '.join(cols)}) y llegaron {len(x)}")
    if any(not math.isfinite(v) for v in x):
        raise ValueError("las covariables deben ser números finitos")

    base = {
        "version": bundle["version"],
        "estado_puerta": bundle["tarjeta"]["puerta"]["estado"],
    }
    fuera = [
        c for c, v in zip(cols, x) if v < est["soporte"][c][0] or v > est["soporte"][c][1]
    ]
    if fuera:
        return {
            **base,
            "cate": None,
            "ic95": None,
            "abstiene": True,
            "motivo": f"fuera del soporte de entrenamiento (p1-p99) en: {', '.join(fuera)}",
        }

    z = np.concatenate([[1.0], np.asarray(x, dtype=float)])
    beta = np.asarray(est["cate_lineal"]["beta"])
    cov = np.asarray(est["cate_lineal"]["beta_cov"])
    cate = float(z @ beta)
    se = float(math.sqrt(max(z @ cov @ z, 0.0)))
    out = {
        **base,
        "cate": cate,
        "ic95": [cate - Z95 * se, cate + Z95 * se],
        "abstiene": False,
        "motivo": None,
    }
    if base["estado_puerta"] == "alerta":
        out["advertencia"] = "La puerta causal de esta versión quedó en alerta; interpretar con cautela."
    return out
