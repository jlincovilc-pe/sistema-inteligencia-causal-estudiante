"""Flujo de punta a punta: datos -> estimación -> diagnósticos -> puerta -> model card -> registro -> alias.

Es el equivalente causal del recorrido de `curso.py` del ejemplo v1, pero cada paso comprueba algo del efecto
y de sus supuestos, no solo que "el servicio responde".
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import diagnosticos as dg
from . import puerta, registro_local, servicio_core, tarjeta
from .dgp import Escenario, columnas_x, generar
from .estimador import ajustar_irm
from .falsificacion import control_negativo
from .holdout import sesgo_vs_experimento
from .sensibilidad import resumen_sensibilidad

ESCENARIOS = {
    "sano": Escenario(),
    "confusor": Escenario(gamma_u=1.0),
    "positividad": Escenario(positividad=0.8),
}
COLUMNAS_GUARDADAS = ("t", "y", "nc", "holdout")


def ejecutar_escenario(
    nombre: str,
    raiz_artefactos: Path,
    dir_datos: Path,
    n: int = 4000,
    semilla: int = 0,
    fraccion_holdout: float = 0.10,
    aceptar_alerta: bool = False,
) -> dict:
    """Corre el flujo para un escenario del DGP y devuelve un informe con lo que pasó en cada paso."""
    esc = ESCENARIOS[nombre]
    raiz_artefactos, dir_datos = Path(raiz_artefactos), Path(dir_datos)
    dir_datos.mkdir(parents=True, exist_ok=True)

    # 1. Datos: se guardan SIN las columnas de verdad y se identifican por su hash.
    df = generar(n, esc, semilla=semilla, fraccion_holdout=fraccion_holdout)
    cols = columnas_x(df)
    ruta_csv = dir_datos / f"entrenamiento_{nombre}.csv"
    df[cols + list(COLUMNAS_GUARDADAS)].to_csv(ruta_csv, index=False)
    sha = registro_local.sha256_archivo(ruta_csv)

    # 2. Estimación sobre la parte observacional; el holdout aleatorizado se reserva para contrastar.
    obs, h = df[df["holdout"] == 0], df[df["holdout"] == 1]
    X, t, y = obs[cols].to_numpy(), obs["t"].to_numpy(), obs["y"].to_numpy()
    r = ajustar_irm(X, t, y, columnas=cols, semilla=semilla)

    # 3. Supuestos observables y falsificables -> puerta causal.
    nc = control_negativo(X, t, obs["nc"].to_numpy(), semilla=semilla)
    diag = {
        "frac_ps_extremo": dg.frac_ps_extremo(r.e_hat),
        "ess_rel_min": dg.ess_relativo(r.e_hat, t),
        "smd_pond_max": dg.smd_max(X, t, r.e_hat),
        "nc_abs_z": abs(nc["z"]),
    }
    informativo = {"calib_ps_z": dg.calibracion_ps_z(r.e_hat, t)}
    resultado_puerta = puerta.evaluar(diag)

    # 4. Supuestos no observables: se acotan (sensibilidad) y se contrastan (holdout aleatorizado).
    sens = resumen_sensibilidad(r.ate, r.se, r.n, float(np.std(y)))
    sesgo = sesgo_vs_experimento(r.ate, r.se, h["t"].to_numpy(), h["y"].to_numpy())

    # 5. Model card validada, registro versionado y promoción condicionada a la puerta.
    card = tarjeta.construir(
        nombre="efecto-demo",
        version="pendiente",
        fuente_datos=f"sintético: escenario '{nombre}' (DGP con verdad conocida)",
        sha256_datos=sha,
        resumen_estimacion=r.a_dict(),
        resultado_puerta=resultado_puerta,
        sensibilidad=sens,
        contraste_experimental=sesgo,
        commit=registro_local.commit_limpio(),
    )
    version = registro_local.registrar_version(raiz_artefactos, r.a_dict(), card, sha)
    promovida, motivo = False, ""
    try:
        registro_local.promover(raiz_artefactos, version, aceptar_alerta=aceptar_alerta)
        promovida = True
    except registro_local.PromocionRechazada as exc:
        motivo = str(exc)

    return {
        "escenario": nombre,
        "version": version,
        "ate": r.ate,
        "ic95": list(r.ic95),
        "ate_verdadero": esc.ate,
        "ic_cubre_la_verdad": r.ic95[0] <= esc.ate <= r.ic95[1],
        "puerta": resultado_puerta["estado"],
        "chequeos": resultado_puerta["chequeos"],
        "informativo": informativo,
        "control_negativo_z": nc["z"],
        "e_value_punto": sens["e_value"]["punto"],
        "rv_anular": sens["rv_anular"],
        "sesgo_vs_holdout": {"sesgo": sesgo["sesgo"], "ic95": sesgo["ic95_sesgo"], "distinto_de_cero": bool(sesgo["distinto_de_cero"])},
        "promovida": promovida,
        "motivo_no_promovida": motivo,
        "sha256_datos": sha,
    }


def demo_completa(raiz_artefactos: Path, dir_datos: Path, n: int = 4000, semilla: int = 0) -> tuple[dict, list[dict]]:
    """Corre los tres escenarios en orden y comprueba el resultado esperado de cada uno.

    Esperado: `sano` se promueve; `positividad` y `confusor` quedan registrados pero BLOQUEADOS por la puerta,
    y el alias `champion` sigue apuntando a la versión sana. Devuelve (informe, casos) con una fila PASA/FALLA por caso.
    """
    raiz_artefactos = Path(raiz_artefactos)
    informes = {nombre: ejecutar_escenario(nombre, raiz_artefactos, dir_datos, n=n, semilla=semilla) for nombre in ("sano", "positividad", "confusor")}
    alias = registro_local.cargar_alias(raiz_artefactos)

    # Consulta al "servicio" sobre la versión vigente: dentro y fuera de soporte.
    dentro = servicio_core.consultar(alias, [0.0] * len(alias["estimacion"]["columnas"]))
    fuera = servicio_core.consultar(alias, [9.0] + [0.0] * (len(alias["estimacion"]["columnas"]) - 1))
    s, p, c = informes["sano"], informes["positividad"], informes["confusor"]

    casos = []

    def caso(nombre, ok, detalle):
        casos.append({"caso": nombre, "estado": "PASA" if ok else "FALLA", "detalle": detalle})

    caso("sano: ic cubre la verdad", s["ic_cubre_la_verdad"], f"ate={s['ate']:.3f} ic=({s['ic95'][0]:.2f}, {s['ic95'][1]:.2f}) verdad={s['ate_verdadero']}")
    caso("sano: puerta pasa y se promueve", s["puerta"] == "pasa" and s["promovida"], f"puerta={s['puerta']} version={s['version']}")
    caso("sano: holdout no halla sesgo", not s["sesgo_vs_holdout"]["distinto_de_cero"], f"sesgo={s['sesgo_vs_holdout']['sesgo']:.3f}")
    caso("positividad: la puerta falla y se bloquea", p["puerta"] == "falla" and not p["promovida"], f"puerta={p['puerta']} ({p['motivo_no_promovida']})")
    caso("confusor oculto: los diagnosticos observables pasan", all(ch["estado"] == "pasa" for ch in c["chequeos"] if ch["clave"] != "nc_abs_z"), "balance y solapamiento no lo ven")
    caso("confusor oculto: el control negativo lo delata", c["control_negativo_z"] > 5, f"z={c['control_negativo_z']:.1f}")
    caso("confusor oculto: el holdout mide el sesgo", c["sesgo_vs_holdout"]["distinto_de_cero"], f"sesgo={c['sesgo_vs_holdout']['sesgo']:.2f}")
    caso("confusor oculto: se bloquea", c["puerta"] == "falla" and not c["promovida"], f"puerta={c['puerta']}")
    caso("el alias sigue en la version sana", alias["version"] == s["version"], f"champion={alias['version']}")
    caso("servicio: efecto con intervalo dentro del soporte", not dentro["abstiene"] and dentro["ic95"] is not None, f"cate={dentro['cate']:.3f}")
    caso("servicio: se abstiene fuera del soporte", fuera["abstiene"], fuera["motivo"] or "")
    return {"informes": informes, "alias": alias["version"]}, casos


def escribir_informe(informe: dict, casos: list[dict], destino: Path) -> str:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "informe.json").write_text(json.dumps({"casos": casos, **informe}, indent=2, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    lineas = [f"{c['estado']:6s} {c['caso']:55s} {c['detalle']}" for c in casos]
    texto = "\n".join(lineas) + "\n"
    (destino / "informe.txt").write_text(texto, encoding="utf-8")
    return texto
