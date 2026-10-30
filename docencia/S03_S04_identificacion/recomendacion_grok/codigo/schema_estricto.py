"""
Schema estricto de roles para sistemas causales.
Detecta los fallos que el CausalSchema actual del repo deja pasar.
Uso: from schema_estricto import CausalSchemaEstricto
"""
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class CausalSchemaEstricto:
    treatment: str
    outcome: str
    covariates: list[str] = field(default_factory=list)
    instruments: list[str] = field(default_factory=list)
    post_treatment: list[str] = field(default_factory=list)  # explícitamente prohibidas
    scenario_id: Optional[str] = None

    def validate(self, df: pd.DataFrame) -> None:
        """Rechaza los cuatro fallos del plan + covariable posterior."""
        cols = set(df.columns)

        # Fallo 1: columna renombrada en el origen
        required = {self.treatment, self.outcome, *self.covariates, *self.instruments}
        missing = required - cols
        if missing:
            raise ValueError(f"Columnas requeridas ausentes: {missing}")

        # Fallo 2: tratamiento constante tras un filtro
        if df[self.treatment].nunique() < 2:
            raise ValueError("Tratamiento constante: no hay variación para identificar")

        # Fallo 3: instrumento también entre covariables (doble rol)
        dual = set(self.instruments) & set(self.covariates)
        if dual:
            raise ValueError(f"Columna con doble rol (instrumento y covariable): {dual}")

        # Fallo 4: esquema desincronizado (columnas extra no declaradas que parecen post)
        declared = required | set(self.post_treatment)
        undeclared = cols - declared - {self.treatment, self.outcome}
        # Solo alerta si hay columnas no declaradas; el contrato fuerte las rechaza
        if undeclared:
            raise ValueError(f"Columnas no declaradas en el esquema: {undeclared}")

        # Invariante (7): covariable posterior al tratamiento
        post_in_cov = set(self.post_treatment) & set(self.covariates)
        if post_in_cov:
            raise ValueError(
                f"Covariable posterior al tratamiento declarada como pre: {post_in_cov}. "
                "El contrato no puede verificar causalidad, pero rechaza la declaración explícita de post."
            )

    def summary(self) -> dict:
        return {
            "treatment": self.treatment,
            "outcome": self.outcome,
            "covariates": self.covariates,
            "instruments": self.instruments,
            "post_treatment": self.post_treatment,
        }
