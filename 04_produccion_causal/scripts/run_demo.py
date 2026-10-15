#!/usr/bin/env python3
"""Run the public local end-to-end causal demo."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from causalops.flujo import demo_completa, escribir_informe  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artefactos" / "demo")
    parser.add_argument("--n", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    output = args.output.resolve()
    info, cases = demo_completa(output, output / "datos", n=args.n, semilla=args.seed)
    print(escribir_informe(info, cases, output), end="")
    return 0 if all(case["estado"] == "PASA" for case in cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
