"""Kernel-less policy API for tests/autograder (no UI framework required)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

import numpy as np
from runtime import PolicyBundle, load_bundle

B3_ROOT = Path(__file__).resolve().parent
REPO = B3_ROOT.parents[1]
SERIE_A = REPO / "03_notebooks_caso_estudio"
if str(SERIE_A) not in sys.path:
    sys.path.insert(0, str(SERIE_A))

ARTIFACTS = Path(os.environ.get("B3_ARTIFACTS_DIR", B3_ROOT / "artifacts"))


def _uncertainty(bundle: Optional[PolicyBundle] = None) -> dict[str, str]:
    """Return the uncertainty object without treating a ranking score as an interval."""
    if bundle is not None:
        card_uncertainty = bundle.card.get("incertidumbre")
        if isinstance(card_uncertainty, dict):
            return dict(card_uncertainty)
    return {
        "estado": "sin_cuantificacion_valida",
        "objeto": "valor_de_politica",
        "limitacion": (
            "Este bundle sirve una regla top-k y no porta una muestra de evaluación "
            "para calcular un intervalo del valor de la política; uplift_score es "
            "un score de ranking, no una medida de incertidumbre."
        ),
    }


def load_policy(path: Optional[Path] = None):
    # Some pytest/plugin environments preload a top-level module named ``lib``.
    # Remove that non-package so the monorepo's ``lib.policy_utils`` wins.
    loaded_lib = sys.modules.get("lib")
    if loaded_lib is not None and not hasattr(loaded_lib, "__path__"):
        del sys.modules["lib"]
    from lib.policy_utils import load_policy as _load

    p = Path(path) if path is not None else ARTIFACTS / "policy.joblib"
    return _load(p)


def predict_rows(
    policy,
    rows: Union[Mapping[str, float], Sequence[Mapping[str, float]], np.ndarray],
    bundle: Optional[PolicyBundle] = None,
) -> Dict[str, Any]:
    names = list(policy.feature_names or [])
    if isinstance(rows, np.ndarray):
        X = np.asarray(rows, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
    elif isinstance(rows, Mapping):
        X = np.asarray([[float(rows[n]) for n in names]], dtype=float)
    else:
        X = np.asarray([[float(r[n]) for n in names] for r in rows], dtype=float)
    if bundle is not None:
        row_dict = {name: float(X[0, i]) for i, name in enumerate(names)} if len(X) == 1 else None
        reasons = bundle.outside_support(row_dict) if row_dict is not None else []
        if reasons:
            return {
                "estimando": "valor_de_politica",
                "estimand": "policy_value",
                "incertidumbre": _uncertainty(bundle),
                "decision": np.asarray([], dtype=int),
                "uplift_score": np.asarray([], dtype=float),
                "threshold": float(policy.threshold),
                "budget_fraction": float(policy.budget_fraction),
                "version": bundle.version,
                "gate_status": bundle.gate_status,
                "abstiene": True,
                "motivo": "; ".join(reasons),
            }
    out = policy.predict(X=X)
    result = {
        "estimando": "valor_de_politica",
        "estimand": "policy_value",
        "incertidumbre": _uncertainty(bundle),
        "decision": np.asarray(out["decision"], dtype=int).reshape(-1),
        "uplift_score": np.asarray(out["uplift_score"], dtype=float).reshape(-1),
        "threshold": float(policy.threshold),
        "budget_fraction": float(policy.budget_fraction),
        "abstiene": False,
        "motivo": None,
    }
    if bundle is not None:
        result.update({"version": bundle.version, "gate_status": bundle.gate_status})
    return result


def load_runtime_policy():
    """Load policy plus its manifest, support and promotion state."""
    return load_policy(), load_bundle(ARTIFACTS)


def smoke_three_cases(policy) -> List[Dict[str, Any]]:
    """Three fixed cases for humo (zeros, ones, mixed)."""
    names = list(policy.feature_names or [])
    p = len(names)
    cases = [
        np.zeros(p),
        np.ones(p),
        np.linspace(-1.0, 1.0, p),
    ]
    results = []
    for i, x in enumerate(cases):
        out = predict_rows(policy, x.reshape(1, -1))
        results.append(
            {
                "case": i,
                "decision": int(out["decision"][0]),
                "uplift_score": float(out["uplift_score"][0]),
            }
        )
    return results
