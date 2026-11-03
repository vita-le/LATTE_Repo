# src/latte/core/airfoil.py
"""Thickness and trailing-edge angles from airfoil coordinates (Roskam Part VI, fig. 10.62)."""
import math
from dataclasses import dataclass

import numpy as np

# Trailing-edge angle definitions (thesis eq. 3.5): angle measured between a point
# at x_start and the point at 0.99c.
PHI1_START = 0.90
PHI2_START = 0.95
TE_END = 0.99


@dataclass(frozen=True)
class AirfoilProperties:
    t_c: float                  # maximum thickness / chord
    phi_te_1_deg: float         # trailing-edge angle, 0.90c -> 0.99c [deg]
    phi_te_2_deg: float         # trailing-edge angle, 0.95c -> 0.99c [deg]


def _branches(x, z):
    """Split a closed airfoil contour at the leading edge into (upper, lower) functions."""
    i_le = int(np.argmin(x))
    first, second = (x[: i_le + 1], z[: i_le + 1]), (x[i_le:], z[i_le:])
    curves = []
    for bx, bz in (first, second):
        order = np.argsort(bx, kind="stable")
        curves.append((bx[order], bz[order]))
    # The upper surface is the one with larger z at mid-chord
    mid = [float(np.interp(0.5, cx, cz)) for cx, cz in curves]
    return (curves[0], curves[1]) if mid[0] >= mid[1] else (curves[1], curves[0])


def _fit_slope(bx, bz, x_start, x_end):
    """Slope of the least-squares line through the points of a surface in [x_start, x_end].

    With fewer than two points in the range the last four points of the surface are used
    (the same fallback as the MATLAB Airfoil_Function).
    """
    mask = (bx >= x_start) & (bx <= x_end)
    if mask.sum() < 2:
        return float(np.polyfit(bx[-4:], bz[-4:], 1)[0])
    return float(np.polyfit(bx[mask], bz[mask], 1)[0])


def _split(x, z):
    x = np.asarray(x, dtype=float)
    z = np.asarray(z, dtype=float)
    if x.shape != z.shape or x.ndim != 1:
        raise ValueError("x and z must be one-dimensional arrays of equal length")
    if len(x) < 10:
        raise ValueError("At least 10 contour points are needed to compute thickness")
    chord = float(x.max() - x.min())
    if chord <= 0:
        raise ValueError("Airfoil chord is zero")
    x = (x - x.min()) / chord          # normalise to unit chord
    z = z / chord
    (ux, uz), (lx, lz) = _branches(x, z)
    if len(ux) < 3 or len(lx) < 3:
        raise ValueError("Airfoil contour must have upper and lower surfaces")
    return ux, uz, lx, lz


def thickness_ratio_at(x, z, xi: float) -> float:
    """Airfoil thickness / chord at the chord fraction xi (vertical distance upper - lower)."""
    ux, uz, lx, lz = _split(x, z)
    return float(np.interp(xi, ux, uz) - np.interp(xi, lx, lz))


def airfoil_properties(x, z, te_method: str = "fit") -> AirfoilProperties:
    """t/c and Roskam trailing-edge angles from the contour points of an airfoil.

    x, z: coordinates of the closed contour in either direction (chordwise x, vertical z).
    The thickness is measured vertically; sparse coordinates reduce the accuracy.

    te_method:
      "fit"    as the MATLAB Airfoil_Function: a straight line is fitted to each surface in
               the chord range of the angle (0.90-0.99c and 0.95-0.99c) and the angle is
               |atan(slope_upper) - atan(slope_lower)|.
      "secant" slope of the half thickness between the two ends of the range.
    """
    if te_method not in ("fit", "secant"):
        raise ValueError("te_method must be 'fit' or 'secant'")
    ux, uz, lx, lz = _split(x, z)

    def thickness(xq):
        return np.interp(xq, ux, uz) - np.interp(xq, lx, lz)

    grid = np.linspace(0.0, 1.0, 2001)
    t_c = float(np.max(thickness(grid)))

    def te_angle_deg(x_start):
        if te_method == "fit":
            slope_u = _fit_slope(ux, uz, x_start, TE_END)
            slope_l = _fit_slope(lx, lz, x_start, TE_END)
            return math.degrees(abs(math.atan(slope_u) - math.atan(slope_l)))
        # tan(phi/2) is the slope of the half thickness between x_start and 0.99c
        tan_half = (thickness(x_start) - thickness(TE_END)) / 2.0 / (TE_END - x_start)
        return 2.0 * math.degrees(math.atan(float(tan_half)))

    return AirfoilProperties(
        t_c=t_c,
        phi_te_1_deg=te_angle_deg(PHI1_START),
        phi_te_2_deg=te_angle_deg(PHI2_START),
    )