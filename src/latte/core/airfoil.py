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


def airfoil_properties(x, z) -> AirfoilProperties:
    """t/c and Roskam trailing-edge angles from the contour points of an airfoil.

    x, z: coordinates of the closed contour in either direction (chordwise x, vertical z).
    The thickness is measured vertically; sparse coordinates reduce the accuracy
    (the angles use linear interpolation between points).
    """
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

    def thickness(xq):
        return np.interp(xq, ux, uz) - np.interp(xq, lx, lz)

    grid = np.linspace(0.0, 1.0, 2001)
    t_c = float(np.max(thickness(grid)))

    def te_angle_deg(x_start):
        # tan(phi/2) is the slope of the half thickness between x_start and 0.99c
        tan_half = (thickness(x_start) - thickness(TE_END)) / 2.0 / (TE_END - x_start)
        return 2.0 * math.degrees(math.atan(float(tan_half)))

    return AirfoilProperties(
        t_c=t_c,
        phi_te_1_deg=te_angle_deg(PHI1_START),
        phi_te_2_deg=te_angle_deg(PHI2_START),
    )