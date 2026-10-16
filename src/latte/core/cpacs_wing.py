# src/latte/core/cpacs_wing.py
"""Rewrite the wing and aileron of a CPACS file from a few design numbers.

Used to build a standard-compliant CPACS of the F/A-18 SRA wing from Table 4.1 of the
thesis (trapezoidal wing + one aileron), starting from an existing CPACS so that the
rest of the file (fuselage, tail, profiles, ...) is kept. Requires lxml.
"""
import math
from dataclasses import dataclass

try:
    from lxml import etree
except ImportError:                      # lxml is only needed by this module
    etree = None


@dataclass(frozen=True)
class TrapezoidWing:
    root_chord: float            # [m]
    tip_chord: float             # [m]
    half_span: float             # [m], projected on the y axis
    sweep_c4_deg: float          # quarter-chord sweep, measured in the x-y plane
    dihedral_deg: float          # negative = anhedral


@dataclass(frozen=True)
class AileronSpec:
    y_i: float                   # inboard edge [m]
    y_o: float                   # outboard edge [m]
    cf_over_c: float             # aileron chord / local wing chord
    hinge_fraction: float        # hinge position, fraction of the aileron chord from its LE
    area_m2: float | None = None  # S_f, written in the (non-standard) MATLAB field


# Table 4.1 of the thesis (F/A-18 SRA)
F18_WING = TrapezoidWing(root_chord=4.04, tip_chord=1.68, half_span=6.155,
                         sweep_c4_deg=20.0, dihedral_deg=-3.0)
F18_AILERON = AileronSpec(y_i=4.03, y_o=5.87, cf_over_c=0.288, hinge_fraction=0.25, area_m2=1.135)


def _require_lxml():
    if etree is None:
        raise ImportError("lxml is required: pip install lxml")


def _num(value) -> str:
    return f"{value:.10g}"


def _get(parent, path):
    element = parent.find(path)
    if element is None:
        raise ValueError(f"<{path}> not found under <{parent.tag}>")
    return element


def _set_xyz(transformation, kind, values):
    block = transformation.find(kind)
    if block is None:
        block = etree.SubElement(transformation, kind)
    for name, value in zip("xyz", values):
        child = block.find(name)
        if child is None:
            child = etree.SubElement(block, name)
        child.text = _num(value)


def _find_by_uid(root, tag, uid):
    for element in root.iter(tag):
        if element.get("uID") == uid:
            return element
    raise KeyError(f"<{tag} uID={uid!r}> not found")


