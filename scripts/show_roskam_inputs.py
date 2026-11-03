# scripts/show_roskam_inputs.py
"""Print the Roskam inputs derived from a CPACS file, next to the MATLAB values.

Usage:
  python scripts/show_roskam_inputs.py examples/F18SRA_fixed.xml [configuration]
"""
import math
import sys
import warnings
from pathlib import Path

from latte.analysis.roskam.adapter import build_roskam_geometry
from latte.core.cpacs_airfoil import airfoil_properties_for_aileron, read_wing_sections
from latte.core.cpacs_document import CPACSDocument
from latte.core.cpacs_reference import read_reference_area

# F/A-18 SRA values inferred from the MATLAB loop (Results_LOOP_SUB.mat)
MATLAB_REFERENCE = {
    "b [m]": 12.31,
    "AR [-]": 12.31 ** 2 / 37.16,
    "sweep c/4 [deg]": 20.0,
    "sweep hinge [deg]": 17.577,
    "y_i [m]": 4.0300,
    "y_o [m]": 5.8700,
    "c_aileron [m]": 0.61685,
    "hinge [-]": 0.25,
    "MAC [m]": 3.0187,
    "t/c [-]": 0.10,
}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    configuration = sys.argv[2] if len(sys.argv) > 2 else None

    with CPACSDocument(path, configuration) as doc:
        if not doc.ailerons:
            sys.exit("No ailerons in this file.")
        for aileron in doc.ailerons:
            wing = next(
                w for w in doc.wings
                if any(s["uid"] == aileron["parent_uid"] for s in w["segments"])
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                reference_area = read_reference_area(path, configuration)
                geo, diag = build_roskam_geometry(
                    wing, doc.aileron_geometry(aileron), reference_area=reference_area)
            airfoil = airfoil_properties_for_aileron(path, wing["uid"], geo.y_i, geo.y_o)

            print("=" * 72)
            print(f"{path.name}  aileron {aileron['uid']}  (wing {wing['uid']})")
            print("  wing sections:", [(round(s.y, 3), s.airfoil_uid)
                                       for s in read_wing_sections(path, wing["uid"])])
            rows = {
                "b [m]": geo.b,
                "AR [-]": geo.aspect_ratio,
                "sweep c/4 [deg]": geo.lambda_c4_deg,
                "sweep hinge [deg]": geo.lambda_hl_deg,
                "y_i [m]": geo.y_i,
                "y_o [m]": geo.y_o,
                "c_aileron [m]": geo.c_aileron,
                "hinge [-]": geo.hinge,
                "MAC [m]": geo.mac,
                "t/c [-]": airfoil.t_c,
            }
            compare = "F18" in path.name.upper()        # MATLAB values exist only for the F/A-18
            header = f"  {'quantity':20s}{'CPACS':>12s}"
            print(header + (f"{'MATLAB':>12s}{'diff':>10s}" if compare else ""))
            for name, value in rows.items():
                line = f"  {name:20s}{value:12.4f}"
                if compare:
                    ref = MATLAB_REFERENCE[name]
                    line += f"{ref:12.4f}{(value - ref) / abs(ref) * 100:+9.1f}%"
                print(line)
            print(f"  Phi_TE_1 = {airfoil.phi_te_1_deg:.2f} deg, Phi_TE_2 = {airfoil.phi_te_2_deg:.2f} deg"
                  + ("   (MATLAB loop: 0, 0)" if compare else ""))
            print(f"  AR = {geo.aspect_ratio:.4f}: " + (f"b^2 / S_ref with S_ref = {reference_area:.2f} m2 (CPACS reference area)" if reference_area else "from the wing geometry")
                  + f"; geometric AR = {diag['aspect_ratio_geometric']:.4f}")
            print(f"  S = {diag['planform_area_m2']:.3f} m2 (area from {diag['area_source']}), "
                  f"aileron area = {diag['aileron_area_m2']:.3f} m2")
            print(f"  cf/c: local chord = {diag['cf_ratio_local']:.3f} "
                  f"(local chord {diag['local_wing_chord_m']:.3f} m), c_ail/MAC = {diag['cf_ratio_mac']:.3f}")
            print(f"  cb/cf = {diag['cb_over_cf']:.3f}")


if __name__ == "__main__":
    main()