# scripts/inspect_geometry.py
"""Show wing stations and aileron 3D points, to design the Roskam adapter."""
from pathlib import Path
from pprint import pprint

from latte.core.cpacs_document import CPACSDocument

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

with CPACSDocument(EXAMPLES / "cs23_base.xml", "AircraftModel") as doc:
    for wing in doc.wings:
        print(f"WING {wing['uid']}: span={wing['span']:.4f} area={wing['area']:.4f} "
              f"segments={len(wing['segments'])}")
        seg = wing["segments"][0]
        print("  first segment:", seg["uid"], "- stations:", len(seg["stations"]))
        pprint(seg["stations"][:2], width=100, compact=True)

    print("\nAILERON 3D GEOMETRY:")
    pprint(doc.aileron_geometry(doc.ailerons[0]), width=100)