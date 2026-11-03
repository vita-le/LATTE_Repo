# tests/test_roskam_solver.py
import json
import math
import warnings
from pathlib import Path

import pytest

from latte.analysis.base import HingeMomentResult
from latte.analysis.roskam.case import RoskamCase, build_case
from latte.analysis.roskam.coefficients import RoskamAirfoil, RoskamGeometry
from latte.analysis.roskam.solver import RoskamSolver
from latte.analysis.runner import run_conditions
from latte.core.flight_state import FlightCondition, build_conditions

DATA = json.loads((Path(__file__).parent / "data" / "roskam_fa18_cases.json").read_text())
GEO = RoskamGeometry(**DATA["geometry"])
AIRFOIL = RoskamAirfoil(**DATA["airfoil"])
CASE = RoskamCase(
    geometry=GEO, airfoil=AIRFOIL,
    aileron_area_m2=DATA["hinge_moment"]["s_f"], aileron_chord_m=GEO.c_aileron,
    reynolds_length_m=GEO.mac, offset_nm=DATA["hinge_moment"]["offset_nm"], label="F18",
)


def fa18_conditions():
    return [
        FlightCondition(c["mach"], c["altitude_m"], c["alpha_deg"], 0.0, c["delta_deg"])
        for c in DATA["cases"]
    ]


def test_solver_reproduces_the_486_matlab_cases():
    results = run_conditions(RoskamSolver(CASE), fa18_conditions())
    assert len(results) == 486 and all(r.ok for r in results)
    worst_cha = worst_chd = worst_moment = 0.0
    for result, case in zip(results, DATA["cases"]):
        exp = case["expected"]
        worst_cha = max(worst_cha, abs(result.cha - exp["Cha"]) / abs(exp["Cha"]))
        worst_chd = max(worst_chd, abs(result.chd - exp["Chd"]) / abs(exp["Chd"]))
        worst_moment = max(worst_moment, abs(result.hinge_moment_nm - exp["Ma"]))
    # Differences come from the atmosphere model (Re 0.1-0.2% higher in MATLAB)
    assert worst_cha < 5e-4                         # measured: 1.4e-4
    assert worst_chd < 2e-4                         # measured: 3.7e-5
    assert worst_moment < 6.0                       # N*m, measured 3.5 on moments up to +-5800


def test_result_carries_details_and_warnings():
    result = RoskamSolver(CASE).run(FlightCondition(0.6, 7620.0, 2.0, 0.0, 10.0))
    assert result.method == "Roskam"
    assert result.details["Reynolds"] > 1e7
    assert "Cha_theory" in result.details
    # Phi_TE = 0 in this dataset triggers the thickness-correction warning
    assert any("thickness correction" in message for message in result.warnings)


def test_supersonic_condition_is_an_error_not_a_crash():
    conditions = [
        FlightCondition(0.5, 0.0, 0.0), FlightCondition(1.2, 0.0, 0.0), FlightCondition(0.7, 0.0, 0.0)
    ]
    results = run_conditions(RoskamSolver(CASE), conditions)
    assert [r.ok for r in results] == [True, False, True]
    assert "subsonic" in results[1].error
    with pytest.raises(ValueError):
        RoskamSolver(CASE).run(conditions[1])


def test_runner_reports_progress_and_can_be_cancelled():
    conditions = build_conditions((0.3, 0.6, 4), 0.0, 2.0, 5.0)
    seen = []
    run_conditions(RoskamSolver(CASE), conditions, progress_cb=lambda d, t: seen.append((d, t)))
    assert seen == [(1, 4), (2, 4), (3, 4), (4, 4)]

    stop_after = {"n": 0}

    def cancel():
        stop_after["n"] += 1
        return stop_after["n"] > 2

    assert len(run_conditions(RoskamSolver(CASE), conditions, should_cancel=cancel)) == 2


def test_derivative_signs_and_offset():
    solver = RoskamSolver(CASE)
    result = solver.run(FlightCondition(0.5, 0.0, 0.0, 0.0, 0.0))
    assert result.cha < 0 and result.chd < 0           # usual sign of hinge-moment derivatives
    assert result.hinge_moment_nm == pytest.approx(-400.0)     # only the offset at alpha = delta = 0


def test_failed_result_helper():
    cond = FlightCondition(0.5, 0.0, 0.0)
    failed = HingeMomentResult.failed("X", cond, "boom")
    assert not failed.ok and failed.error == "boom" and failed.hinge_moment_nm is None


# ---- build_case with a fake document (no TiGL needed) ---------------------------
class FakeDoc:
    def __init__(self, path, wing, aileron_geometry):
        self.path, self.wings, self._geometry = path, [wing], aileron_geometry

    def aileron_geometry(self, aileron):
        return self._geometry


