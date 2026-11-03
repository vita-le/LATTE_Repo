# src/latte/analysis/roskam/adapter.py
"""Build RoskamGeometry from the plain dictionaries of CPACSDocument.

Input data (all lengths in metres):
  wing:     {'span', 'area', 'segments': [{'uid', 'stations': [{'chord', 'eta',
             'leading_edge': (x, y, z), 'trailing_edge': (x, y, z)}, ...]}]}
  aileron_geometry: {'inner'/'outer': {'leading_edge', 'hinge', 'trailing_edge'}}
"""
import math
import warnings
from dataclasses import dataclass, replace

import numpy as np

from latte.analysis.roskam.coefficients import RoskamGeometry, RoskamModelWarning


@dataclass(frozen=True)
class Planform:
    span: float                 # full span b [m]
    area: float                 # planform area S [m2] (both semi-wings)
    aspect_ratio: float
    mac: float                  # mean aerodynamic chord [m]
    lambda_c4_deg: float        # sweep of the quarter-chord line, root to tip [deg]
    mirrored: bool              # True if the CPACS wing is one half of a symmetric wing
    area_source: str            # 'cpacs' (TiGL area) or 'stations' (integrated)
    y: np.ndarray               # station y coordinates (sorted)
    chord: np.ndarray           # chord at each station


def _distance(p, q):
    return math.dist(p, q)


def planform_from_wing(wing: dict) -> Planform:
    """Planform quantities from the wing stations (trapezoidal integration)."""
    stations = [s for seg in wing["segments"] for s in seg["stations"]]
    if len(stations) < 2:
        raise ValueError("The wing needs at least two stations")
    stations.sort(key=lambda s: s["leading_edge"][1])

    # Drop duplicated stations (shared by consecutive segments)
    unique = [stations[0]]
    for s in stations[1:]:
        if abs(s["leading_edge"][1] - unique[-1]["leading_edge"][1]) > 1e-9:
            unique.append(s)
    stations = unique

    y = np.array([s["leading_edge"][1] for s in stations])
    chord = np.array([s["chord"] for s in stations])
    if y[-1] - y[0] <= 0:
        raise ValueError("Wing stations do not extend in the spanwise (y) direction")

    area_half = float(np.sum(np.diff(y) * (chord[:-1] + chord[1:]) / 2))
    # Exact integral of c^2 for a chord that is linear between stations:
    # int c^2 dy = dy * (c1^2 + c1*c2 + c2^2) / 3 on each interval
    c1, c2 = chord[:-1], chord[1:]
    mean_square = float(np.sum(np.diff(y) * (c1 ** 2 + c1 * c2 + c2 ** 2) / 3))
    mac = mean_square / area_half

    # One half of a symmetric wing: TiGL reports the full span
    y_extent = float(y[-1] - y[0])
    mirrored = wing["span"] > 1.5 * y_extent
    # TiGL reports the area of the semi-wing; it is exact, so prefer it when it
    # agrees with the area integrated from the stations (10 samples only).
    cpacs_half = float(wing.get("area") or 0.0)
    area_source = "stations"
    if cpacs_half > 0:
        if abs(cpacs_half - area_half) / area_half <= 0.03:
            area_half, area_source = cpacs_half, "cpacs"
        else:
            warnings.warn(
                f"CPACS wing area ({cpacs_half:.4g} m2) differs from the area integrated "
                f"from the stations ({area_half:.4g} m2): using the integrated one",
                RoskamModelWarning, stacklevel=2,
            )
    area = 2 * area_half if mirrored else area_half
    span = float(wing["span"])

    # Quarter-chord line from root to tip station
    def quarter_chord_x(s):
        le, te = s["leading_edge"], s["trailing_edge"]
        return le[0] + 0.25 * (te[0] - le[0])

    dx = quarter_chord_x(stations[-1]) - quarter_chord_x(stations[0])
    lambda_c4 = math.degrees(math.atan2(dx, y[-1] - y[0]))

    return Planform(
        span=span, area=area, aspect_ratio=span ** 2 / area, mac=mac,
        lambda_c4_deg=lambda_c4, mirrored=mirrored, area_source=area_source, y=y, chord=chord,
    )


def build_roskam_geometry(
    wing: dict,
    aileron_geometry: dict,
    use_local_chord_ratio: bool = True,
    reference_area: float | None = None,
) -> tuple[RoskamGeometry, dict]:
    """Return (RoskamGeometry, diagnostics).

    use_local_chord_ratio=True (default): cf_ratio = aileron chord / local wing chord.
    False reproduces the MATLAB cf_ratio = c_aileron / MAC.
    reference_area: wing reference area S_ref [m2] (CPACS model/reference/area). If given,
    AR = b^2 / S_ref (as the MATLAB Geometry_Function); otherwise AR comes from the geometry.
    """
    plan = planform_from_wing(wing)
    inner, outer = aileron_geometry["inner"], aileron_geometry["outer"]

    y_i, y_o = inner["hinge"][1], outer["hinge"][1]
    if y_o <= y_i:
        raise ValueError("Aileron outboard section must lie outboard of the inboard one")

    chord_in = _distance(inner["leading_edge"], inner["trailing_edge"])
    chord_out = _distance(outer["leading_edge"], outer["trailing_edge"])
    c_aileron = 0.5 * (chord_in + chord_out)            # mean chord of the trapezoid

    # Hinge position as a fraction of the aileron chord, from its leading edge
    h_in = _distance(inner["leading_edge"], inner["hinge"]) / chord_in
    h_out = _distance(outer["leading_edge"], outer["hinge"]) / chord_out
    hinge = 0.5 * (h_in + h_out)

    dx = outer["hinge"][0] - inner["hinge"][0]
    lambda_hl = math.degrees(math.atan2(dx, y_o - y_i))

    local_chord = 0.5 * float(
        np.interp(y_i, plan.y, plan.chord) + np.interp(y_o, plan.y, plan.chord)
    )

    geometry = RoskamGeometry(
        b=plan.span,
        lambda_c4_deg=plan.lambda_c4_deg,
        lambda_hl_deg=lambda_hl,
        y_i=y_i,
        y_o=y_o,
        aspect_ratio=plan.aspect_ratio,
        c_aileron=c_aileron,
        mac=plan.mac,
        hinge=hinge,
        cf_reference_chord=local_chord if use_local_chord_ratio else None,
    )
    if reference_area is not None:
        if reference_area <= 0:
            raise ValueError("The reference area must be positive")
        geometry = replace(geometry, aspect_ratio=plan.span ** 2 / reference_area)
    cb_over_cf = hinge / (1 - hinge)
    diagnostics = {
        "planform_area_m2": plan.area,
        "area_source": plan.area_source,
        "reference_area_m2": reference_area,
        "aspect_ratio_geometric": plan.aspect_ratio,
        "cpacs_wing_area_m2": wing["area"],
        "mirrored_wing": plan.mirrored,
        "local_wing_chord_m": local_chord,
        "cf_ratio_mac": c_aileron / plan.mac,
        "cf_ratio_local": c_aileron / local_chord,
        "cb_over_cf": cb_over_cf,
        "aileron_area_m2": c_aileron * (y_o - y_i),
    }
    return geometry, diagnostics