# scripts/compare_f18_matlab.py
"""CPACS -> Roskam versus the 486 MATLAB cases, changing one input at a time.

Usage:
  python scripts/compare_f18_matlab.py [examples/F18SRA_thesis.xml]
"""
import json
import sys
import warnings
from pathlib import Path

from latte.analysis.roskam.case import build_case
from latte.analysis.roskam.validation import matlab_bridge, single_input_effects
from latte.core.cpacs_document import CPACSDocument

ROOT = Path(__file__).resolve().parent.parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "examples" / "F18SRA_thesis.xml"
data = json.loads((ROOT / "tests" / "data" / "roskam_fa18_cases.json").read_text())

with CPACSDocument(path) as doc:
    if not doc.ailerons:
        sys.exit("No ailerons in this file.")
    case = build_case(doc, doc.ailerons[0], offset_nm=data["hinge_moment"]["offset_nm"])

print(f"Inputs derived from {path.name}:")
for name, value in case.summary().items():
    print(f"  {name:36s} {value if isinstance(value, str) else format(value, '.5g')}")

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    rows = matlab_bridge(case, data)
    effects = single_input_effects(case, data)

print()
print(f"{'step':58s}{'Cha max':>9s}{'Chd max':>9s}{'Ma max [N*m]':>14s}{'Ma mean':>9s}")
for r in rows:
    print(f"{r.step:58s}{r.cha_max_rel * 100:8.1f}%{r.chd_max_rel * 100:8.1f}%"
          f"{r.moment_max_abs:14.1f}{r.moment_mean_abs:9.1f}")
print("\nEach difference ALONE, starting from the MATLAB inputs:")
print(f"{'input replaced by the CPACS value':58s}{'Cha max':>9s}{'Cha mean':>9s}{'Chd max':>9s}{'Ma max':>9s}{'Ma mean':>9s}")
for r in effects:
    print(f"{r.step:58s}{r.cha_max_rel * 100:8.1f}%{r.cha_mean_rel * 100:8.1f}%{r.chd_max_rel * 100:8.1f}%"
          f"{r.moment_max_abs:9.1f}{r.moment_mean_abs:9.1f}")
print("\nCha, Chd: relative difference over the 486 MATLAB cases; Ma: absolute, in N*m.")