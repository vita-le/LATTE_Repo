# src/latte/analysis/hinge_moment.py
"""Hinge moment from the derivatives Cha and Chd (shared by Roskam and VLM)."""
import math

from latte.core.flight_state import FlightCondition, dynamic_pressure


def hinge_moment_coefficient(
    cha: float,
    chd: float,
    cond: FlightCondition,
    ch0: float = 0.0,
) -> float:
    """Ch = Ch0 + Cha*alpha + Chd*delta (derivatives in 1/rad)."""
    alpha = math.radians(cond.alpha_deg)
    delta = math.radians(cond.delta_deg)
    return ch0 + cha * alpha + chd * delta


def hinge_moment(
    cha: float,
    chd: float,
    cond: FlightCondition,
    s_f: float,
    c_f: float,
    offset_nm: float = 0.0,
) -> tuple[float, float]:
    """Return (Ch, hinge moment in N*m).

    s_f: control-surface area [m2]
    c_f: reference chord of the control surface [m]
    offset_nm: constant hinge moment at alpha = delta = 0 [N*m]
               (replaces the hard-coded Ch0 of the MATLAB code)
    """
    if s_f <= 0 or c_f <= 0:
        raise ValueError("Control-surface area and chord must be positive")
    q = dynamic_pressure(cond)
    ch0 = offset_nm / (q * s_f * c_f)
    ch = hinge_moment_coefficient(cha, chd, cond, ch0)
    return ch, q * s_f * c_f * ch