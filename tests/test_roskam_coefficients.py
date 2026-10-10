# tests/test_roskam_coefficients.py
"""Regression of the Python Roskam port against 486 MATLAB cases (F/A-18 SRA)."""
import json
import warnings
from pathlib import Path

import pytest

from latte.analysis.hinge_moment import hinge_moment
from latte.analysis.roskam.coefficients import (
    RoskamAirfoil,
    RoskamFlight,
    RoskamGeometry,
    hinge_coefficients,
)
from latte.core.flight_state import FlightCondition

DATA = json.loads(
    (Path(__file__).parent / "data" / "roskam_fa18_cases.json").read_text()
)
GEO = RoskamGeometry(**DATA["geometry"])
AIRFOIL = RoskamAirfoil(**DATA["airfoil"])
CASES = DATA["cases"]

# 2D 'makima' of get_b2 differs from MATLAB by ~1e-5 (relative); it propagates here
LOOSE_KEYS = {"B2", "Delta_Cha", "Delta_Chd", "Cha_final", "Chd_final"}


def run_case(case):
    flight = RoskamFlight(case["mach"], case["delta_deg"], case["reynolds"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")      # model/range warnings are expected here
        return hinge_coefficients(GEO, AIRFOIL, flight)


def test_there_are_486_cases():
    assert len(CASES) == 486


def test_all_intermediates_match_matlab():
    worst = {}
    for case in CASES:
        result = run_case(case)
        for key, value in result.values.items():
            expected = case["expected"][key]
            tol = 1e-4 if key in LOOSE_KEYS else 1e-9
            error = abs(value - expected) / max(abs(expected), 1e-12)
            worst[key] = max(worst.get(key, 0.0), error)
            assert error < tol, f"case {case['case']}: {key} {value} vs {expected}"
    assert len(worst) >= 40


def test_cha_chd_match_matlab():
    for case in CASES:
        result = run_case(case)
        assert result.cha == pytest.approx(case["expected"]["Cha"], rel=1e-4)
        assert result.chd == pytest.approx(case["expected"]["Chd"], rel=1e-4)


def test_hinge_moment_matches_matlab():
    # The atmosphere of flight_state differs from MATLAB's by ~0.1-0.2% (Re) and
    # ~0.03% (q), so the moment is compared with an absolute tolerance in N*m.
    hm = DATA["hinge_moment"]
    for case in CASES:
        result = run_case(case)
        cond = FlightCondition(
            case["mach"], case["altitude_m"], case["alpha_deg"], 0.0, case["delta_deg"]
        )
        _, moment = hinge_moment(
            result.cha, result.chd, cond, hm["s_f"], GEO.c_aileron, hm["offset_nm"]
        )
        assert moment == pytest.approx(case["expected"]["Ma"], abs=15.0)


def test_supersonic_is_rejected():
    flight = RoskamFlight(mach=1.1, delta_deg=0.0, reynolds=2e7)
    with pytest.raises(ValueError):
        hinge_coefficients(GEO, AIRFOIL, flight)


def test_thickness_warning_is_emitted_for_zero_te_angle():
    # Phi_TE = 0 differs from t/c = 0.1 by more than the 1e-2 tolerance
    from latte.analysis.roskam.coefficients import RoskamModelWarning

    flight = RoskamFlight(mach=0.5, delta_deg=0.0, reynolds=2e7)
    with pytest.warns(RoskamModelWarning):
        hinge_coefficients(GEO, AIRFOIL, flight)


def test_nose_type_changes_balance_effect():
    from dataclasses import replace

    flight = RoskamFlight(mach=0.5, delta_deg=5.0, reynolds=2e7)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        elliptic = hinge_coefficients(GEO, AIRFOIL, flight)
        round_ = hinge_coefficients(GEO, replace(AIRFOIL, nose_type="round"), flight)
    assert round_.values["Cha_balance_ratio"] < elliptic.values["Cha_balance_ratio"]
    assert round_.cha != pytest.approx(elliptic.cha)
    with pytest.raises(ValueError):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            hinge_coefficients(GEO, replace(AIRFOIL, nose_type="pointy"), flight)