def _airfoil_element(uid, name, x, z):
    """<wingAirfoil> with the points ordered TE -> lower -> LE -> upper (openAD/TiGL style)."""
    if z[len(z) // 4] > 0:               # contour given upper-first: reverse it
        x, z = x[::-1], z[::-1]
    element = etree.Element("wingAirfoil", uID=uid)
    etree.SubElement(element, "name").text = name
    etree.SubElement(element, "description").text = "Imported from a .dat file by LATTE"
    points = etree.SubElement(element, "pointList")
    for axis, values in (("x", x), ("y", [0.0] * len(x)), ("z", z)):
        child = etree.SubElement(points, axis, mapType="vector")
        child.text = ";".join(repr(float(v)) for v in values)
    return element


def build_wing_model(
    root,
    wing_uid: str,
    aileron_uid: str,
    wing: TrapezoidWing = F18_WING,
    aileron: AileronSpec = F18_AILERON,
    airfoil: tuple | None = None,
    airfoil_uid: str = "N64210.DAT",
    keep_other_devices: bool = False,
    keep_matlab_fields: bool = True,
) -> dict:
    """Edit the CPACS tree in place; returns the numbers written (for printing/tests).

    airfoil: (name, x, z) of the profile used on both sections, or None to keep the
    airfoil UIDs of the sections as they are.
    """
    _require_lxml()
    wing_el = _find_by_uid(root, "wing", wing_uid)

    # ---- sections: only root and tip, trapezoidal planform with sweep and dihedral
    sections_el = _get(wing_el, "sections")
    sections = sections_el.findall("section")
    if len(sections) < 2:
        raise ValueError("The wing needs at least two sections")
    root_sec, tip_sec = sections[0], sections[-1]
    for middle in sections[1:-1]:
        sections_el.remove(middle)

    root_translation = _get(_get(root_sec, "transformation"), "translation")
    x0 = float(_get(root_translation, "x").text)
    z0 = float(_get(root_translation, "z").text)
    theta = wing.dihedral_deg
    x_tip = (x0 + 0.25 * wing.root_chord + wing.half_span * math.tan(math.radians(wing.sweep_c4_deg))
             - 0.25 * wing.tip_chord)
    z_tip = z0 + wing.half_span * math.tan(math.radians(theta))

    for section, chord, translation in (
        (root_sec, wing.root_chord, (x0, 0.0, z0)),
        (tip_sec, wing.tip_chord, (x_tip, wing.half_span, z_tip)),
    ):
        transformation = _get(section, "transformation")
        _set_xyz(transformation, "scaling", (chord, 1.0, chord))       # same scale on x and z
        _set_xyz(transformation, "rotation", (theta, 0.0, 0.0))
        _set_xyz(transformation, "translation", translation)
        if airfoil is not None:
            _get(section, "elements/element/airfoilUID").text = airfoil_uid

    # ---- one segment root -> tip, component segment over the same elements
    root_el = _get(root_sec, "elements/element").get("uID")
    tip_el = _get(tip_sec, "elements/element").get("uID")
    segments_el = _get(wing_el, "segments")
    segments = segments_el.findall("segment")
    for extra in segments[1:]:
        segments_el.remove(extra)
    segment = segments[0]
    segment.set("uID", f"{root_el}_{tip_el}")
    _get(segment, "name").text = "wingSegment0"
    _get(segment, "fromElementUID").text = root_el
    _get(segment, "toElementUID").text = tip_el

    cseg = _get(wing_el, "componentSegments/componentSegment")
    _get(cseg, "fromElementUID").text = root_el
    _get(cseg, "toElementUID").text = tip_el

    # ---- aileron: standard fields (eta, xsi, hinge) plus the MATLAB-specific ones
    controls = _get(cseg, "controlSurfaces")
    devices = _get(controls, "trailingEdgeDevices")
    device = next((d for d in devices if d.get("uID") == aileron_uid), None)
    if device is None:
        raise KeyError(f"trailingEdgeDevice {aileron_uid!r} not found")
    if not keep_other_devices:
        for other in [d for d in devices if d is not device]:
            devices.remove(other)
        for name in ("leadingEdgeDevices", "spoilers"):
            for container in controls.findall(name):
                controls.remove(container)

    xsi_le = 1.0 - aileron.cf_over_c
    hinge_xsi = xsi_le + aileron.hinge_fraction * (1.0 - xsi_le)
    eta = {"inner": aileron.y_i / wing.half_span, "outer": aileron.y_o / wing.half_span}
    y_field = {"inner": ("y_i", aileron.y_i), "outer": ("y_o", aileron.y_o)}
    for side in ("inner", "outer"):
        border = _get(device, f"outerShape/{side}Border")
        _get(border, "etaLE/eta").text = _num(eta[side])
        _get(border, "etaTE/eta").text = _num(eta[side])
        _get(border, "xsiLE/xsi").text = _num(xsi_le)
        _get(device, f"path/{side}HingePoint/hingeXsi").text = _num(hinge_xsi)
        field, value = y_field[side]
        custom = border.find(field)
        if keep_matlab_fields and custom is not None:
            inner = custom.find(field)
            (inner if inner is not None else custom).text = _num(value)
        elif not keep_matlab_fields and custom is not None:
            border.remove(custom)
    reference = device.find("reference_S")
    if reference is not None:
        if not keep_matlab_fields:
            device.remove(reference)
        elif aileron.area_m2 is not None:
            _get(reference, "S_f").text = _num(aileron.area_m2)

    # ---- the airfoil used on both sections
    if airfoil is not None:
        name, x, z = airfoil
        container = root.find(".//profiles/wingAirfoils")
        if container is None:
            raise ValueError("The file has no <wingAirfoils> section")
        for old in [a for a in container if a.get("uID") == airfoil_uid]:
            container.remove(old)
        container.append(_airfoil_element(airfoil_uid, name, list(x), list(z)))

    header_name = root.find("header/name")
    if header_name is not None:
        header_name.text = "F/A-18 SRA wing from Table 4.1 of the thesis (generated by LATTE)"

    return {
        "x_tip_le": x_tip, "z_tip": z_tip, "eta_inner": eta["inner"], "eta_outer": eta["outer"],
        "xsi_le": xsi_le, "hinge_xsi": hinge_xsi, "root_element": root_el, "tip_element": tip_el,
    }


def schema_errors(xml_path, xsd_path):
    """[(line, message)] of the schema validation errors of a CPACS file."""
    _require_lxml()
    schema = etree.XMLSchema(etree.parse(str(xsd_path)))
    schema.validate(etree.parse(str(xml_path)))
    return [(e.line, e.message) for e in schema.error_log]