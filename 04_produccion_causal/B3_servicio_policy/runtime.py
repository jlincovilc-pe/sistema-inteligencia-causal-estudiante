"""Versioned policy bundle and support checks for the local service."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PolicyBundle:
    version: str
    alias: str
    gate_status: str
    support: dict[str, tuple[float, float]]
    card: dict[str, Any]
    manifest: dict[str, Any]

    def outside_support(self, row: dict[str, float]) -> list[str]:
        return [
            f"{name}={value:g} fuera de [{lo:g}, {hi:g}]"
            for name, value in row.items()
            for lo, hi in [self.support.get(name, (-float("inf"), float("inf")))]
            if value < lo or value > hi
        ]


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Falta {path.name}; ejecute build_runtime_bundles.py")
    return json.loads(path.read_text(encoding="utf-8"))


def load_bundle(root: Path) -> PolicyBundle:
    root = Path(root)
    manifest = _read(root / "manifest.json")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
        if actual != expected:
            raise ValueError(f"Hash inválido o archivo ausente: {name}")
    support_data = _read(root / "support.json")
    support = {name: (float(v[0]), float(v[1])) for name, v in support_data["features"].items()}
    version = _read(root / "version.json")
    card = _read(root / "policy_card.json")
    if version.get("gate_status") == "falla":
        raise ValueError("La policy no puede servirse: la puerta causal está en falla")
    return PolicyBundle(
        version=str(version["version"]),
        alias=str(version.get("alias", "champion")),
        gate_status=str(version.get("gate_status", "falla")),
        support=support,
        card=card,
        manifest=manifest,
    )
