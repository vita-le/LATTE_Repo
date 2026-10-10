# src/latte/core/cpacs_airfoil.py
"""Read airfoil contours from the profiles section of a CPACS file."""
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from latte.core.airfoil import AirfoilProperties, airfoil_properties


def _local(tag):
    """Tag name without XML namespace."""
    return tag.rsplit("}", 1)[-1]


def _child(element, name):
    for child in element:
        if _local(child.tag) == name:
            return child
    return None


def parse_vector(text):
    """'1.0;0.95;0.9' -> [1.0, 0.95, 0.9]"""
    return [float(v) for v in text.replace("\n", " ").split(";") if v.strip()]


def _airfoil_elements(path):
    root = ET.parse(str(Path(path))).getroot()
    return {
        el.get("uID"): el
        for el in root.iter()
        if _local(el.tag) == "wingAirfoil" and el.get("uID")
    }


def list_airfoil_uids(path):
    """uIDs of all wing airfoils defined in the file."""
    return sorted(_airfoil_elements(path))


def read_airfoil_points(path, airfoil_uid):
    """Return (x, z) lists of the contour of a wing airfoil (chord-normalised in CPACS)."""
    airfoils = _airfoil_elements(path)
    if airfoil_uid not in airfoils:
        raise KeyError(f"Airfoil {airfoil_uid!r} is not defined in {Path(path).name}")
    point_list = _child(airfoils[airfoil_uid], "pointList")
    if point_list is None:
        raise NotImplementedError(
            f"Airfoil {airfoil_uid!r} is not defined by a point list (e.g. CST): not supported yet"
        )
    x_el, z_el = _child(point_list, "x"), _child(point_list, "z")
    if x_el is None or z_el is None or not x_el.text or not z_el.text:
        raise ValueError(f"Airfoil {airfoil_uid!r} has an incomplete point list")
    x, z = parse_vector(x_el.text), parse_vector(z_el.text)
    if len(x) != len(z):
        raise ValueError(f"Airfoil {airfoil_uid!r}: x and z have different lengths")
    return x, z


def cpacs_airfoil_properties(path, airfoil_uid) -> AirfoilProperties:
    """t/c and trailing-edge angles of an airfoil defined in a CPACS file."""
    x, z = read_airfoil_points(path, airfoil_uid)
    return airfoil_properties(x, z)


# ---------------------------------------------------------------------------
# Which airfoil is at a given spanwise position of a wing
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class WingSection:
    y: float                    # spanwise position of the section [m]
    airfoil_uid: str


def _translation_y(element):
    """y of <transformation><translation> of an element (0.0 if missing)."""
    transformation = _child(element, "transformation")
    translation = _child(transformation, "translation") if transformation is not None else None
    y = _child(translation, "y") if translation is not None else None
    return float(y.text) if y is not None and y.text and y.text.strip() else 0.0


def read_wing_sections(path, wing_uid):
    """Sections of a wing as [WingSection], sorted from root to tip.

    The position is wing translation + section translation + element translation
    (y only: wing rotations are not considered).
    """
    root = ET.parse(str(Path(path))).getroot()
    wing = next(
        (el for el in root.iter() if _local(el.tag) == "wing" and el.get("uID") == wing_uid),
        None,
    )
    if wing is None:
        raise KeyError(f"Wing {wing_uid!r} is not defined in {Path(path).name}")
    sections_el = _child(wing, "sections")
    if sections_el is None:
        raise ValueError(f"Wing {wing_uid!r} has no sections")

    wing_y = _translation_y(wing)
    sections = []
    for section in sections_el:
        if _local(section.tag) != "section":
            continue
        elements = _child(section, "elements")
        element = next((e for e in elements if _local(e.tag) == "element"), None) if elements is not None else None
        airfoil = _child(element, "airfoilUID") if element is not None else None
        if airfoil is None or not airfoil.text:
            continue
        y = wing_y + _translation_y(section) + _translation_y(element)
        sections.append(WingSection(y=y, airfoil_uid=airfoil.text.strip()))
    if len(sections) < 1:
        raise ValueError(f"Wing {wing_uid!r}: no section with an airfoil found")
    return sorted(sections, key=lambda s: s.y)


def _interpolate(a: AirfoilProperties, b: AirfoilProperties, f: float) -> AirfoilProperties:
    mix = lambda u, v: (1 - f) * u + f * v
    return AirfoilProperties(
        t_c=mix(a.t_c, b.t_c),
        phi_te_1_deg=mix(a.phi_te_1_deg, b.phi_te_1_deg),
        phi_te_2_deg=mix(a.phi_te_2_deg, b.phi_te_2_deg),
    )


def airfoil_properties_at(path, wing_uid, y) -> AirfoilProperties:
    """t/c and TE angles at spanwise position y (linear between the two sections around it)."""
    sections = read_wing_sections(path, wing_uid)
    props = {
        uid: cpacs_airfoil_properties(path, uid)
        for uid in {s.airfoil_uid for s in sections}
    }
    if len(sections) == 1 or y <= sections[0].y:
        return props[sections[0].airfoil_uid]
    if y >= sections[-1].y:
        return props[sections[-1].airfoil_uid]
    for inner, outer in zip(sections, sections[1:]):
        if inner.y <= y <= outer.y:
            f = 0.0 if outer.y == inner.y else (y - inner.y) / (outer.y - inner.y)
            return _interpolate(props[inner.airfoil_uid], props[outer.airfoil_uid], f)
    raise AssertionError("unreachable")


def airfoil_properties_for_aileron(path, wing_uid, y_i, y_o) -> AirfoilProperties:
    """Mean of the airfoil properties at the inboard and outboard edges of the aileron."""
    return _interpolate(
        airfoil_properties_at(path, wing_uid, y_i),
        airfoil_properties_at(path, wing_uid, y_o),
        0.5,
    )