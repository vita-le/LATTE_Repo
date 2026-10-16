# src/latte/analysis/roskam/validation.py
"""Step-by-step bridge between a CPACS-derived RoskamCase and the MATLAB reference cases.

Starting from the case built from the CPACS, one input at a time is replaced with the
value used by the MATLAB code. The error against the MATLAB results shrinks as the
inputs converge; the contribution of every difference can be read from the rows.
"""
from dataclasses import dataclass, replace

import numpy as np

from latte.analysis.roskam.case import RoskamCase
from latte.analysis.roskam.coefficients import RoskamAirfoil, RoskamGeometry
from latte.analysis.roskam.solver import RoskamSolver
from latte.analysis.runner import run_conditions
from latte.core.flight_state import FlightCondition


@dataclass(frozen=True)
class BridgeRow:
    step: str
    cha_max_rel: float
    cha_mean_rel: float
    chd_max_rel: float
    chd_mean_rel: float
    moment_max_abs: float
    moment_mean_abs: float
    failed: int = 0


def conditions_from(data) -> list:
    return [
        FlightCondition(c["mach"], c["altitude_m"], c["alpha_deg"], 0.0, c["delta_deg"])
        for c in data["cases"]
    ]


def compare_with_matlab(case: RoskamCase, data) -> BridgeRow | None:
    """Run all MATLAB conditions on `case` and compare Cha, Chd and the hinge moment."""
    results = run_conditions(RoskamSolver(case), conditions_from(data))
    pairs = [(r, c["expected"]) for r, c in zip(results, data["cases"]) if r.ok]
    if not pairs:
        return None
    rel = lambda value, ref: abs(value - ref) / abs(ref)
    cha = np.array([rel(r.cha, e["Cha"]) for r, e in pairs])
    chd = np.array([rel(r.chd, e["Chd"]) for r, e in pairs])
    moment = np.array([abs(r.hinge_moment_nm - e["Ma"]) for r, e in pairs])
    return BridgeRow("", float(cha.max()), float(cha.mean()), float(chd.max()), float(chd.mean()),
                      float(moment.max()), float(moment.mean()), failed=len(results) - len(pairs))


def matlab_bridge(case: RoskamCase, data) -> list[BridgeRow]:
    """Cumulative steps from the CPACS case to the MATLAB inputs (last row = full regression)."""
    ref_geo = RoskamGeometry(**data["geometry"])
    ref_air = RoskamAirfoil(**data["airfoil"])
    hm = data["hinge_moment"]

    steps = []
    current = case
    steps.append(("CPACS as is (local-chord cf/c, airfoil from the file)", current))

    current = replace(current,
                      geometry=replace(current.geometry, cf_reference_chord=None, mac=ref_geo.mac),
                      reynolds_length_m=ref_geo.mac)
    steps.append(("+ MATLAB cf/c = c_aileron/MAC and MAC = S/b", current))

    current = replace(current, airfoil=replace(
        current.airfoil, t_c=ref_air.t_c, phi_te_1_deg=ref_air.phi_te_1_deg, phi_te_2_deg=ref_air.phi_te_2_deg))
    steps.append(("+ MATLAB airfoil (t/c = 0.10, Phi_TE = 0)", current))

    current = replace(current, geometry=replace(current.geometry, aspect_ratio=ref_geo.aspect_ratio))
    steps.append((f"+ AR from S_ref (AR = {ref_geo.aspect_ratio:.3f})", current))

    current = replace(current, geometry=replace(current.geometry, lambda_hl_deg=ref_geo.lambda_hl_deg))
    steps.append((f"+ hinge-line sweep of MATLAB ({ref_geo.lambda_hl_deg:.2f} deg)", current))

    current = replace(current, geometry=ref_geo, airfoil=ref_air,
                      aileron_area_m2=hm["s_f"], aileron_chord_m=ref_geo.c_aileron,
                      offset_nm=hm["offset_nm"], reynolds_length_m=ref_geo.mac)
    steps.append(("+ all remaining MATLAB inputs (full regression)", current))

    rows = []
    for name, step_case in steps:
        row = compare_with_matlab(step_case, data)
        if row is not None:
            row = replace(row, step=name)
            rows.append(row)
    return rows


def single_input_effects(cpacs_case: RoskamCase, data) -> list[BridgeRow]:
    """MATLAB reference case with ONE input at a time replaced by the CPACS-derived value.

    Unlike matlab_bridge (cumulative, order dependent) every row isolates one difference.
    """
    ref_geo = RoskamGeometry(**data["geometry"])
    ref_air = RoskamAirfoil(**data["airfoil"])
    hm = data["hinge_moment"]
    baseline = RoskamCase(ref_geo, ref_air, hm["s_f"], ref_geo.c_aileron, ref_geo.mac, hm["offset_nm"])
    g, a = cpacs_case.geometry, cpacs_case.airfoil

    variants = [
        ("MATLAB inputs (reference)", baseline),
        ("cf/c on the local chord, as in the CPACS model",
         replace(baseline, geometry=replace(ref_geo, cf_reference_chord=g.cf_reference_chord))),
        ("airfoil from the file (t/c and Phi_TE)",
         replace(baseline, airfoil=replace(ref_air, t_c=a.t_c, phi_te_1_deg=a.phi_te_1_deg,
                                           phi_te_2_deg=a.phi_te_2_deg))),
        (f"AR from the CPACS geometry ({g.aspect_ratio:.3f})",
         replace(baseline, geometry=replace(ref_geo, aspect_ratio=g.aspect_ratio))),
        (f"hinge-line sweep from the geometry ({g.lambda_hl_deg:.2f} deg)",
         replace(baseline, geometry=replace(ref_geo, lambda_hl_deg=g.lambda_hl_deg))),
        ("MAC (Reynolds number) from the CPACS geometry",
         replace(baseline, geometry=replace(ref_geo, mac=g.mac), reynolds_length_m=cpacs_case.reynolds_length_m)),
    ]
    rows = []
    for name, case in variants:
        row = compare_with_matlab(case, data)
        if row is not None:
            rows.append(replace(row, step=name))
    return rows