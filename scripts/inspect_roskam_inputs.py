# scripts/inspect_roskam_inputs.py
"""Show which Roskam inputs the CPACS reader already provides."""
from pathlib import Path
from pprint import pprint

from latte.core.cpacs_document import CPACSDocument

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

for name in ("cs23_base.xml", "DLH_CPACS.xml"):
    print("=" * 70, name)
    with CPACSDocument(EXAMPLES / name, "AircraftModel") as doc:
        wing = doc.wings[0]
        print("wing keys:", list(wing.keys()))
        print("segment keys:", list(wing["segments"][0].keys()))
        for aileron in doc.ailerons:
            print("AILERON:")
            pprint(aileron, width=100, compact=True)