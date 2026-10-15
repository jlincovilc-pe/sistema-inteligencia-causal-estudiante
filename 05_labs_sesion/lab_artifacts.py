"""Contratos mínimos para artefactos compartidos por los labs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LABS_ROOT = Path(__file__).resolve().parent
ARTIFACTS_ROOT = LABS_ROOT / "artefactos"

REQUIRED_A2_FIELDS = {
    "version", "scenario", "origen_datos", "estimando", "metodo", "theta", "se",
    "ic95", "n_train", "covariables", "soporte", "hash_datos_entrenamiento", "semilla",
}


def artifact_path(name: str) -> Path:
    """Resolve an artifact only below ``05_labs_sesion/artefactos``."""
    key = str(name).strip().replace("\\", "/").lstrip("/")
    path = (ARTIFACTS_ROOT / key).resolve()
    try:
        path.relative_to(ARTIFACTS_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"Ruta de artefacto fuera de artefactos/: {name!r}") from exc
    return path


def save_json(name: str, value: dict[str, Any]) -> Path:
    path = artifact_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_json(name: str) -> dict[str, Any]:
    path = artifact_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el artefacto local: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"El artefacto no es un objeto JSON: {path}")
    return value


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def validate_a2(value: dict[str, Any]) -> list[str]:
    """Return actionable contract errors for an A2 estimator artifact."""
    errors = [f"falta {key}" for key in sorted(REQUIRED_A2_FIELDS - set(value))]
    if value.get("origen_datos") != "benchmark":
        errors.append("origen_datos debe ser 'benchmark' en la edición local")
    if not isinstance(value.get("covariables"), list) or not value.get("covariables"):
        errors.append("covariables debe ser una lista no vacía")
    interval = value.get("ic95")
    if not isinstance(interval, list) or len(interval) != 2:
        errors.append("ic95 debe contener [inferior, superior]")
    return errors
