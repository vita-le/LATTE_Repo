# tests/test_flight_state.py
import pytest

from latte.core.flight_state import FlightCondition, isa_atmosphere, true_airspeed


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