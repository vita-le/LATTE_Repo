# tests/test_cpacs_wing.py
"""Builds the F/A-18 SRA model of the thesis from examples/F18SRA_cpacs.xml and checks it."""
import math

import numpy as np
import pytest

lxml_etree = pytest.importorskip("lxml.etree")

from latte.analysis.roskam.adapter import build_roskam_geometry          # noqa: E402
from latte.core.cpacs_wing import (                                      # noqa: E402
    F18_AILERON,
    F18_WING,
    build_wing_model,
    schema_errors,
)

# Elements the original (hand-edited) file already has and the CPACS schema does not know
KNOWN_NONSTANDARD = {"payload", "symmetric"}
MATLAB_FIELDS = {"y_i", "y_o", "reference_S"}


def synthetic_airfoil(t=0.10, n=80):
    beta = np.linspace(0, math.pi, n)
    x = 0.5 * (1 - np.cos(beta))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    xs = np.concatenate([x[::-1], x[1:]])
    zs = np.concatenate([yt[::-1], -yt[1:]])                 # upper surface first
    return "synthetic NACA 0010", xs.tolist(), zs.tolist()


@pytest.fixture(scope="module")
def paths(examples_dir):
    original = examples_dir / "F18SRA_cpacs.xml"
    schema = examples_dir / "cpacs_schema.xsd"
    if not original.exists() or not schema.exists():
        pytest.skip("examples/F18SRA_cpacs.xml or cpacs_schema.xsd not found")
    return original, schema


def generate(original, out, **kwargs):
    tree = lxml_etree.parse(str(original))
    summary = build_wing_model(tree.getroot(), "wing", "AileronUID", airfoil=synthetic_airfoil(), **kwargs)
    tree.write(str(out), xml_declaration=True, encoding="UTF-8")
    return summary


@pytest.fixture(scope="module")
def generated(paths, tmp_path_factory):
    original, _ = paths
    out = tmp_path_factory.mktemp("f18") / "F18SRA_thesis.xml"
    summary = generate(original, out)
    return out, summary


def wing_element(path):
    root = lxml_etree.parse(str(path)).getroot()
    return root, next(w for w in root.iter("wing") if w.get("uID") == "wing")


def test_two_sections_with_thesis_chords_and_sweep(generated):
    _, wing = wing_element(generated[0])
    sections = wing.findall("sections/section")
    assert len(sections) == 2
    values = []
    for section in sections:
        tr = section.find("transformation")
        values.append({k: [float(tr.find(f"{k}/{a}").text) for a in "xyz"]
                       for k in ("scaling", "rotation", "translation")})
    root_v, tip_v = values
    assert root_v["scaling"] == pytest.approx([4.04, 1.0, 4.04])         # t/c is the airfoil's
    assert tip_v["scaling"] == pytest.approx([1.68, 1.0, 1.68])
    assert tip_v["translation"][1] == pytest.approx(6.155)               # half span
    assert tip_v["translation"][2] - root_v["translation"][2] == pytest.approx(
        6.155 * math.tan(math.radians(-3.0)))                            # anhedral through z
    c4 = lambda v: v["translation"][0] + 0.25 * v["scaling"][0]
    assert math.degrees(math.atan((c4(tip_v) - c4(root_v)) / 6.155)) == pytest.approx(20.0)
    assert root_v["rotation"][0] == tip_v["rotation"][0] == -3.0


def test_segment_and_component_segment_are_consistent(generated):
    root, wing = wing_element(generated[0])
    elements = [e.get("uID") for e in wing.iter("element")]
    assert len(elements) == 2
    segments = wing.findall("segments/segment")
    assert len(segments) == 1
    assert [segments[0].find("fromElementUID").text, segments[0].find("toElementUID").text] == elements
    cseg = wing.find("componentSegments/componentSegment")
    assert [cseg.find("fromElementUID").text, cseg.find("toElementUID").text] == elements
    # every referenced element exists
    assert {e.text for e in wing.iter("fromElementUID", "toElementUID")} <= set(elements)


