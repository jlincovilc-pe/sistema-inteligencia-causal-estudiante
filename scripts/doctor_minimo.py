#!/usr/bin/env python3
"""Diagnóstico mínimo del entorno docente; no instala paquetes."""

# <!-- OPS:ENS-04:inicio -->
from __future__ import annotations

import importlib
import sys

REQUIRED = ("numpy", "pandas", "sklearn")
RANDOM_STATE = 42


def main() -> int:
    ok = True
    version_ok = sys.version_info >= (3, 10)
    print(f"python >= 3.10: {'OK' if version_ok else 'FALTA'} ({sys.version.split()[0]})")
    ok &= version_ok

    for module in REQUIRED:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - el diagnóstico informa el entorno
            print(f"import {module}: FALTA ({exc.__class__.__name__})")
            ok = False
        else:
            print(f"import {module}: OK")

    print(f"semilla de referencia del curso: {RANDOM_STATE}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
# <!-- OPS:ENS-04:fin -->
