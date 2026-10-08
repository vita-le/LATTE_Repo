# scripts/show_roskam_inputs.py
"""Print the Roskam inputs derived from the CPACS geometry, to check them by eye."""
from pathlib import Path

from latte.analysis.roskam.adapter import build_roskam_geometry
from latte.core.cpacs_document import CPACSDocument

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
FILES = {"cs23_base.xml": "AircraftModel", "DLH_CPACS.xml": "AircraftModel"}

for name, configuration in FILES.items():
    with CPACSDocument(EXAMPLES / name, configuration) as doc:
        for aileron in doc.ailerons:
            wing = next(w for w in doc.wings
                        if any(s["uid"] == aileron["parent_uid"] for s in w["segments"]))
            geo, diag = build_roskam_geometry(wing, doc.aileron_geometry(aileron))
            print("=" * 70)
            print(f"{name}  aileron {aileron['uid']}  (wing {wing['uid']})")
            print(f"  b={geo.b:.3f} m  S={diag['planform_area_m2']:.3f} m2 "
                  f"(CPACS area {diag['cpacs_wing_area_m2']:.3f})  AR={geo.aspect_ratio:.3f}  "
                  f"mirrored={diag['mirrored_wing']}")
            print(f"  MAC={geo.mac:.3f} m  sweep c/4={geo.lambda_c4_deg:.2f} deg  "
                  f"sweep hinge={geo.lambda_hl_deg:.2f} deg")
            print(f"  y_i={geo.y_i:.3f}  y_o={geo.y_o:.3f}  c_aileron={geo.c_aileron:.3f} m  "
                  f"hinge={geo.hinge:.3f}  area={diag['aileron_area_m2']:.3f} m2")
            print(f"  cf_ratio: c_ail/MAC={diag['cf_ratio_mac']:.3f}  "
                  f"c_ail/local chord={diag['cf_ratio_local']:.3f}  "
                  f"(local chord {diag['local_wing_chord_m']:.3f} m)")
            print(f"  cb/cf={diag['cb_over_cf']:.3f}")