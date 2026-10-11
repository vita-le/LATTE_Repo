# src/latte/analysis/roskam/case.py
"""Everything Roskam needs for ONE aileron, built once from a CPACSDocument."""
from dataclasses import dataclass

from latte.analysis.roskam.adapter import build_roskam_geometry
from latte.analysis.roskam.coefficients import RoskamAirfoil, RoskamGeometry
from latte.core.cpacs_airfoil import airfoil_properties_for_aileron


@dataclass(frozen=True)
class RoskamCase:
    geometry: RoskamGeometry
    airfoil: RoskamAirfoil
    aileron_area_m2: float          # S_f, used for the hinge moment
    aileron_chord_m: float          # reference chord of the hinge moment
    reynolds_length_m: float        # length for the Reynolds number (MAC)
    offset_nm: float = 0.0          # hinge moment at alpha = delta = 0 [N*m]
    label: str = ""

    def summary(self) -> dict:
        """Inputs in a flat dict, ready to show in a table."""
        g, a = self.geometry, self.airfoil
        reference = g.cf_reference_chord or g.mac
        return {
            "Span b [m]": g.b,
            "Aspect ratio [-]": g.aspect_ratio,
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
            "Nose type": a.nose_type,
        }


def build_case(
    doc,
    aileron: dict,
    use_local_chord_ratio: bool = True,
    nose_type: str = "elliptic",
    offset_nm: float = 0.0,
) -> RoskamCase:
    """Build the Roskam inputs of one aileron of an open CPACSDocument.

    The area of the aileron is the one declared in the CPACS (reference_area) if
    present, otherwise mean chord * span.
    """
    wing = next(
        (w for w in doc.wings if any(s["uid"] == aileron["parent_uid"] for s in w["segments"])),
        None,
    )
    if wing is None:
        raise ValueError(f"No wing contains the component segment {aileron['parent_uid']!r}")

    geometry, diagnostics = build_roskam_geometry(
        wing, doc.aileron_geometry(aileron), use_local_chord_ratio=use_local_chord_ratio
    )
    props = airfoil_properties_for_aileron(doc.path, wing["uid"], geometry.y_i, geometry.y_o)
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
    )