def make_doc(tmp_path, hinge=0.25, reference_area=None, model_area=None):
    from test_cpacs_airfoil import naca_points
    from test_roskam_adapter import aileron as aileron_geometry
    from test_roskam_adapter import make_wing

    x, z = naca_points(0.10)
    ref = f"<reference><area>{model_area}</area></reference>" if model_area else ""
    xml = (f'<cpacs><vehicles><aircraft><model uID="M">{ref}<wings><wing uID="w"><sections>'
           f'<section uID="a"><transformation><translation><y>0</y></translation></transformation>'
           f'<elements><element uID="ae"><airfoilUID>P</airfoilUID></element></elements></section>'
           f'<section uID="b"><transformation><translation><y>5</y></translation></transformation>'
           f'<elements><element uID="be"><airfoilUID>P</airfoilUID></element></elements></section>'
           f'</sections></wing></wings></model></aircraft><profiles><wingAirfoils>'
           f'<wingAirfoil uID="P"><pointList><x>{x}</x><y>0</y><z>{z}</z></pointList></wingAirfoil>'
           f'</wingAirfoils></profiles></vehicles></cpacs>')
    path = tmp_path / "wing.xml"
    path.write_text(xml)
    wing = make_wing()
    wing["uid"] = "w"
    aileron = {"uid": "AIL", "parent_uid": "seg", "reference_area": reference_area}
    return FakeDoc(path, wing, aileron_geometry(3.0, 4.5, 0.0, 0.6, 0.4, hinge=hinge)), aileron


def test_build_case_and_run(tmp_path):
    doc, aileron = make_doc(tmp_path)
    case = build_case(doc, aileron)
    assert case.label == "AIL"
    assert case.aileron_area_m2 == pytest.approx(0.5 * 1.5)           # mean chord * span
    assert case.airfoil.t_c == pytest.approx(0.10, abs=2e-3)
    assert case.geometry.cf_reference_chord == pytest.approx(1.25)    # mean local chord at y = 3 and 4.5
    assert case.summary()["Hinge (fraction of aileron chord)"] == pytest.approx(0.25)
    result = RoskamSolver(case).run(FlightCondition(0.3, 0.0, 2.0, 0.0, 5.0))
    assert result.ok and math.isfinite(result.hinge_moment_nm)


def test_declared_aileron_area_is_used_when_present(tmp_path):
    doc, aileron = make_doc(tmp_path, reference_area=1.135)
    assert build_case(doc, aileron).aileron_area_m2 == pytest.approx(1.135)


def test_aileron_without_balance_gives_a_clear_error(tmp_path):
    doc, aileron = make_doc(tmp_path, hinge=0.03)
    results = run_conditions(RoskamSolver(build_case(doc, aileron)), [FlightCondition(0.3, 0.0, 2.0)])
    assert not results[0].ok
    assert "aerodynamic balance" in results[0].error


def test_unknown_component_segment(tmp_path):
    doc, aileron = make_doc(tmp_path)
    aileron["parent_uid"] = "nowhere"
    with pytest.raises(ValueError):
        build_case(doc, aileron)


def test_reference_area_and_hinge_thickness_options(tmp_path):
    from latte.core.airfoil import thickness_ratio_at
    from latte.core.cpacs_airfoil import read_airfoil_points

    doc, aileron = make_doc(tmp_path, model_area=20.0)
    default = build_case(doc, aileron, configuration="M")
    assert default.geometry.aspect_ratio == pytest.approx(100.0 / 20.0)           # b^2 / S_ref
    assert default.aspect_ratio_source == "CPACS reference area"
    geometric = build_case(doc, aileron, use_reference_area=False)
    assert geometric.geometry.aspect_ratio == pytest.approx(100.0 / 15.0)
    assert geometric.aspect_ratio_source == "wing geometry"

    # hinge-line thickness: airfoil thickness at the hinge chord fraction x local chord (1.25 m)
    xi = 1 - 0.75 * default.geometry.c_aileron / 1.25
    expected = thickness_ratio_at(*read_airfoil_points(doc.path, "P"), xi) * 1.25
    assert default.geometry.hinge_thickness_m == pytest.approx(expected)
    matlab = build_case(doc, aileron, hinge_thickness="matlab")
    assert matlab.geometry.hinge_thickness_m is None
    summary = default.summary()
    assert summary["  (thickness from)"] == "airfoil at the hinge line"
    assert matlab.summary()["  (thickness from)"].startswith("t/c x aileron chord")
    with pytest.raises(ValueError):
        build_case(doc, aileron, hinge_thickness="nope")


def test_no_reference_area_in_the_file_falls_back_to_the_geometry(tmp_path):
    doc, aileron = make_doc(tmp_path)                  # no <reference> in the model
    case = build_case(doc, aileron)
    assert case.geometry.aspect_ratio == pytest.approx(100.0 / 15.0)
    assert case.aspect_ratio_source == "wing geometry"