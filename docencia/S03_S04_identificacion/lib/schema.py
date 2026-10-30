"""CausalSchema — operational bridge to monografía Cap. 4 design.

The monografía describes a typed role schema (treatment / outcome / covariates /
instruments). In the monorepo this is implemented on top of
:func:`lib.data_io.load_scenario` and inferred column roles — **CSV +
metadata.json**, not Parquet-by-default.

Example::

    from lib.schema import CausalSchema
    schema = CausalSchema.from_scenario("real/jobs")
    y, t, X = schema.ytx_scenario(split="train")
    print(schema.summary())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from .schema_estricto import CausalSchemaEstricto, ColumnasAusentes

from .data_io import (
    TREATMENT_COL,
    ScenarioBundle,
    infer_covariate_columns,
    infer_outcome_column,
    load_scenario,
)


@dataclass
class CausalSchema(CausalSchemaEstricto):
    """Explicit causal roles for a tabular scenario.

    Attributes
    ----------
    treatment:
        Treatment column name (default ``treatment``).
    outcome:
        Outcome column name (e.g. ``re78``, ``outcome``).
    covariates:
        Pre-treatment feature columns used as ``X``.
    instruments:
        Optional instrument column names (usually empty in course benchmarks).
    scenario:
        Relative scenario key when loaded from the monorepo.
    scenario_id:
        Canonical id when available.
    """

    treatment: str
    outcome: str
    covariates: List[str]
    instruments: List[str] = field(default_factory=list)
    scenario: Optional[str] = None
    scenario_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_frame(
        cls,
        df: pd.DataFrame,
        *,
        treatment: str = TREATMENT_COL,
        outcome: Optional[str] = None,
        covariates: Optional[Sequence[str]] = None,
        instruments: Optional[Sequence[str]] = None,
        scenario: Optional[str] = None,
        scenario_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "CausalSchema":
        """Build a schema from a DataFrame (infers roles if omitted)."""
        y = outcome if outcome is not None else infer_outcome_column(df)
        if treatment not in df.columns:
            raise ColumnasAusentes(f"Columnas requeridas ausentes: {treatment!r}")
        if y not in df.columns:
            raise ColumnasAusentes(f"Columnas requeridas ausentes: {y!r}")
        if covariates is None:
            x = infer_covariate_columns(df)
        else:
            x = list(covariates)
        inst = list(instruments or [])
        return cls(
            treatment=treatment,
            outcome=y,
            covariates=list(x),
            instruments=inst,
            scenario=scenario,
            scenario_id=scenario_id,
            meta=dict(meta or {}),
            post_treatment=list((meta or {}).get("post_treatment", [])),
            auxiliary_columns=["row_id"] if "row_id" in df.columns else [],
        )

    @classmethod
    def from_scenario(cls, scenario: str) -> "CausalSchema":
        """Load observed train split and infer roles (student-safe columns only)."""
        bundle = load_scenario(scenario)
        return cls.from_bundle(bundle)

    @classmethod
    def from_bundle(cls, bundle: ScenarioBundle) -> "CausalSchema":
        return cls.from_frame(
            bundle.train,
            treatment=bundle.treatment_column(),
            outcome=bundle.outcome_column(),
            covariates=bundle.covariate_columns(),
            scenario=bundle.scenario,
            scenario_id=bundle.scenario_id,
            meta=dict(bundle.meta or {}),
        )

    # ------------------------------------------------------------------
    # Validation / slicing
    # ------------------------------------------------------------------

    def validate(self, df: pd.DataFrame) -> None:
        """Aplica el contrato estricto compartido; conserva el API del repositorio."""
        return super().validate(df)

    def ytx(
        self, df: pd.DataFrame
    ) -> Tuple[pd.Series, pd.Series, pd.DataFrame]:
        """Return ``(Y, T, X)`` for ``df`` under this schema."""
        self.validate(df)
        return (
            df[self.outcome].copy(),
            df[self.treatment].copy(),
            df[list(self.covariates)].copy(),
        )

    def ytx_scenario(
        self, scenario: Optional[str] = None, split: str = "train"
    ) -> Tuple[pd.Series, pd.Series, pd.DataFrame]:
        """Load scenario split and return ``(Y, T, X)``."""
        key = scenario or self.scenario
        if not key:
            raise ValueError("scenario key required")
        bundle = load_scenario(key)
        df = bundle._split_frame(split)  # noqa: SLF001 — intentional reuse
        return self.ytx(df)

    def summary(self, df: Optional[pd.DataFrame] = None) -> str:
        """Human-readable role summary (and optional missingness if ``df`` given)."""
        lines = [
            f"CausalSchema(scenario={self.scenario!r}, id={self.scenario_id!r})",
            f"  treatment : {self.treatment}",
            f"  outcome   : {self.outcome}",
            f"  covariates: {len(self.covariates)} → {self.covariates[:8]}"
            + ("…" if len(self.covariates) > 8 else ""),
            f"  instruments: {self.instruments or '[]'}",
        ]
        if df is not None:
            self.validate(df)
            for role, cols in (
                ("treatment", [self.treatment]),
                ("outcome", [self.outcome]),
                ("covariates", self.covariates),
            ):
                for c in cols:
                    na = int(df[c].isna().sum())
                    lines.append(f"  [{role}] {c}: dtype={df[c].dtype}, n_missing={na}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()

    def feature_list(self) -> List[str]:
        """Alias for B1-style feature ordering."""
        return list(self.covariates)
