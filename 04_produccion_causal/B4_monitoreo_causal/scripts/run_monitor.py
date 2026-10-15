#!/usr/bin/env python3
"""Run the local monitoring simulation and write auditable reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

B4 = Path(__file__).resolve().parents[1]
if str(B4) not in sys.path:
    sys.path.insert(0, str(B4))
from monitor_core import simulate_monitor_table  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=B4 / "reports" / "monitoring_windows.csv")
    args = parser.parse_args()
    table = simulate_monitor_table()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False)
    summary = {
        "windows": int(len(table)),
        "actions": table["accion"].value_counts().to_dict(),
        "max_ks": float(table["ks_max"].max()),
        "source": "observed_train + drift simulado; truth no usado",
    }
    (args.output.with_suffix(".json")).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
