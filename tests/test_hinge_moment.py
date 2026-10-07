# tests/test_hinge_moment.py
import math

import pytest

from latte.analysis.hinge_moment import hinge_moment, hinge_moment_coefficient
from latte.core.flight_state import FlightCondition, build_conditions, dynamic_pressure


def test_coefficient_is_linear():
    cond = FlightCondition(mach=0.3, altitude_m=0.0, alpha_deg=2.0, delta_deg=-3.0)
    ch = hinge_moment_coefficient(-0.4, -0.8, cond)
    expected = -0.4 * math.radians(2.0) + -0.8 * math.radians(-3.0)
    assert ch == pytest.approx(expected)


def test_moment_matches_manual_formula():
    cond = FlightCondition(mach=0.5, altitude_m=0.0, alpha_deg=4.0, delta_deg=5.0)
    ch, m = hinge_moment(-0.3, -0.7, cond, s_f=1.135, c_f=0.5)
    q = dynamic_pressure(cond)
    assert m == pytest.approx(q * 1.135 * 0.5 * ch)


def test_offset_adds_constant_moment():
    cond = FlightCondition(mach=0.5, altitude_m=0.0, alpha_deg=0.0, delta_deg=0.0)
    _, m = hinge_moment(-0.3, -0.7, cond, s_f=1.0, c_f=1.0, offset_nm=-400.0)
    assert m == pytest.approx(-400.0)


def test_invalid_geometry():
    cond = FlightCondition(mach=0.5, altitude_m=0.0, alpha_deg=0.0)
    with pytest.raises(ValueError):
        hinge_moment(-0.3, -0.7, cond, s_f=0.0, c_f=1.0)


def test_delta_loop():
    conds = build_conditions(0.3, 0.0, 0.0, delta_deg=(-10.0, 10.0, 5))
    assert len(conds) == 5
    assert conds[0].delta_deg == pytest.approx(-10.0)
    assert conds[-1].delta_deg == pytest.approx(10.0)