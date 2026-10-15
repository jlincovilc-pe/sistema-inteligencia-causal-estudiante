"""Registro local mínimo y portátil: versiones inmutables, manifiesto con hashes y alias atómico.

No sustituye a MLflow: es el camino sin dependencias, útil para el CI y para entender qué hace un
registro. Con MLflow (infra/mlflow_adapter.py) la idea es la misma: versión + alias (`champion`),
no etapas.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from . import tarjeta as tarjeta_mod

ALIAS_POR_DEFECTO = "champion"


class PromocionRechazada(Exception):
    pass


def sha256_bytes(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def sha256_archivo(ruta: Path) -> str:
    return sha256_bytes(Path(ruta).read_bytes())


def commit_limpio(raiz_repo: Path | None = None) -> str | None:
    """Hash del commit actual si el árbol está limpio; None si no hay git o hay cambios sin confirmar."""
    try:
        cwd = str(raiz_repo) if raiz_repo else None
        cabeza = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10, cwd=cwd)
        estado = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10, cwd=cwd)
        if cabeza.returncode == 0 and estado.returncode == 0 and not estado.stdout.strip():
            return cabeza.stdout.strip()
    except Exception:
        pass
    return None


def _escribir_json(ruta: Path, obj: dict) -> None:
    ruta.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def siguiente_version(raiz: Path) -> str:
    existentes = [int(m.group(1)) for p in Path(raiz).glob("v*") if (m := re.fullmatch(r"v(\d{4})", p.name))]
    return f"v{(max(existentes) + 1 if existentes else 1):04d}"


def registrar_version(raiz: Path, estimacion: dict, tarjeta: dict, sha256_datos: str) -> str:
    """Valida la card y escribe estimacion.json, tarjeta.json y manifest.json en una carpeta nueva."""
    tarjeta_mod.validar(tarjeta)
    raiz = Path(raiz)
    raiz.mkdir(parents=True, exist_ok=True)
    version = siguiente_version(raiz)
    carpeta = raiz / version
    carpeta.mkdir()
    _escribir_json(carpeta / "estimacion.json", estimacion)
    _escribir_json(carpeta / "tarjeta.json", tarjeta)
    manifiesto = {
        "version": version,
        "dataset_sha256": sha256_datos,
        "archivos": {
            nombre: sha256_archivo(carpeta / nombre) for nombre in ("estimacion.json", "tarjeta.json")
        },
        "puerta": tarjeta["puerta"]["estado"],
        "commit": tarjeta["entorno"].get("commit"),
    }
    _escribir_json(carpeta / "manifest.json", manifiesto)
    return version


def verificar_integridad(raiz: Path, version: str) -> bool:
    carpeta = Path(raiz) / version
    manifiesto = json.loads((carpeta / "manifest.json").read_text(encoding="utf-8"))
    return all(sha256_archivo(carpeta / n) == h for n, h in manifiesto["archivos"].items())


def promover(raiz: Path, version: str, alias: str = ALIAS_POR_DEFECTO, aceptar_alerta: bool = False) -> None:
    """Apunta el alias a la versión. "falla" nunca se promueve; "alerta" exige aceptarla explícitamente."""
    raiz = Path(raiz)
    carpeta = raiz / version
    if not carpeta.is_dir():
        raise PromocionRechazada(f"no existe {version}")
    if not verificar_integridad(raiz, version):
        raise PromocionRechazada(f"{version}: los archivos no coinciden con su manifiesto")
    estado = json.loads((carpeta / "manifest.json").read_text(encoding="utf-8"))["puerta"]
    if estado == "falla":
        raise PromocionRechazada(f"{version}: la puerta causal falló; no se promueve")
    if estado == "alerta" and not aceptar_alerta:
        raise PromocionRechazada(f"{version}: la puerta quedó en alerta; exige aceptar_alerta=True")
    destino = raiz / f"alias_{alias}.json"
    fd, tmp = tempfile.mkstemp(dir=raiz, prefix=".alias_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"alias": alias, "version": version, "puerta": estado}, f)
        os.replace(tmp, destino)  # atómico en el mismo sistema de archivos
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def cargar_alias(raiz: Path, alias: str = ALIAS_POR_DEFECTO) -> dict:
    """Devuelve estimacion + tarjeta + version de la versión a la que apunta el alias."""
    raiz = Path(raiz)
    ptr = json.loads((raiz / f"alias_{alias}.json").read_text(encoding="utf-8"))
    carpeta = raiz / ptr["version"]
    return {
        "version": ptr["version"],
        "estimacion": json.loads((carpeta / "estimacion.json").read_text(encoding="utf-8")),
        "tarjeta": json.loads((carpeta / "tarjeta.json").read_text(encoding="utf-8")),
    }
