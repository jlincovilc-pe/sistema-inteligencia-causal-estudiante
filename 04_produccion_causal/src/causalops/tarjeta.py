"""Model card causal: se construye desde los resultados y se valida contra un JSON Schema.

La validación hace de "puerta de documentación": una card que no declara supuestos no observables
(con su sensibilidad y su criterio de revisión) no es válida y no puede promoverse.
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

from jsonschema import Draft202012Validator

ESQUEMA = Path(__file__).resolve().parents[2] / "esquemas" / "causal-model-card.local.schema.json"
LIBRERIAS = ("numpy", "scipy", "pandas", "scikit-learn", "jsonschema", "pydantic")


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def versiones_librerias() -> dict:
    out = {}
    for nombre in LIBRERIAS:
        try:
            out[nombre] = metadata.version(nombre)
        except metadata.PackageNotFoundError:
            out[nombre] = "no instalada"
    return out


def construir(
    *,
    nombre: str,
    version: str,
    fuente_datos: str,
    sha256_datos: str,
    resumen_estimacion: dict,
    resultado_puerta: dict,
    sensibilidad: dict,
    contraste_experimental: dict | None,
    commit: str | None = None,
) -> dict:
    ahora = _ahora()
    observables = [
        {
            "nombre": c["nombre"],
            "prueba": c["clave"],
            "valor": c["valor"],
            "umbral_alerta": c["umbral_alerta"],
            "umbral_falla": c["umbral_falla"],
            "estado": c["estado"],
            "verificado_en": ahora,
        }
        for c in resultado_puerta["chequeos"]
    ]
    ignorabilidad = {
        "nombre": "Ausencia de confusión no medida (ignorabilidad condicional)",
        "justificacion": (
            "No es comprobable con los datos observacionales. Se declara, se acota con análisis de "
            "sensibilidad y se contrasta, cuando existe, contra un holdout aleatorizado."
        ),
        "sensibilidad": {
            "metodo": "e_value_continuo_aproximado",
            "estado": "cuantificada",
            "objeto": "ATE puntual",
            "escala": "aproximacion_RR_desde_diferencia_estandarizada",
            "valor": float(sensibilidad["e_value"]["punto"]),
            "limitacion": "Aproximación docente; no sustituye una sensibilidad formal en la escala original.",
        },
        "criterio_revision": "Revisar si el control negativo rechaza o si el sesgo contra el holdout es distinto de cero.",
    }
    if contraste_experimental is not None:
        ignorabilidad["contraste_experimental"] = {
            "sesgo": float(contraste_experimental["sesgo"]),
            "ic95_sesgo": [float(v) for v in contraste_experimental["ic95_sesgo"]],
        }
    return {
        "schema_version": "local-0.2",
        "modelo": {"nombre": nombre, "version": version, "creado": ahora},
        "estimando": {
            "tipo": "ATE",
            "definicion": "Efecto promedio del tratamiento sobre el resultado en la población de los datos de entrenamiento.",
        },
        "datos": {"n": int(resumen_estimacion["n"]), "sha256": sha256_datos, "fuente": fuente_datos},
        "estimacion": {
            "metodo": resumen_estimacion["metodo"],
            "ate": resumen_estimacion["ate"],
            "se": resumen_estimacion["se"],
            "ic95": resumen_estimacion["ic95"],
            "k_folds": resumen_estimacion["k_folds"],
            "semilla": resumen_estimacion["semilla"],
        },
        "supuestos": {
            "observables": observables,
            "no_observables": [
                ignorabilidad,
                {
                    "nombre": "Validez externa: la población futura se parece a la de entrenamiento",
                    "justificacion": "No es comprobable con datos de entrenamiento; se vigila con drift de covariables y se limita con el soporte de las covariables.",
                    "sensibilidad": {
                        "metodo": "no_disponible_para_validez_externa",
                        "estado": "sin_cuantificacion_valida",
                        "limitacion": "El PSI y el soporte son señales de monitoreo; no cuantifican por sí solos la confusión ni la validez externa.",
                    },
                    "criterio_revision": "Revisar si el PSI máximo supera 0.25 o si el efecto re-estimado se aleja de la referencia.",
                },
            ],
        },
        "puerta": {"estado": resultado_puerta["estado"]},
        "limitaciones": [
            "Estimación válida solo dentro del soporte de las covariables de entrenamiento.",
            "Los umbrales de la puerta son convenciones de trabajo y deben recalibrarse por caso.",
        ],
        "uso_previsto": "Apoyar decisiones de priorización con efecto estimado e intervalo; no usar fuera de soporte.",
        "entorno": {"python": platform.python_version(), "librerias": versiones_librerias(), "commit": commit},
    }


def cargar_esquema() -> dict:
    return json.loads(ESQUEMA.read_text(encoding="utf-8"))


def errores(tarjeta: dict) -> list[str]:
    validador = Draft202012Validator(cargar_esquema())
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(raíz)'}: {e.message}" for e in validador.iter_errors(tarjeta)]


def validar(tarjeta: dict) -> None:
    fallos = errores(tarjeta)
    if fallos:
        raise ValueError("model card inválida:\n- " + "\n- ".join(fallos))
