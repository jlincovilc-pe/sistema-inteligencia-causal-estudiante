"""Contrato local de datos para los labs canónicos del curso.

Este módulo no genera datos. Resuelve el benchmark que vive en el monorepo,
normaliza sus formatos históricos y mantiene separados los frames observados
de los archivos de evaluación con ground truth.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

BENCH_REL = Path("data_benchmark_causal") / "causal_benchmark_synthetic" / "datasets"


@dataclass(frozen=True)
class ScenarioSpec:
    """Roles físicos y reglas mínimas de un escenario del curso."""

    treatment: str | None
    outcome: str | None
    covariates: tuple[str, ...] | None = None
    task: str = "inference"


SCENARIO_SPECS: dict[str, ScenarioSpec] = {
    "real/jobs": ScenarioSpec(
        treatment="treatment",
        outcome="re78",
        covariates=("age", "educ", "black", "hispan", "married", "nodegree", "re74", "re75"),
    ),
    "real/ihdp": ScenarioSpec(
        treatment="treatment",
        outcome="outcome",
        covariates=(
            "bw", "b.head", "preterm", "birth.o", "nnhealth", "momage",
            "sex", "twin", "b.marr", "mom.lths", "mom.hs", "mom.scoll",
            "cig", "first", "booze", "drugs", "work.dur", "prenatal",
            "ark", "ein", "har", "mia", "pen", "tex", "was",
        ),
    ),
    "synthetic/inference/ihdp_medium": ScenarioSpec(
        treatment="treatment",
        outcome="outcome",
        covariates=tuple(f"x{i}" for i in range(25)),
    ),
    "synthetic/edge_cases/latent_confounder": ScenarioSpec(
        treatment="X8",
        outcome="X9",
        covariates=tuple(f"X{i}" for i in range(1, 8)),
        task="non_identifiable",
    ),
    "synthetic/linear_gaussian/10_vars_10_edges": ScenarioSpec(
        treatment=None,
        outcome=None,
        covariates=tuple(f"X{i}" for i in range(10)),
        task="discovery",
    ),
}


class DataContractError(ValueError):
    """Error accionable de contrato de datos para un lab."""


def _candidate_roots() -> list[Path]:
    candidates: list[Path] = []
    for key in ("CAUSAL_DATA_ROOT", "LAB_BENCH_ROOT"):
        value = os.environ.get(key)
        if value:
            candidates.append(Path(value).expanduser())
    repo = os.environ.get("CAUSAL_REPO_ROOT")
    if repo:
        candidates.append(Path(repo).expanduser())
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        candidates.extend([start, *start.parents])
    return candidates


def _as_data_root(path: Path) -> Path:
    """Accept repo root, benchmark root or datasets root."""
    path = path.resolve()
    options = (
        path,
        path / "datasets",
        path / "causal_benchmark_synthetic" / "datasets",
        path / "data_benchmark_causal" / "causal_benchmark_synthetic" / "datasets",
    )
    for option in options:
        if (option / "real").is_dir() and (option / "synthetic").is_dir():
            return option.resolve()
    return path


def data_root(required: bool = True) -> Path | None:
    """Return the local benchmark datasets root.

    The normal path is inferred from the monorepo. A missing benchmark is an
    error unless the caller explicitly requests ``required=False``.
    """
    seen: set[Path] = set()
    for candidate in _candidate_roots():
        root = _as_data_root(candidate)
        if root in seen:
            continue
        seen.add(root)
        if (root / "real").is_dir() and (root / "synthetic").is_dir():
            return root
    if required:
        raise FileNotFoundError(
            "No se encontró el benchmark local. Ejecuta desde la raíz del "
            "repositorio o define CAUSAL_REPO_ROOT/CAUSAL_DATA_ROOT. "
            f"Ruta esperada: {BENCH_REL}"
        )
    return None


def scenario_path(name: str) -> Path:
    root = data_root()
    if root is None:
        raise FileNotFoundError("No se pudo resolver la raíz de datos del benchmark")
    key = str(name).strip().replace("\\", "/").strip("/")
    if not key or ".." in Path(key).parts:
        raise DataContractError(f"Nombre de escenario inválido: {name!r}")
    path = (root / key).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise DataContractError(f"El escenario escapa del benchmark: {name!r}") from exc
    if not path.is_dir():
        raise FileNotFoundError(f"No existe el escenario local: {path}")
    return path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DataContractError(f"Se esperaba un objeto JSON en {path}")
    return value


def _read_csv(path: Path, required: bool = True) -> pd.DataFrame | None:
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"Falta archivo requerido del benchmark: {path}")
        return None
    return pd.read_csv(path)


def _read_required_csv(path: Path) -> pd.DataFrame:
    frame = _read_csv(path, required=True)
    if frame is None:
        raise FileNotFoundError(f"Falta archivo requerido del benchmark: {path}")
    return frame


def _read_adj(path: Path) -> np.ndarray | None:
    """Read numeric or labelled adjacency matrices from the benchmark."""
    if not path.is_file():
        return None
    raw = pd.read_csv(path)
    # Legacy matrices have a first column with node labels and a header row.
    if raw.shape[1] == raw.shape[0] + 1:
        first = raw.columns[0]
        values = raw.drop(columns=[first])
    else:
        values = raw
    try:
        return values.to_numpy(float)
    except (TypeError, ValueError):
        # A headerless/labelled fallback; fail with useful context if still bad.
        values = pd.read_csv(path, index_col=0)
        try:
            return values.to_numpy(float)
        except (TypeError, ValueError) as exc:
            raise DataContractError(f"Matriz de adyacencia no numérica: {path}") from exc


def _spec_for(name: str, train: pd.DataFrame, meta: dict[str, Any]) -> ScenarioSpec:
    if name in SCENARIO_SPECS:
        return SCENARIO_SPECS[name]
    treatment = meta.get("treatment_var")
    outcome = meta.get("outcome_var")
    excluded = {"row_id", "id", "index", treatment, outcome}
    cov = tuple(c for c in train.columns if c not in excluded and not c.startswith("truth_"))
    return ScenarioSpec(treatment, outcome, cov, "inference" if treatment else "discovery")


def load_local_bundle(name: str) -> dict[str, Any]:
    """Load one scenario from the repository benchmark.

    Returned frames are observed-only. Truth/full data are returned separately
    so callers can make evaluation-only use explicit.
    """
    root = scenario_path(name)
    train = _read_required_csv(root / "observed_train.csv")
    validation = _read_required_csv(root / "observed_validation.csv")
    test = _read_required_csv(root / "observed_test.csv")
    meta = _read_json(root / "metadata.json")
    identification = _read_json(root / "identification.json")
    scorecard = _read_json(root / "scorecard.json")
    splits = _read_json(root / "splits.json")
    spec = _spec_for(name, train, meta)

    missing = [c for c in (spec.treatment, spec.outcome, *(spec.covariates or ())) if c and c not in train.columns]
    if missing:
        raise DataContractError(f"{name}: columnas ausentes en observed_train.csv: {missing}")
    truth = {}
    for key, filename in (("train", "truth_train.csv"), ("val", "truth_validation.csv"), ("test", "truth_test.csv")):
        frame = _read_csv(root / filename, required=False)
        if frame is not None:
            truth[key] = frame
    full = _read_csv(root / "data_full.csv", required=False)
    if full is None:
        full = _read_csv(root / "full.csv", required=False)
    adj = _read_adj(root / "graph_adjmatrix.csv")

    for split_name, frame in (("train", train), ("validation", validation), ("test", test)):
        forbidden = [c for c in frame.columns if c.startswith("truth_") or c.lower() in {"y0", "y1", "tau", "ite", "cate"}]
        if forbidden:
            raise DataContractError(f"{name}/{split_name}: truth mezclado con datos observados: {forbidden}")
    if spec.treatment and spec.task == "inference":
        values = train[spec.treatment].dropna().unique()
        if len(values) != 2:
            raise DataContractError(f"{name}: el tratamiento {spec.treatment} no es binario en train")
        if train[spec.outcome].nunique(dropna=True) <= 1:
            raise DataContractError(f"{name}: el outcome {spec.outcome} es constante en train")

    ate = next((meta.get(key) for key in ("ate_true", "true_ate", "ate_reference") if isinstance(meta.get(key), (int, float))), None)
    return {
        "name": name,
        "source": "benchmark",
        "root": root,
        "train": train,
        "val": validation,
        "test": test,
        "treatment": spec.treatment,
        "outcome": spec.outcome,
        "covariates": list(spec.covariates or ()),
        "task": spec.task,
        "meta": meta,
        "identification": identification,
        "scorecard": scorecard,
        "splits": splits,
        "truth": truth,
        "true_ate": float(ate) if ate is not None else None,
        "full": full,
        "adj": adj,
    }


def validate_all(required_scenarios: list[str] | None = None) -> list[dict[str, Any]]:
    """Validate the scenarios used by the migrated labs."""
    names = required_scenarios or list(SCENARIO_SPECS)
    reports = []
    for name in names:
        bundle = load_local_bundle(name)
        reports.append({
            "scenario": name,
            "source": bundle["source"],
            "rows": {k: len(bundle[k]) for k in ("train", "val", "test")},
            "treatment": bundle["treatment"],
            "outcome": bundle["outcome"],
            "covariates": len(bundle["covariates"]),
            "truth_splits": sorted(bundle["truth"]),
            "has_graph": bundle["adj"] is not None,
        })
    return reports
