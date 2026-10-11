# scripts/run_roskam.py
"""Run the Roskam solver on every aileron of a CPACS file for a few flight conditions."""
import sys
import warnings

from latte.analysis.roskam.case import build_case
from latte.analysis.roskam.solver import RoskamSolver
from latte.analysis.runner import run_conditions
from latte.core.cpacs_document import CPACSDocument
from latte.core.flight_state import build_conditions

path = sys.argv[1]
configuration = sys.argv[2] if len(sys.argv) > 2 else None

with CPACSDocument(path, configuration) as doc:
    cases = [build_case(doc, aileron) for aileron in doc.ailerons]

# Mach 0.3-0.5, sea level, alpha 0 and 4 deg, delta -10, 0 and +10 deg
conditions = build_conditions((0.3, 0.5, 3), 0.0, (0.0, 4.0, 2), (-10.0, 10.0, 3))

for case in cases:
    print("=" * 78)
    print(f"Aileron {case.label}:  S_f = {case.aileron_area_m2:.3f} m2,  t/c = {case.airfoil.t_c:.3f}")
    results = run_conditions(RoskamSolver(case), conditions)
    for r in results:
        c = r.condition
        head = f"  M={c.mach:.2f} a={c.alpha_deg:4.1f} d={c.delta_deg:5.1f}"
        if r.ok:
            print(f"{head}  Cha={r.cha:8.4f}  Chd={r.chd:8.4f}  H={r.hinge_moment_nm:10.1f} N*m")
        else:
            print(f"{head}  ERROR: {r.error}")
            break                                  # same error for every condition
    warnings_seen = sorted({w for r in results for w in r.warnings})
    for w in warnings_seen:
        print("  warning:", w)