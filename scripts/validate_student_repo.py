from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

forbidden_parts = {"autograder", "rubrics", "tests", "_ejecutados", "__pycache__", ".pytest_cache", "auditoria_experta", "00_guia_profesor", "08_semantica"}
forbidden_names = {"solution.ipynb", "truth.csv", "truth_train.csv", "truth_validation.csv", "truth_test.csv", "data_full.csv", "scorecard.json", "scm.json"}

paths = [p.relative_to(ROOT) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]
violations = []
for p in paths:
    if forbidden_parts.intersection(p.parts) or p.name in forbidden_names:
        violations.append(str(p))

student_labs = sorted(ROOT.glob("05_labs_sesion/L*/lab.ipynb"))
serie_a = sorted(ROOT.glob("03_notebooks_caso_estudio/notebooks/A*.ipynb"))
if len(student_labs) != 27:
    violations.append(f"se esperaban 27 labs y hay {len(student_labs)}")
if len(serie_a) != 4:
    violations.append(f"se esperaban 4 notebooks Serie A y hay {len(serie_a)}")
if any(p.name == "solution.ipynb" for p in ROOT.rglob("*.ipynb")):
    violations.append("hay una solution.ipynb")

if violations:
    print("\n".join(violations))
    raise SystemExit(1)
print(f"student repo: OK ({len(student_labs) + len(serie_a)} notebooks, sin secretos ni material docente)")
