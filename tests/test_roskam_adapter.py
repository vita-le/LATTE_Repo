# tests/test_roskam_adapter.py
import math

import pytest

from latte.analysis.roskam.adapter import build_roskam_geometry, planform_from_wing


def make_wing(root_chord=2.0, tip_chord=1.0, half_span=5.0, le_sweep_deg=0.0, n=6):
    """Semi-wing with linear taper; leading edge swept by le_sweep_deg."""
    stations = []
    for i in range(n):
        eta = i / (n - 1)
        y = eta * half_span
        chord = root_chord + (tip_chord - root_chord) * eta
        x_le = y * math.tan(math.radians(le_sweep_deg))
        stations.append({
            "eta": eta, "chord": chord,
            "leading_edge": (x_le, y, 0.0), "trailing_edge": (x_le + chord, y, 0.0),
        })
    return {"span": 2 * half_span, "area": 0.0, "segments": [{"uid": "seg", "stations": stations}]}


def test_planform_of_tapered_wing():
    plan = planform_from_wing(make_wing())
    assert plan.mirrored
    assert plan.area == pytest.approx(15.0)                 # 2 * (2+1)/2 * 5
    assert plan.aspect_ratio == pytest.approx(100.0 / 15.0)
    # MAC = 2/3 * cr * (1 + lam + lam^2) / (1 + lam), lam = 0.5
    assert plan.mac == pytest.approx(2 / 3 * 2.0 * 1.75 / 1.5)


def test_quarter_chord_sweep():
    # LE swept 30 deg with taper: c/4 sweep from the geometry of the stations
    plan = planform_from_wing(make_wing(le_sweep_deg=30.0))
    dx = 5.0 * math.tan(math.radians(30)) + 0.25 * (1.0 - 2.0)
    assert plan.lambda_c4_deg == pytest.approx(math.degrees(math.atan2(dx, 5.0)))


def test_unmirrored_wing_is_detected():
    wing = make_wing()
    wing["span"] = 5.0                                      # TiGL span of a single semi-wing
    plan = planform_from_wing(wing)
    assert not plan.mirrored
    assert plan.area == pytest.approx(7.5)


def test_duplicate_stations_between_segments_are_ignored():
    wing = make_wing()
    wing["segments"].append({"uid": "seg2", "stations": wing["segments"][0]["stations"][-2:]})
    assert planform_from_wing(wing).area == pytest.approx(15.0)


def aileron(y_in, y_out, x_le_in, c_in, c_out, hinge=0.25, sweep_shift=0.0):
    def section(y, x_le, c):
        return {"leading_edge": (x_le, y, 0.0), "hinge": (x_le + hinge * c, y, 0.0),
                "trailing_edge": (x_le + c, y, 0.0)}
    return {"inner": section(y_in, x_le_in, c_in),
            "outer": section(y_out, x_le_in + sweep_shift, c_out)}


def test_aileron_inputs():
    geo, diag = build_roskam_geometry(make_wing(), aileron(3.0, 4.5, 0.0, 0.6, 0.4))
    assert geo.y_i == pytest.approx(3.0) and geo.y_o == pytest.approx(4.5)
    assert geo.c_aileron == pytest.approx(0.5)              # mean of 0.6 and 0.4
    assert geo.hinge == pytest.approx(0.25)
    assert diag["aileron_area_m2"] == pytest.approx(0.5 * 1.5)
    assert diag["cb_over_cf"] == pytest.approx(0.25 / 0.75)


def test_hinge_line_sweep():
    geo, _ = build_roskam_geometry(make_wing(), aileron(3.0, 4.0, 0.0, 0.5, 0.5, sweep_shift=0.5))
    # hinge x moves by 0.5 over 1.0 m of span
    assert geo.lambda_hl_deg == pytest.approx(math.degrees(math.atan2(0.5, 1.0)))


def test_cf_ratio_definition_switch():
    wing, ail = make_wing(), aileron(3.0, 4.0, 0.0, 0.5, 0.5)
    geo_mac, diag = build_roskam_geometry(wing, ail)
    geo_loc, _ = build_roskam_geometry(wing, ail, use_local_chord_ratio=True)
    assert geo_mac.cf_reference_chord is None
    # local chord at y = 3 -> 1.4, at y = 4 -> 1.2 : mean 1.3
    assert geo_loc.cf_reference_chord == pytest.approx(1.3)
    assert diag["cf_ratio_local"] == pytest.approx(0.5 / 1.3)


def test_invalid_aileron_order():
    with pytest.raises(ValueError):
        build_roskam_geometry(make_wing(), aileron(4.0, 3.0, 0.0, 0.5, 0.5))