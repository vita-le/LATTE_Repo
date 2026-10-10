# tests/test_cpacs_airfoil.py
import pytest

from latte.core.cpacs_airfoil import (
    airfoil_properties_at,
    airfoil_properties_for_aileron,
    cpacs_airfoil_properties,
    list_airfoil_uids,
    parse_vector,
    read_airfoil_points,
    read_wing_sections,
)

# Profile copied from examples/cs23_base.xml (starts at the TE on the lower surface)
NACA0009_XML = """<?xml version="1.0"?>
<cpacs><vehicles><profiles><wingAirfoils>
  <wingAirfoil uID="NACA0009">
    <name>NACA0009 Airfoil</name>
    <pointList>
      <x mapType="vector">1.0;0.95;0.9;0.8;0.7;0.6;0.5;0.4;0.3;0.25;0.2;0.15;0.1;0.075;0.05;0.025;0.0125;0.005;0.0;0.005;0.0125;0.025;0.05;0.075;0.1;0.15;0.2;0.25;0.3;0.4;0.5;0.6;0.7;0.8;0.9;0.95;1.0</x>
      <y mapType="vector">0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0;0.0</y>
      <z mapType="vector">0.0;-0.00605;-0.01086;-0.01967;-0.02748;-0.03423;-0.03971;-0.04352;-0.04501;-0.04456;-0.04303;-0.04009;-0.03512;-0.0315;-0.02666;-0.01961;-0.0142;-0.0089;0.0;0.0089;0.0142;0.01961;0.02666;0.0315;0.03512;0.04009;0.04303;0.04456;0.04501;0.04352;0.03971;0.03423;0.02748;0.01967;0.01086;0.00605;0.0</z>
    </pointList>
  </wingAirfoil>
  <wingAirfoil uID="CST_PROFILE"><name>no point list</name></wingAirfoil>
</wingAirfoils></profiles></vehicles></cpacs>
"""


@pytest.fixture
def xml_file(tmp_path):
    path = tmp_path / "profiles.xml"
    path.write_text(NACA0009_XML)
    return path


def test_parse_vector():
    assert parse_vector("1.0;0.5;\n0.0") == [1.0, 0.5, 0.0]


def test_list_and_read(xml_file):
    assert list_airfoil_uids(xml_file) == ["CST_PROFILE", "NACA0009"]
    x, z = read_airfoil_points(xml_file, "NACA0009")
    assert len(x) == len(z) == 37


def test_naca0009_properties(xml_file):
    props = cpacs_airfoil_properties(xml_file, "NACA0009")
    assert props.t_c == pytest.approx(0.09002, abs=1e-4)      # max half-thickness 0.04501
    assert 8.0 < props.phi_te_1_deg < 14.0                    # tan(Phi/2) close to t/c
    assert 8.0 < props.phi_te_2_deg < 14.0


def test_missing_and_unsupported_airfoil(xml_file):
    with pytest.raises(KeyError):
        read_airfoil_points(xml_file, "NOPE")
    with pytest.raises(NotImplementedError):
        read_airfoil_points(xml_file, "CST_PROFILE")


@pytest.mark.parametrize("name", ["cs23_base.xml", "DLH_CPACS.xml"])
def test_point_list_airfoils_of_example_files_are_plausible(examples_dir, name):
    checked = 0
    for uid in list_airfoil_uids(examples_dir / name):
        try:
            props = cpacs_airfoil_properties(examples_dir / name, uid)
        except NotImplementedError:
            continue                                  # not a point list
        assert 0.005 < props.t_c < 0.30, f"{uid}: t/c={props.t_c}"
        checked += 1
    assert checked >= 1


def test_constant_thickness_profile_has_zero_trailing_edge_angle(examples_dir):
    # The dorsal fin profile of cs23_base is a flat plate: parallel faces -> angle 0
    props = cpacs_airfoil_properties(examples_dir / "cs23_base.xml", "DorsalFinProfile")
    assert props.t_c == pytest.approx(0.02, abs=1e-6)
    assert props.phi_te_1_deg == pytest.approx(0.0, abs=1e-6)
    assert props.phi_te_2_deg == pytest.approx(0.0, abs=1e-6)


# ---- airfoil at a spanwise position -------------------------------------------
def test_cs23_wing_sections(examples_dir):
    sections = read_wing_sections(examples_dir / "cs23_base.xml", "wing")
    assert [s.airfoil_uid for s in sections] == ["NACA43018"] * 5
    assert [s.y for s in sections] == pytest.approx(
        [0.0, 0.78, 2.551533182, 4.784124717, 6.378832956], abs=1e-6
    )


