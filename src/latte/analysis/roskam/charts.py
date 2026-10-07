# src/latte/analysis/roskam/charts.py
"""Digitized Roskam Part VI charts, ported 1:1 from the MATLAB get_*.m files.

Behaviour is kept identical to MATLAB (same fits, same clamping/extrapolation),
but every out-of-range use now emits a RoskamRangeWarning instead of being silent.
"""
import warnings

import numpy as np
from scipy.interpolate import RegularGridInterpolator, interp1d


class RoskamRangeWarning(UserWarning):
    """An input is outside the range covered by a digitized chart."""


def _warn(message):
    # stacklevel=3: point at the caller of the chart function
    warnings.warn(message, RoskamRangeWarning, stacklevel=3)


# ---------------------------------------------------------------------------
# get_ChalphaTheory.m  (linear fit of the chart, symmetrical airfoil)
# ---------------------------------------------------------------------------
def get_chalpha_theory(cf_c: float, tc: float) -> float:
    """Theoretical 2D Ch_alpha [1/rad]; fit valid for t/c in [0, 0.16]."""
    if tc < 0 or tc > 0.16:
        _warn(f"t/c={tc:.4g} outside chart range [0, 0.16]")
    # Ch_alpha = a*(cf/c) + k*(t/c) + offset
    return -1.34 * cf_c + 0.69 * tc - 0.202


# ---------------------------------------------------------------------------
# get_ClalphaCorrection.m  (three Re lines, interpolated in log10(Re))
# ---------------------------------------------------------------------------
_LOG_RE_REFS = np.log10([1e6, 1e7, 1e8])


def get_clalpha_correction(tan_phi_half: float, reynolds: float) -> float:
    """Ratio Cl_alpha / Cl_alpha_theory; linear extrapolation outside 1e6-1e8."""
    ratios = [
        -1.00 * tan_phi_half + 0.90,   # Re = 1e6
        -0.80 * tan_phi_half + 0.94,   # Re = 1e7
        -0.75 * tan_phi_half + 0.97,   # Re = 1e8
    ]
    if reynolds < 1e6 or reynolds > 1e8:
        _warn(f"Re={reynolds:.3e} outside [1e6, 1e8]: result is extrapolated")
    f = interp1d(_LOG_RE_REFS, ratios, kind="linear", fill_value="extrapolate")
    return float(f(np.log10(reynolds)))


# ---------------------------------------------------------------------------
# get_ad.m  (flap effectiveness alpha_delta, 2D linear interpolation)
# ---------------------------------------------------------------------------
_AD_DEFLECTION = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0])   # [deg]
_AD_CF_C = np.array([0.2, 0.3, 0.4])
_AD_VALUES = np.array([                 # rows: cf/c, columns: deflection
    [0.45, 0.44, 0.43, 0.38, 0.32, 0.24],   # cf/c = 0.2
    [0.56, 0.55, 0.54, 0.50, 0.44, 0.34],   # cf/c = 0.3
    [0.60, 0.59, 0.58, 0.54, 0.48, 0.40],   # cf/c = 0.4
])
_AD_INTERP = RegularGridInterpolator((_AD_CF_C, _AD_DEFLECTION), _AD_VALUES)


def get_ad(deflection_deg: float, cf_c: float, use_abs: bool = False) -> float:
    """Flap effectiveness alpha_delta.

    Like MATLAB, inputs are clamped to the chart (deflection 0-50 deg,
    cf/c 0.2-0.4), so a NEGATIVE deflection is treated as 0 deg.
    use_abs=True uses |delta| instead (probably the right choice for an aileron).
    """
    if use_abs:
        deflection_deg = abs(deflection_deg)
    clamped_d = max(0.0, min(50.0, deflection_deg))
    clamped_c = max(0.2, min(0.4, cf_c))
    if clamped_d != deflection_deg or clamped_c != cf_c:
        _warn(
            f"alpha_delta inputs clamped to chart range: delta={deflection_deg:.3g} deg "
            f"-> {clamped_d:.3g}, cf/c={cf_c:.3g} -> {clamped_c:.3g}"
        )
    return float(_AD_INTERP([[clamped_c, clamped_d]])[0])