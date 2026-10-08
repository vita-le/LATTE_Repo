# src/latte/analysis/roskam/charts.py
"""Digitized Roskam Part VI charts, ported 1:1 from the MATLAB get_*.m files.

Behaviour is kept identical to MATLAB (same tables, same interpolation method,
same clamping/extrapolation), but every out-of-range use now emits a
RoskamRangeWarning instead of being silent.

Requires scipy >= 1.13 (Akima1DInterpolator with method="makima").
"""
import warnings

import numpy as np
from scipy.interpolate import (
    Akima1DInterpolator,
    PchipInterpolator,
    RegularGridInterpolator,
    interp1d,
)


class RoskamRangeWarning(UserWarning):
    """An input is outside the range covered by a digitized chart."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _warn(message):
    warnings.warn(message, RoskamRangeWarning, stacklevel=3)


def _clamp(value, lo, hi, name):
    """Saturate value to [lo, hi] like the MATLAB max(min(...)) lines, with a warning."""
    clamped = min(max(value, lo), hi)
    if clamped != value:
        _warn(f"{name}={value:.4g} outside chart range [{lo}, {hi}]: clamped to {clamped:.4g}")
    return clamped


def _check_range(value, lo, hi, name, consequence):
    if not lo <= value <= hi:
        _warn(f"{name}={value:.4g} outside chart range [{lo}, {hi}]: {consequence}")


class _Table2D:
    """MATLAB interp2(x, y, V, xq, yq, 'linear'): x = columns axis, y = rows axis."""

    def __init__(self, x, y, values):
        self._f = RegularGridInterpolator(
            (np.asarray(y, float), np.asarray(x, float)), np.asarray(values, float)
        )

    def __call__(self, xq, yq):
        # Inputs must already be clamped inside the table
        return float(self._f([[yq, xq]])[0])


def _makima(x, y, xq):
    """MATLAB interp1(x, y, xq, 'makima') (extrapolates like MATLAB)."""
    return float(Akima1DInterpolator(x, y, method="makima", extrapolate=True)(xq))


def _pchip(x, y, xq):
    """MATLAB interp1(x, y, xq, 'pchip') (extrapolates like MATLAB)."""
    return float(PchipInterpolator(x, y, extrapolate=True)(xq))


def _linear_extrap(x, y, xq):
    """MATLAB interp1(x, y, xq, 'linear', 'extrap')."""
    return float(interp1d(x, y, kind="linear", fill_value="extrapolate")(xq))


# ---------------------------------------------------------------------------
# Section lift-curve slope (Cl_alpha) charts
# ---------------------------------------------------------------------------
def get_clalpha_theory(tc: float) -> float:
    """get_ClalphaTheory.m - theoretical Cl_alpha [1/rad], linear in t/c."""
    _check_range(tc, 0.0, 0.20, "t/c", "result is extrapolated")
    return 5.1 * tc + 6.28


_LOG_RE_REFS = np.log10([1e6, 1e7, 1e8])


def get_clalpha_correction(tan_phi_half: float, reynolds: float) -> float:
    """get_ClalphaCorrection.m - ratio Cl_alpha / Cl_alpha_theory.

    Three Re lines, interpolated linearly in log10(Re), extrapolated outside.
    """
    ratios = [
        -1.00 * tan_phi_half + 0.90,   # Re = 1e6
        -0.80 * tan_phi_half + 0.94,   # Re = 1e7
        -0.75 * tan_phi_half + 0.97,   # Re = 1e8
    ]
    _check_range(reynolds, 1e6, 1e8, "Re", "result is extrapolated")
    return _linear_extrap(_LOG_RE_REFS, ratios, np.log10(reynolds))


# ---------------------------------------------------------------------------
# Ch_alpha charts
# ---------------------------------------------------------------------------
def get_chalpha_theory(cf_c: float, tc: float) -> float:
    """get_ChalphaTheory.m - theoretical 2D Ch_alpha [1/rad] (linear fit)."""
    _check_range(tc, 0.0, 0.16, "t/c", "fit used outside its range")
    return -1.34 * cf_c + 0.69 * tc - 0.202


_CHA_CORR_LEVELS = [0.7, 0.8, 0.85, 0.9, 1.0]   # Cl_alpha ratio
_CHA_CORR_CF_C = [0.1, 0.2, 0.3, 0.4]
_CHA_CORR_TABLE = _Table2D(
    _CHA_CORR_CF_C,
    _CHA_CORR_LEVELS,
    [
        [-0.11, -0.023, 0.064, 0.151],   # 0.7
        [0.35, 0.417, 0.484, 0.551],     # 0.8
        [0.54, 0.593, 0.646, 0.699],     # 0.85
        [0.72, 0.756, 0.792, 0.828],     # 0.9
        [1.00, 1.000, 1.000, 1.000],     # 1.0
    ],
)


def get_chalpha_correction(cf_c: float, cl_ratio: float) -> float:
    """get_ChalphaCorrection.m - viscous correction ratio Ch1_alpha / Ch_alpha_theory."""
    cf = _clamp(cf_c, 0.1, 0.4, "cf/c")
    level = _clamp(cl_ratio, 0.7, 1.0, "Cl_alpha ratio")
    return _CHA_CORR_TABLE(cf, level)


_BALANCE_ALPHA = {
    "sharp": ([0.18, 0.5], [1.00, 0.30]),
    "elliptic": ([0.17, 0.5], [0.90, 0.20]),
    "round": ([0.15, 0.5], [0.93, 0.02]),
}


def get_balance_effect_chalpha(balance_ratio: float, nose_type: str = "elliptic") -> float:
    """get_BalanceEffect_Chalpha.m - linear through 2 points, extrapolated."""
    try:
        x, y = _BALANCE_ALPHA[nose_type.lower()]
    except KeyError:
        raise ValueError(
            f"Invalid nose type {nose_type!r}: use {sorted(_BALANCE_ALPHA)}"
        ) from None
    _check_range(balance_ratio, 0.1, 0.5, "balance ratio", "result is extrapolated")
    return _linear_extrap(x, y, balance_ratio)


_AR_ALPHA_X = [2, 3, 4, 6, 8, 10]
_AR_ALPHA_Y = [0.0183, 0.014, 0.011, 0.007, 0.0045, 0.0035]


def get_ar_correction_alpha(aspect_ratio: float) -> float:
    """get_AR_Correction_alpha.m - 'term1', pchip through 6 points."""
    _check_range(aspect_ratio, 2, 10, "AR", "result is extrapolated")
    return _pchip(_AR_ALPHA_X, _AR_ALPHA_Y, aspect_ratio)


_B2_CF_C = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
_B2_CB_CF = [0, 0.2, 0.3, 0.4, 0.5, 0.6]
_B2_TABLE = [
    [0.50, 0.71, 0.94, 1.10, 1.22, 1.32, 1.41],   # cb/cf = 0.0
    [0.44, 0.62, 0.84, 1.00, 1.13, 1.24, 1.33],   # cb/cf = 0.2
    [0.39, 0.56, 0.78, 0.93, 1.06, 1.17, 1.26],   # cb/cf = 0.3
    [0.32, 0.49, 0.70, 0.85, 0.98, 1.09, 1.18],   # cb/cf = 0.4
    [0.22, 0.39, 0.60, 0.76, 0.89, 1.00, 1.09],   # cb/cf = 0.5
    [0.10, 0.24, 0.45, 0.62, 0.76, 0.88, 0.98],   # cb/cf = 0.6
]


def get_b2(cf_c: float, cb_cf: float) -> float:
    """get_B2.m - interp2 'makima'.

    MATLAB's 2D makima is not exposed as a simple formula: here it is done as a
    tensor product (makima along cf/c on every curve, then along cb/cf).
    TO VALIDATE against the MATLAB value of RoskamCoeff.B2.
    """
    _check_range(cf_c, 0.05, 0.6, "cf/c", "result is extrapolated")
    _check_range(cb_cf, 0.0, 0.6, "cb/cf", "result is extrapolated")
    along_cf = [_makima(_B2_CF_C, row, cf_c) for row in _B2_TABLE]
    return _makima(_B2_CB_CF, along_cf, cb_cf)


_KA_X = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
_KA_Y = [1.0, 1.25, 1.7, 2.4, 3.3, 4.3]


def get_ka(eta: float) -> float:
    """get_Ka.m - pchip, no clamping in MATLAB (extrapolates)."""
    _check_range(eta, 0.0, 1.0, "eta", "result is extrapolated")
    return _pchip(_KA_X, _KA_Y, eta)


# ---------------------------------------------------------------------------
# Ch_delta charts
# ---------------------------------------------------------------------------
_AD_TABLE = _Table2D(
    [0.0, 10.0, 20.0, 30.0, 40.0, 50.0],   # deflection [deg]
    [0.2, 0.3, 0.4],                       # cf/c
    [
        [0.45, 0.44, 0.43, 0.38, 0.32, 0.24],   # cf/c = 0.2
        [0.56, 0.55, 0.54, 0.50, 0.44, 0.34],   # cf/c = 0.3
        [0.60, 0.59, 0.58, 0.54, 0.48, 0.40],   # cf/c = 0.4
    ],
)


def get_ad(deflection_deg: float, cf_c: float, use_abs: bool = False) -> float:
    """get_ad.m - flap effectiveness alpha_delta.

    Like MATLAB, deflection is clamped to 0-50 deg, so a NEGATIVE deflection is
    treated as 0 deg. use_abs=True uses |delta| (probably right for an aileron).
    """
    if use_abs:
        deflection_deg = abs(deflection_deg)
    d = _clamp(deflection_deg, 0.0, 50.0, "delta [deg]")
    c = _clamp(cf_c, 0.2, 0.4, "cf/c")
    return _AD_TABLE(d, c)


_CHD_THEORY_TC = [0, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15]
_CHD_THEORY_CF = [0.1, 0.2, 0.3, 0.4]
_CHD_THEORY_TABLE = _Table2D(
    _CHD_THEORY_CF,
    _CHD_THEORY_TC,
    [
        [-0.88, -0.91, -0.95, -0.99],   # t/c = 0
        [-0.84, -0.88, -0.93, -0.98],   # 0.04
        [-0.80, -0.85, -0.91, -0.96],   # 0.06
        [-0.77, -0.82, -0.88, -0.94],   # 0.08
        [-0.74, -0.79, -0.86, -0.92],   # 0.10
        [-0.70, -0.76, -0.83, -0.90],   # 0.12
        [-0.64, -0.72, -0.81, -0.89],   # 0.15
    ],
)


def get_chdelta_theory(cf_c: float, tc: float) -> float:
    """get_ChdeltaTheory.m - theoretical 2D Ch_delta [1/rad]."""
    tc = _clamp(tc, 0.0, 0.15, "t/c")
    cf = _clamp(cf_c, 0.1, 0.4, "cf/c")
    return _CHD_THEORY_TABLE(cf, tc)


_CHD_CORR_LEVELS = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0]
_CHD_CORR_CF = [0.1, 0.2, 0.3, 0.4]
_CHD_CORR_TABLE = _Table2D(
    _CHD_CORR_CF,
    _CHD_CORR_LEVELS,
    [
        [0.66, 0.60, 0.52, 0.41],   # 0.60
        [0.71, 0.67, 0.61, 0.53],   # 0.65
        [0.76, 0.73, 0.69, 0.63],   # 0.70
        [0.81, 0.79, 0.76, 0.72],   # 0.75
        [0.85, 0.84, 0.82, 0.79],   # 0.80
        [0.89, 0.88, 0.87, 0.85],   # 0.85
        [0.93, 0.92, 0.91, 0.90],   # 0.90
        [0.97, 0.96, 0.96, 0.95],   # 0.95
        [1.00, 1.00, 1.00, 1.00],   # 1.00
    ],
)


def get_chdelta_correction(cf_c: float, cl_ratio: float) -> float:
    """get_ChdeltaCorrection.m - viscous correction ratio for Ch_delta."""
    cf = _clamp(cf_c, 0.1, 0.4, "cf/c")
    level = _clamp(cl_ratio, 0.6, 1.0, "Cl_alpha ratio")
    return _CHD_CORR_TABLE(cf, level)


_CLD_THEORY_TC = [0.05, 0.08, 0.12, 0.15, 0.20]
_CLD_THEORY_K = [7.8, 8.1, 8.4, 8.8, 9.2]


def get_cldelta_theory(cf_c: float, tc: float) -> float:
    """get_CldeltaTheory.m - Cl_delta = k(t/c) * (cf/c)^0.6 [1/rad]."""
    tc = _clamp(tc, 0.05, 0.20, "t/c")
    k = float(np.interp(tc, _CLD_THEORY_TC, _CLD_THEORY_K))
    return k * cf_c ** 0.6


_CLD_CORR_LEVELS = [0.7, 0.8, 0.9, 1.0]
_CLD_CORR_CF = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
_CLD_CORR_TABLE = _Table2D(
    _CLD_CORR_CF,
    _CLD_CORR_LEVELS,
    [
        [0.15, 0.23, 0.31, 0.37, 0.44, 0.50],   # 0.7
        [0.47, 0.52, 0.57, 0.63, 0.66, 0.71],   # 0.8
        [0.76, 0.79, 0.82, 0.84, 0.86, 0.87],   # 0.9
        [1.00, 1.00, 1.00, 1.00, 1.00, 1.00],   # 1.0
    ],
)


def get_cldelta_correction(cf_c: float, cl_ratio: float) -> float:
    """get_CldeltaCorrection.m - ratio Cl_delta / Cl_delta_theory."""
    cl = _clamp(cl_ratio, 0.7, 1.0, "Cl_alpha ratio")
    cf = _clamp(cf_c, 0.1, 0.6, "cf/c")
    return _CLD_CORR_TABLE(cf, cl)


_BALANCE_DELTA_X = [0.18, 0.30, 0.40, 0.50]
_BALANCE_DELTA = {
    "sharp": [1.00, 0.82, 0.67, 0.52],
    "elliptic": [0.86, 0.70, 0.53, 0.35],
    "round": [0.75, 0.53, 0.31, 0.12],
    "low-drag": [0.81, 0.48, 0.22, 0.00],
}


def get_balance_effect_chdelta(balance_ratio: float, nose_type: str = "elliptic") -> float:
    """get_BalanceEffect_Chdelta.m - pchip, extrapolated."""
    try:
        y = _BALANCE_DELTA[nose_type.lower()]
    except KeyError:
        raise ValueError(
            f"Invalid nose type {nose_type!r}: use {sorted(_BALANCE_DELTA)}"
        ) from None
    _check_range(balance_ratio, 0.18, 0.5, "balance ratio", "result is extrapolated")
    return _pchip(_BALANCE_DELTA_X, y, balance_ratio)


_AR_DELTA_A = [2, 3, 4, 5, 6, 8, 10]
_AR_DELTA_CF = [0.2, 0.4, 0.6]
_AR_DELTA_DATA = [
    [0.0350, 0.0240, 0.0175, 0.0135, 0.0110, 0.0075, 0.0055],   # cf/c = 0.2
    [0.0310, 0.0210, 0.0155, 0.0120, 0.0095, 0.0065, 0.0048],   # cf/c = 0.4
    [0.0280, 0.0185, 0.0135, 0.0105, 0.0085, 0.0055, 0.0040],   # cf/c = 0.6
]


def get_ar_correction_delta(aspect_ratio: float, cf_ratio: float) -> float:
    """get_AR_Correction_delta.m - 'term2'.

    makima along AR on each cf/c curve, then linear across cf/c (as in MATLAB).
    """
    a = _clamp(aspect_ratio, 2, 10, "AR")
    cf = _clamp(cf_ratio, 0.2, 0.6, "cf/c")
    at_a = [_makima(_AR_DELTA_A, row, a) for row in _AR_DELTA_DATA]
    return float(np.interp(cf, _AR_DELTA_CF, at_a))


_KD_X = [0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0]
_KD_Y = [1.0, 1.15, 1.45, 1.95, 2.90, 3.60, 4.45]


def get_kd(eta: float) -> float:
    """get_Kd.m - pchip, input clamped to [0, 1]."""
    eta = _clamp(eta, 0.0, 1.0, "eta")
    return _pchip(_KD_X, _KD_Y, eta)