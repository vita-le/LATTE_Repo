# src/latte/core/cpacs_airfoil.py
"""Read airfoil contours from the profiles section of a CPACS file."""
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from latte.core.airfoil import AirfoilProperties, airfoil_properties, thickness_ratio_at


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


def _cst_surface(psi, n1, n2, coefficients):
    """Kulfan CST: z(psi) = psi^N1 (1-psi)^N2 * sum_i B_i C(n,i) psi^i (1-psi)^(n-i)."""
    n = len(coefficients) - 1
    shape = sum(
        b * math.comb(n, i) * psi ** i * (1 - psi) ** (n - i)
        for i, b in enumerate(coefficients)
    )
    return psi ** n1 * (1 - psi) ** n2 * shape


def _cst_contour(cst, airfoil_uid):
    """Contour (TE -> upper -> LE -> lower -> TE) of a CPACS <cst2D> definition.

    Both coefficient vectors are positive in CPACS: the lower surface is mirrored
    (z_lower = -CST). trailingEdgeThickness is split equally between both surfaces.
    """
    def number(name, default=None):
        el = _child(cst, name)
        if el is None or not el.text or not el.text.strip():
            if default is None:
                raise ValueError(f"Airfoil {airfoil_uid!r}: cst2D has no <{name}>")
            return default
        return float(el.text)

    def vector(name):
        el = _child(cst, name)
        if el is None or not el.text:
            raise ValueError(f"Airfoil {airfoil_uid!r}: cst2D has no <{name}>")
        return parse_vector(el.text)

    upper_b, lower_b = vector("upperB"), vector("lowerB")
    psi_el = _child(cst, "psi")
    if psi_el is not None and psi_el.text and psi_el.text.strip():
        psi = np.sort(np.array(parse_vector(psi_el.text)))
    else:
        psi = 0.5 * (1 - np.cos(np.linspace(0, math.pi, 201)))       # cosine spacing
    te = number("trailingEdgeThickness", 0.0)

    z_upper = _cst_surface(psi, number("upperN1"), number("upperN2"), upper_b) + psi * te / 2
    z_lower = -_cst_surface(psi, number("lowerN1"), number("lowerN2"), lower_b) - psi * te / 2
    x = np.concatenate([psi[::-1], psi[1:]])
    z = np.concatenate([z_upper[::-1], z_lower[1:]])
    return x.tolist(), z.tolist()


def read_airfoil_points(path, airfoil_uid):
    """Return (x, z) lists of the contour of a wing airfoil (chord-normalised in CPACS).

    Supports <pointList> and Kulfan <cst2D> definitions.
    """
    airfoils = _airfoil_elements(path)
    if airfoil_uid not in airfoils:
        raise KeyError(f"Airfoil {airfoil_uid!r} is not defined in {Path(path).name}")
    element = airfoils[airfoil_uid]

    point_list = _child(element, "pointList")
    if point_list is None:
        cst = _child(element, "cst2D")
        if cst is not None:
            return _cst_contour(cst, airfoil_uid)
        raise NotImplementedError(
            f"Airfoil {airfoil_uid!r} has neither a pointList nor a cst2D: not supported"
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


def thickness_ratio_for_aileron(path, wing_uid, y_i, y_o, xi) -> float:
    """Airfoil thickness / chord at the chord fraction xi, averaged over the aileron span.

    Like airfoil_properties_for_aileron: the airfoil is blended linearly between the two wing
    sections around each edge of the aileron, then inboard and outboard values are averaged.
    """
    sections = read_wing_sections(path, wing_uid)
    ratios = {
        uid: thickness_ratio_at(*read_airfoil_points(path, uid), xi)
        for uid in {s.airfoil_uid for s in sections}
    }

    def at(y):
        if len(sections) == 1 or y <= sections[0].y:
            return ratios[sections[0].airfoil_uid]
        if y >= sections[-1].y:
            return ratios[sections[-1].airfoil_uid]
        for inner, outer in zip(sections, sections[1:]):
            if inner.y <= y <= outer.y:
                f = 0.0 if outer.y == inner.y else (y - inner.y) / (outer.y - inner.y)
                return (1 - f) * ratios[inner.airfoil_uid] + f * ratios[outer.airfoil_uid]
        raise AssertionError("unreachable")

    return 0.5 * (at(y_i) + at(y_o))