def test_aileron_uses_standard_fractions(generated):
    _, wing = wing_element(generated[0])
    device = next(d for d in wing.iter("trailingEdgeDevice") if d.get("uID") == "AileronUID")
    f = lambda path: float(device.find(path).text)
    for side, y in (("inner", 4.03), ("outer", 5.87)):
        eta = y / 6.155
        assert 0.0 <= eta <= 1.0
        assert f(f"outerShape/{side}Border/etaLE/eta") == pytest.approx(eta)
        assert f(f"outerShape/{side}Border/etaTE/eta") == pytest.approx(eta)
        assert f(f"outerShape/{side}Border/xsiLE/xsi") == pytest.approx(0.712)
        assert f(f"path/{side}HingePoint/hingeXsi") == pytest.approx(0.712 + 0.25 * 0.288)
    # MATLAB-specific fields kept, with the thesis values
    assert f("outerShape/innerBorder/y_i/y_i") == pytest.approx(4.03)
    assert f("outerShape/outerBorder/y_o/y_o") == pytest.approx(5.87)
    assert f("reference_S/S_f") == pytest.approx(1.135)


def test_other_control_surfaces_are_removed_unless_kept(paths, generated, tmp_path):
    _, wing = wing_element(generated[0])
    assert [d.get("uID") for d in wing.iter("trailingEdgeDevice")] == ["AileronUID"]
    assert not list(wing.iter("leadingEdgeDevice")) and not list(wing.iter("spoiler"))

    kept = tmp_path / "kept.xml"
    generate(paths[0], kept, keep_other_devices=True)
    _, wing_kept = wing_element(kept)
    assert len(list(wing_kept.iter("trailingEdgeDevice"))) == 3


