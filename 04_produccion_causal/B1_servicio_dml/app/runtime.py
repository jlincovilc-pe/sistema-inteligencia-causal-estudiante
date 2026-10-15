"""Runtime contract for versioned causal artifacts.

The service refuses to treat an artifact bundle as production-ready unless its
manifest hashes, support limits and promotion metadata are available.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeBundle:
    version: str
    alias: str
    gate_status: str
    support: dict[str, tuple[float, float]]
    manifest: dict[str, Any]
    card: dict[str, Any]

    def outside_support(self, rows: list[list[float]], feature_names: list[str]) -> list[str]:
        reasons: list[str] = []
        for row_number, row in enumerate(rows):
            for name, value in zip(feature_names, row):
                lo, hi = self.support.get(name, (-float("inf"), float("inf")))
                if value < lo or value > hi:
                    reasons.append(f"fila {row_number}: {name}={value:g} fuera de [{lo:g}, {hi:g}]")
        return reasons


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Falta el artefacto de producción: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Se esperaba un objeto JSON en {path}")
    return value


def load_runtime(artifacts_dir: Path) -> RuntimeBundle:
    root = Path(artifacts_dir)
    manifest = _read_json(root / "manifest.json")
    for filename, expected in manifest.get("files", {}).items():
        path = root / filename
        if not path.is_file() or _sha256(path) != expected:
            raise ValueError(f"Hash inválido o archivo ausente en el manifiesto: {filename}")
    support_raw = _read_json(root / "support.json")
    support = {
        str(name): (float(bounds[0]), float(bounds[1]))
        for name, bounds in support_raw.get("features", {}).items()
    }
    version = _read_json(root / "version.json")
    card = _read_json(root / "model_card.json")
    gate_status = str(version.get("gate_status", card.get("puerta", {}).get("estado", "falla")))
    if gate_status == "falla":
        raise ValueError("La versión tiene la puerta causal en falla y no puede ser servida")
    return RuntimeBundle(
        version=str(version.get("version", "desconocida")),
        alias=str(version.get("alias", "champion")),
        gate_status=gate_status,
        support=support,
        manifest=manifest,
        card=card,
    )
