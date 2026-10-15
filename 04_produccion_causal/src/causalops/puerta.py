"""Puerta causal: decide si un estimador puede promoverse, a partir de supuestos OBSERVABLES.

Estados: "pasa" < "alerta" < "falla". El estado global es el peor de los chequeos.
Los umbrales son convenciones de trabajo; recalíbralos por caso y regístralos en la model card.

La calibración del propensity (diagnosticos.calibracion_ps_z) se calcula y se informa, pero NO entra en la
regla de decisión: con ventanas de ~1500 unidades un propensity regularizado queda levemente mal calibrado
sin que eso invalide el efecto, y como puerta producía falsas alarmas. Lo que sí decide es el balance
ponderado (SMD), que mide directamente si los pesos equilibran las covariables.
"""

from __future__ import annotations

from dataclasses import dataclass

ORDEN = {"pasa": 0, "alerta": 1, "falla": 2}


@dataclass(frozen=True)
class Umbral:
    nombre: str
    clave: str
    alerta: float          # valor a partir del cual se pasa a "alerta"
    falla: float           # valor a partir del cual se pasa a "falla"
    mayor_es_peor: bool = True
    origen: str = "convención de trabajo"


UMBRALES_POR_DEFECTO = (
    Umbral("Propensity extremo (fuera de [0.05, 0.95])", "frac_ps_extremo", 0.05, 0.10),
    Umbral("Tamaño efectivo relativo (mínimo de brazos)", "ess_rel_min", 0.30, 0.15, mayor_es_peor=False),
    Umbral("SMD máximo ponderado", "smd_pond_max", 0.10, 0.25, origen="convención de balance (SMD < 0.1)"),
    Umbral("Control negativo |z|", "nc_abs_z", 3.0, 5.0, origen="z = 3 por comparaciones repetidas en el tiempo"),
)


def _estado(valor: float, u: Umbral) -> str:
    if valor != valor:  # NaN
        return "alerta"
    v = valor if u.mayor_es_peor else -valor
    a = u.alerta if u.mayor_es_peor else -u.alerta
    f = u.falla if u.mayor_es_peor else -u.falla
    if v >= f:
        return "falla"
    if v >= a:
        return "alerta"
    return "pasa"


def evaluar(diagnosticos: dict, umbrales=UMBRALES_POR_DEFECTO) -> dict:
    """Evalúa los diagnósticos presentes (los ausentes se omiten) y devuelve el estado global."""
    chequeos = []
    for u in umbrales:
        if u.clave not in diagnosticos:
            continue
        valor = float(diagnosticos[u.clave])
        chequeos.append(
            {
                "nombre": u.nombre,
                "clave": u.clave,
                "valor": valor,
                "umbral_alerta": u.alerta,
                "umbral_falla": u.falla,
                "estado": _estado(valor, u),
                "origen_umbral": u.origen,
            }
        )
    estado = max((c["estado"] for c in chequeos), key=ORDEN.get, default="pasa")
    return {"estado": estado, "chequeos": chequeos}
