# src/latte/analysis/roskam/case.py
"""Everything Roskam needs for ONE aileron, built once from a CPACSDocument."""
from dataclasses import dataclass, replace

from latte.analysis.roskam.adapter import build_roskam_geometry
from latte.analysis.roskam.coefficients import RoskamAirfoil, RoskamGeometry
from latte.core.cpacs_airfoil import airfoil_properties_for_aileron, thickness_ratio_for_aileron
from latte.core.cpacs_reference import read_reference_area


@dataclass(frozen=True)
class RoskamCase:
    geometry: RoskamGeometry
    airfoil: RoskamAirfoil
    aileron_area_m2: float          # S_f, used for the hinge moment
    aileron_chord_m: float          # reference chord of the hinge moment
    reynolds_length_m: float        # length for the Reynolds number (MAC)
    offset_nm: float = 0.0          # hinge moment at alpha = delta = 0 [N*m]
    label: str = ""
    aspect_ratio_source: str = "wing geometry"

    def summary(self) -> dict:
        """Inputs in a flat dict, ready to show in a table."""
        g, a = self.geometry, self.airfoil
        reference = g.cf_reference_chord or g.mac
        return {
            "Span b [m]": g.b,
            "Aspect ratio [-]": g.aspect_ratio,
            "  (AR from)": self.aspect_ratio_source,
            "Sweep c/4 [deg]": g.lambda_c4_deg,
            "Sweep hinge line [deg]": g.lambda_hl_deg,
            "Aileron y_i [m]": g.y_i,
            "Aileron y_o [m]": g.y_o,
            "Aileron mean chord [m]": g.c_aileron,
            "Aileron area S_f [m2]": self.aileron_area_m2,
            "Hinge (fraction of aileron chord)": g.hinge,
            "cf/c [-]": g.c_aileron / reference,
            "MAC [m]": g.mac,
            "t/c [-]": a.t_c,
            "Phi_TE_1 [deg]": a.phi_te_1_deg,
            "Phi_TE_2 [deg]": a.phi_te_2_deg,
            "Hinge-line thickness [m]": (
                g.hinge_thickness_m if g.hinge_thickness_m is not None else a.t_c * g.c_aileron),
            "  (thickness from)": ("airfoil at the hinge line" if g.hinge_thickness_m is not None
                                   else "t/c x aileron chord (MATLAB)"),
            "Nose type": a.nose_type,
        }


def build_case(
    doc,
    aileron: dict,
    use_local_chord_ratio: bool = True,
    nose_type: str = "elliptic",
    offset_nm: float = 0.0,
    use_reference_area: bool = True,
    hinge_thickness: str = "profile",
    configuration: str | None = None,
) -> RoskamCase:
    """Build the Roskam inputs of one aileron of an open CPACSDocument.

    use_reference_area: AR = b^2 / S_ref with the CPACS model/reference/area when the file
        declares it (as the MATLAB Geometry_Function); otherwise AR comes from the geometry.
    hinge_thickness: "profile" = absolute thickness of the airfoil at the hinge line (thesis
        definition); "matlab" = t/c x aileron chord (what Hinge_Coeff does).
    The area of the aileron is the one declared in the CPACS (reference_area) if present,
    otherwise mean chord * span.
    """
    if hinge_thickness not in ("profile", "matlab"):
        raise ValueError("hinge_thickness must be 'profile' or 'matlab'")
    wing = next(
        (w for w in doc.wings if any(s["uid"] == aileron["parent_uid"] for s in w["segments"])),
        None,
    )
    if wing is None:
        raise ValueError(f"No wing contains the component segment {aileron['parent_uid']!r}")

    reference_area = read_reference_area(doc.path, configuration) if use_reference_area else None
    geometry, diagnostics = build_roskam_geometry(
        wing, doc.aileron_geometry(aileron),
        use_local_chord_ratio=use_local_chord_ratio, reference_area=reference_area,
    )
    props = airfoil_properties_for_aileron(doc.path, wing["uid"], geometry.y_i, geometry.y_o)

    if hinge_thickness == "profile":
        # chord fraction of the hinge line: the aileron occupies the last c_aileron/c_local of the chord
        xi_hinge = 1.0 - (1.0 - geometry.hinge) * geometry.c_aileron / diagnostics["local_wing_chord_m"]
        ratio = thickness_ratio_for_aileron(doc.path, wing["uid"], geometry.y_i, geometry.y_o, xi_hinge)
        geometry = replace(geometry, hinge_thickness_m=ratio * diagnostics["local_wing_chord_m"])

    airfoil = RoskamAirfoil(
        t_c=props.t_c,
        phi_te_1_deg=props.phi_te_1_deg,
        phi_te_2_deg=props.phi_te_2_deg,
        nose_type=nose_type,
    )
    declared_area = aileron.get("reference_area")
    return RoskamCase(
        geometry=geometry,
        airfoil=airfoil,
        aileron_area_m2=float(declared_area) if declared_area else diagnostics["aileron_area_m2"],
        aileron_chord_m=geometry.c_aileron,
        reynolds_length_m=geometry.mac,
        offset_nm=offset_nm,
        label=aileron.get("uid", ""),
        aspect_ratio_source=("CPACS reference area" if reference_area is not None else "wing geometry"),
    )