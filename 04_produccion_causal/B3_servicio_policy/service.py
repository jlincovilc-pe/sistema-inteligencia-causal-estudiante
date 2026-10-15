#!/usr/bin/env python3
"""Local policy service without a UI framework.

Usage:
    python service.py --features-json '{"bw": 0, ...}'
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from policy_service import load_runtime_policy, predict_rows


def evaluate(values: dict[str, float]) -> dict[str, Any]:
    policy, bundle = load_runtime_policy()
    result = predict_rows(policy, values, bundle=bundle)
    for key, value in list(result.items()):
        if hasattr(value, "tolist"):
            result[key] = value.tolist()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Consulta local de una policy causal versionada")
    parser.add_argument("--features-json", required=True, help="Mapa JSON feature -> valor")
    args = parser.parse_args()
    values = json.loads(args.features_json)
    if not isinstance(values, dict):
        parser.error("--features-json debe ser un objeto JSON")
    print(json.dumps(evaluate({str(k): float(v) for k, v in values.items()}), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