def test_airfoil_is_defined_on_both_sections_lower_surface_first(generated):
    from latte.core.cpacs_airfoil import cpacs_airfoil_properties, read_airfoil_points

    root, wing = wing_element(generated[0])
    assert [a.text for a in wing.iter("airfoilUID")] == ["N64210.DAT"] * 2
    x, z = read_airfoil_points(generated[0], "N64210.DAT")
    assert z[len(z) // 4] < 0 < z[3 * len(z) // 4]
    assert cpacs_airfoil_properties(generated[0], "N64210.DAT").t_c == pytest.approx(0.10, abs=2e-3)


def test_schema_errors_are_only_the_known_nonstandard_elements(paths, generated):
    _, schema = paths
    names = lambda errors: {m.split("'")[1] for _, m in errors if "'" in m}
    original_errors = names(schema_errors(paths[0], schema))
    new_errors = names(schema_errors(generated[0], schema))
    assert new_errors <= KNOWN_NONSTANDARD | MATLAB_FIELDS
    assert new_errors <= original_errors                      # nothing new was broken


def test_without_matlab_fields_only_unrelated_schema_errors_remain(paths, tmp_path):
    out = tmp_path / "standard.xml"
    generate(paths[0], out, keep_matlab_fields=False)
    names = {m.split("'")[1] for _, m in schema_errors(out, paths[1]) if "'" in m}
    assert names <= KNOWN_NONSTANDARD


# ---- independent evaluation of the geometry (what TiGL computes for a 2-section wing) ----
def evaluate_geometry(path):
    """Stations and aileron points from the XML numbers: linear between root and tip sections."""
    root, wing = wing_element(path)
    sections = []
    for s in wing.findall("sections/section"):
        tr = s.find("transformation")
        get = lambda k: np.array([float(tr.find(f"{k}/{a}").text) for a in "xyz"])
        scaling, translation = get("scaling"), get("translation")
        sections.append((translation, translation + np.array([scaling[0], 0.0, 0.0])))
    (le0, te0), (le1, te1) = sections

    def le(eta): return (1 - eta) * le0 + eta * le1
    def te(eta): return (1 - eta) * te0 + eta * te1
    def point(eta, xsi): return le(eta) + xsi * (te(eta) - le(eta))

    stations = [{"eta": e, "chord": float(np.linalg.norm(te(e) - le(e))),
                 "leading_edge": tuple(le(e)), "trailing_edge": tuple(te(e))}
                for e in np.linspace(0, 1, 10)]
    span = 2 * float(le1[1] - le0[1])
    wing_dict = {"uid": "wing", "span": span, "area": 0.0, "segments": [{"uid": "seg", "stations": stations}]}

    device = next(d for d in wing.iter("trailingEdgeDevice") if d.get("uID") == "AileronUID")
    geo = {}
    for side in ("inner", "outer"):
        b = device.find(f"outerShape/{side}Border")
        eta, xsi = float(b.find("etaLE/eta").text), float(b.find("xsiLE/xsi").text)
        hinge = float(device.find(f"path/{side}HingePoint/hingeXsi").text)
        geo[side] = {"leading_edge": tuple(point(eta, xsi)), "hinge": tuple(point(eta, hinge)),
                     "trailing_edge": tuple(point(eta, 1.0))}
    return wing_dict, geo


def test_generated_geometry_reproduces_table_4_1_of_the_thesis(generated):
    wing, aileron = evaluate_geometry(generated[0])
    geometry, diag = build_roskam_geometry(wing, aileron)
    assert geometry.b == pytest.approx(12.31)
    assert geometry.lambda_c4_deg == pytest.approx(20.0, abs=0.01)
    assert geometry.y_i == pytest.approx(4.03, abs=0.01) and geometry.y_o == pytest.approx(5.87, abs=0.01)
    assert geometry.c_aileron == pytest.approx(0.61685, rel=3e-3)       # MATLAB loop value
    assert diag["aileron_area_m2"] == pytest.approx(1.135, rel=3e-3)    # Table 4.1: S_f
    assert diag["cf_ratio_local"] == pytest.approx(0.288, rel=2e-3)     # Table 4.1: cf/c
    assert geometry.hinge == pytest.approx(0.25, abs=1e-3)
    assert diag["planform_area_m2"] == pytest.approx(35.2, rel=5e-3)    # trapezoid, not 37.16


# ---- the bridge to the MATLAB cases, driven by the generated model ----------------------
def test_matlab_bridge_converges_to_the_regression(generated):
    import json
    from pathlib import Path

    from latte.analysis.roskam.case import RoskamCase
    from latte.analysis.roskam.coefficients import RoskamAirfoil
    from latte.analysis.roskam.validation import matlab_bridge
    from latte.core.airfoil import airfoil_properties

    data = json.loads((Path(__file__).parent / "data" / "roskam_fa18_cases.json").read_text())
    wing, aileron = evaluate_geometry(generated[0])
    geometry, diag = build_roskam_geometry(wing, aileron)
    props = airfoil_properties(*synthetic_airfoil()[1:])
    case = RoskamCase(
        geometry=geometry,
        airfoil=RoskamAirfoil(props.t_c, props.phi_te_1_deg, props.phi_te_2_deg),
        aileron_area_m2=diag["aileron_area_m2"], aileron_chord_m=geometry.c_aileron,
        reynolds_length_m=geometry.mac, offset_nm=-400.0,
    )
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rows = matlab_bridge(case, data)

    assert len(rows) == 7 and all(r.failed == 0 for r in rows)
    first, last = rows[0], rows[-1]
    assert first.cha_max_rel > 0.05                       # CPACS inputs differ from MATLAB's
    assert last.cha_max_rel < 5e-4 and last.chd_max_rel < 2e-4 and last.moment_max_abs < 6.0


def test_single_input_effects_are_isolated_and_reference_is_exact(generated):
    import json
    import warnings
    from pathlib import Path

    from latte.analysis.roskam.case import RoskamCase
    from latte.analysis.roskam.coefficients import RoskamAirfoil
    from latte.analysis.roskam.validation import single_input_effects
    from latte.core.airfoil import airfoil_properties

    data = json.loads((Path(__file__).parent / "data" / "roskam_fa18_cases.json").read_text())
    wing, aileron = evaluate_geometry(generated[0])
    geometry, diag = build_roskam_geometry(wing, aileron)
    props = airfoil_properties(*synthetic_airfoil()[1:])
    case = RoskamCase(geometry, RoskamAirfoil(props.t_c, props.phi_te_1_deg, props.phi_te_2_deg),
                      diag["aileron_area_m2"], geometry.c_aileron, geometry.mac, -400.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rows = single_input_effects(case, data)

    by_name = {r.step.split(" (")[0]: r for r in rows}
    reference = rows[0]
    assert reference.cha_max_rel < 5e-4 and reference.moment_max_abs < 6.0
    assert all(r.cha_max_rel >= reference.cha_max_rel - 1e-12 for r in rows)
    airfoil_row = by_name["airfoil from the file"]
    assert airfoil_row.cha_max_rel > 0.5                          # Phi_TE = 0 vs a real angle
    sweep_row = next(r for r in rows if r.step.startswith("hinge-line sweep"))
    assert sweep_row.cha_max_rel < 5e-4 and sweep_row.chd_max_rel > 0.02   # sweep only enters Chd