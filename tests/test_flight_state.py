# tests/test_flight_state.py
import pytest

from latte.core.flight_state import (
    FlightCondition,
    dynamic_pressure,
    dynamic_viscosity,
    flow_summary,
    isa_atmosphere,
    reynolds_number,
    true_airspeed,
)


def test_isa_sea_level():
    atm = isa_atmosphere(0.0)
    # Standard sea-level values
    assert atm["T"] == pytest.approx(288.15)
    assert atm["p"] == pytest.approx(101325.0)
    assert atm["rho"] == pytest.approx(1.225, rel=1e-3)
    assert atm["a"] == pytest.approx(340.29, rel=1e-3)


def test_isa_tropopause():
    atm = isa_atmosphere(11000.0)
    assert atm["T"] == pytest.approx(216.65)
    assert atm["p"] == pytest.approx(22632.0, rel=1e-3)


def test_true_airspeed():
    cond = FlightCondition(mach=0.5, altitude_m=0.0, alpha_deg=2.0)
    assert true_airspeed(cond) == pytest.approx(170.1, rel=1e-3)


def test_invalid_mach():
    with pytest.raises(ValueError):
        FlightCondition(mach=-0.1, altitude_m=0.0, alpha_deg=0.0)


def test_altitude_above_isa_limit_raises():
    with pytest.raises(ValueError):
        FlightCondition(mach=0.5, altitude_m=25000.0, alpha_deg=0.0)


def test_viscosity_sea_level():
    # Standard value at 288.15 K is about 1.789e-5 Pa*s
    assert dynamic_viscosity(288.15) == pytest.approx(1.789e-5, rel=1e-3)


def test_dynamic_pressure_sea_level():
    cond = FlightCondition(mach=0.5, altitude_m=0.0, alpha_deg=0.0)
    # q = 0.5 * 1.225 * 170.15^2 is about 17733 Pa
    assert dynamic_pressure(cond) == pytest.approx(17733.0, rel=1e-2)


def test_reynolds_sea_level():
    cond = FlightCondition(mach=0.5, altitude_m=0.0, alpha_deg=0.0)
    # About 1.165e7 per meter of reference length
    assert reynolds_number(cond, 1.0) == pytest.approx(1.165e7, rel=1e-2)


def test_reynolds_scales_with_length():
    cond = FlightCondition(mach=0.3, altitude_m=3000.0, alpha_deg=2.0)
    assert reynolds_number(cond, 2.0) == pytest.approx(2 * reynolds_number(cond, 1.0))


def test_reynolds_invalid_length():
    cond = FlightCondition(mach=0.3, altitude_m=0.0, alpha_deg=0.0)
    with pytest.raises(ValueError):
        reynolds_number(cond, 0.0)


def test_flow_summary_keys():
    cond = FlightCondition(mach=0.3, altitude_m=0.0, alpha_deg=0.0)
    assert "reynolds" not in flow_summary(cond)
    assert "reynolds" in flow_summary(cond, length_m=1.5)