def test_cs23_aileron_airfoil_is_naca43018(examples_dir):
    path = examples_dir / "cs23_base.xml"
    at_aileron = airfoil_properties_for_aileron(path, "wing", 3.894, 5.551)
    reference = cpacs_airfoil_properties(path, "NACA43018")
    assert at_aileron.t_c == pytest.approx(reference.t_c)
    assert at_aileron.phi_te_1_deg == pytest.approx(reference.phi_te_1_deg)


def naca_points(t):
    """Closed NACA 00xx contour as CPACS vectors (TE -> lower -> LE -> upper -> TE)."""
    import math

    import numpy as np

    beta = np.linspace(0, math.pi, 120)
    x = 0.5 * (1 - np.cos(beta))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2
                  + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    xs = np.concatenate([x[::-1], x[1:]])
    zs = np.concatenate([-yt[::-1], yt[1:]])
    return ";".join(f"{v:.6f}" for v in xs), ";".join(f"{v:.6f}" for v in zs)


@pytest.fixture
def tapered_wing_xml(tmp_path):
    def airfoil(uid, t):
        x, z = naca_points(t)
        return (f'<wingAirfoil uID="{uid}"><pointList><x>{x}</x><y>0</y>'
                f'<z>{z}</z></pointList></wingAirfoil>')

    def section(i, y, airfoil_uid):
        return (f'<section uID="S{i}"><transformation><scaling><y>1</y></scaling>'
                f'<rotation><y>0</y></rotation><translation><y>{y}</y></translation></transformation>'
                f'<elements><element uID="S{i}E"><airfoilUID>{airfoil_uid}</airfoilUID>'
                f'<transformation><translation><y>0</y></translation></transformation>'
                f'</element></elements></section>')

    xml = (f'<cpacs><vehicles><aircraft><model><wings>'
           f'<wing uID="w"><transformation><translation><y>1.0</y></translation></transformation>'
           f'<sections>{section(2, 4.0, "THICK")}{section(1, 0.0, "THIN")}</sections></wing>'
           f'</wings></model></aircraft>'
           f'<profiles><wingAirfoils>{airfoil("THIN", 0.06)}{airfoil("THICK", 0.12)}'
           f'</wingAirfoils></profiles></vehicles></cpacs>')
    path = tmp_path / "wing.xml"
    path.write_text(xml)
    return path


def test_sections_are_sorted_and_offset_by_wing_translation(tapered_wing_xml):
    sections = read_wing_sections(tapered_wing_xml, "w")
    assert [(s.y, s.airfoil_uid) for s in sections] == [(1.0, "THIN"), (5.0, "THICK")]


def test_airfoil_is_interpolated_between_sections(tapered_wing_xml):
    thin = cpacs_airfoil_properties(tapered_wing_xml, "THIN")
    thick = cpacs_airfoil_properties(tapered_wing_xml, "THICK")
    mid = airfoil_properties_at(tapered_wing_xml, "w", 3.0)       # halfway between y=1 and y=5
    assert mid.t_c == pytest.approx(0.5 * (thin.t_c + thick.t_c))
    assert mid.phi_te_1_deg == pytest.approx(0.5 * (thin.phi_te_1_deg + thick.phi_te_1_deg))
    # Outside the sections the nearest airfoil is used
    assert airfoil_properties_at(tapered_wing_xml, "w", 0.0).t_c == pytest.approx(thin.t_c)
    assert airfoil_properties_at(tapered_wing_xml, "w", 9.0).t_c == pytest.approx(thick.t_c)


def test_aileron_airfoil_is_the_mean_of_its_two_edges(tapered_wing_xml):
    thin = cpacs_airfoil_properties(tapered_wing_xml, "THIN")
    thick = cpacs_airfoil_properties(tapered_wing_xml, "THICK")
    # y_i = 2 (25%), y_o = 4 (75%) -> mean fraction 50%
    props = airfoil_properties_for_aileron(tapered_wing_xml, "w", 2.0, 4.0)
    assert props.t_c == pytest.approx(0.5 * (thin.t_c + thick.t_c))


def test_unknown_wing(tapered_wing_xml):
    with pytest.raises(KeyError):
        read_wing_sections(tapered_wing_xml, "nope")