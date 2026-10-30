"""
Tests de los fallos que el esquema actual deja pasar.
Ejecutar después de aplicar schema_estricto.py.
"""
import pandas as pd
import pytest
from schema_estricto import CausalSchemaEstricto


def test_columna_renombrada():
    df = pd.DataFrame({"trat": [0, 1], "y": [1, 2], "x": [0.1, 0.2]})
    esq = CausalSchemaEstricto(treatment="D", outcome="Y", covariates=["x"])
    with pytest.raises(ValueError, match="ausentes"):
        esq.validate(df)


def test_tratamiento_constante():
    df = pd.DataFrame({"D": [1, 1], "Y": [1, 2], "x": [0.1, 0.2]})
    esq = CausalSchemaEstricto(treatment="D", outcome="Y", covariates=["x"])
    with pytest.raises(ValueError, match="constante"):
        esq.validate(df)


def test_instrumento_duplicado():
    df = pd.DataFrame({"D": [0, 1], "Y": [1, 2], "z": [0, 1]})
    esq = CausalSchemaEstricto(treatment="D", outcome="Y", covariates=["z"], instruments=["z"])
    with pytest.raises(ValueError, match="doble rol"):
        esq.validate(df)


def test_post_tratamiento():
    df = pd.DataFrame({"D": [0, 1], "Y": [1, 2], "x": [0.1, 0.2], "post": [0, 1]})
    esq = CausalSchemaEstricto(
        treatment="D", outcome="Y", covariates=["x", "post"], post_treatment=["post"]
    )
    with pytest.raises(ValueError, match="posterior"):
        esq.validate(df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
