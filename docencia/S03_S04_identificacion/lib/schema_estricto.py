"""Contrato compartido de roles, derivado del paquete de recomendaciones S03/S04.

La información temporal debe declararse: el contrato no descubre causalidad.
Entrenamiento valida Y/D/X; inferencia valida únicamente las covariables.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
import numpy as np
import pandas as pd


class ColumnasAusentes(ValueError, KeyError):
    """ValueError de contrato compatible con los consumidores históricos KeyError."""


@dataclass
class CausalSchemaEstricto:
    treatment: str
    outcome: str
    covariates: list[str] = field(default_factory=list)
    instruments: list[str] = field(default_factory=list)
    post_treatment: list[str] = field(default_factory=list)
    scenario_id: Optional[str] = None
    auxiliary_columns: list[str] = field(default_factory=list)

    def __post_init__(self):
        for name in ("covariates", "instruments", "post_treatment", "auxiliary_columns"):
            setattr(self, name, list(getattr(self, name)))

    def validate_roles(self):
        roles = [self.treatment, self.outcome, *self.covariates, *self.instruments]
        if not self.covariates:
            raise ValueError("Falta el conjunto de covariables")
        if any(not isinstance(col, str) or not col for col in roles):
            raise ValueError("Los roles deben ser nombres de columna no vacíos")
        repetidas = sorted({col for col in roles if roles.count(col) > 1})
        if repetidas:
            raise ValueError(f"Columna con doble rol: {repetidas}")
        posteriores = set(self.post_treatment) & set(self.covariates)
        if posteriores:
            raise ValueError(f"Covariable posterior al tratamiento declarada como pre: {sorted(posteriores)}")
        if set(self.auxiliary_columns) & set(roles):
            raise ValueError("Una columna auxiliar no puede tener un rol de modelo")
        from .data_io import TRUTH_COLS
        verdad = set(roles) & set(TRUTH_COLS)
        if verdad:
            raise ValueError(f"Columnas de verdad causal prohibidas: {sorted(verdad)}")
        return roles

    def _columns(self, df, required, allowed):
        if not isinstance(df, pd.DataFrame) or df.columns.has_duplicates:
            raise ValueError("Se requiere una tabla con nombres de columna únicos")
        missing = set(required) - set(df.columns)
        if missing:
            raise ColumnasAusentes(f"Columnas requeridas ausentes: {sorted(missing)}")
        undeclared = set(df.columns) - set(allowed)
        if undeclared:
            raise ValueError(f"Columnas no declaradas en el esquema: {sorted(undeclared)}")

    def validate(self, df):
        roles = self.validate_roles()
        self._columns(df, roles, [*roles, *self.post_treatment, *self.auxiliary_columns])
        if df[[self.treatment, self.outcome]].isna().any().any():
            raise ValueError("Tratamiento o resultado con valores ausentes")
        if df[self.treatment].nunique() < 2:
            raise ValueError(f"Tratamiento constante: {self.treatment}")
        return True

    def validate_features(self, x):
        """Una persona nueva no tiene Y ni necesita variación de D en su consulta."""
        self.validate_roles()
        self._columns(x, self.covariates, [*self.covariates, *self.auxiliary_columns])
        if x.empty:
            raise ValueError("La consulta no puede estar vacía")
        try:
            values = x[self.covariates].to_numpy(dtype=float)
        except (ValueError, TypeError) as error:
            raise ValueError("Las covariables de consulta deben ser numéricas") from error
        if not np.isfinite(values).all():
            raise ValueError("Las covariables de consulta deben ser finitas y sin ausentes")
        return True

    def ytx(self, df):
        self.validate(df)
        return df[self.outcome].copy(), df[self.treatment].copy(), df[list(self.covariates)].copy()

    def X(self, df):
        return self.ytx(df)[2].to_numpy(float)

    def D(self, df):
        return self.ytx(df)[1].to_numpy(float)

    def Y(self, df):
        return self.ytx(df)[0].to_numpy(float)

    def summary(self):
        return self.to_dict()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        return cls(**value)
