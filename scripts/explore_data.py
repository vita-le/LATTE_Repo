# scripts/explore_data.py
"""Print the structure of wing and aileron data for every example CPACS."""
from pathlib import Path

from latte.core.wing_geo import open_cpacs, extract_all_wings
from latte.core.aileron import extract_ailerons, extract_aileron_geometry

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
FILES = ["cs23_base.xml", "DLH_CPACS.xml", "F18SRA_cpacs.xml",
         "GripenECPACS.xml", "TEST_CPACS.xml"]


def describe(obj, indent=0, max_depth=2):
    """Print type and shape/keys of an object, recursively for dict/list."""
    pad = " " * indent
    if isinstance(obj, dict):
        print(f"{pad}dict with keys: {list(obj.keys())}")
        if max_depth > 0:
            for k, v in list(obj.items())[:4]:
                print(f"{pad}  [{k!r}] ->", end=" ")
                describe(v, indent + 4, max_depth - 1)
    elif isinstance(obj, (list, tuple)):
        print(f"{pad}{type(obj).__name__} of len {len(obj)}")
        if obj and max_depth > 0:
            print(f"{pad}  first item ->", end=" ")
            describe(obj[0], indent + 4, max_depth - 1)
    elif hasattr(obj, "shape"):
        print(f"{pad}array shape {obj.shape}")
    else:
        print(f"{pad}{type(obj).__name__}: {str(obj)[:60]}")

import traceback

for name in FILES:
    path = EXAMPLES / name
    print("=" * 70)
    print(name)
    tigl = tixi = None
    try:
        # open_cpacs returns (tigl, tixi); keep tixi alive while using tigl
        tigl, tixi = open_cpacs(str(path))

        wings = extract_all_wings(tigl)
        print("WINGS:", end=" ")
        describe(wings)

        ailerons = extract_ailerons(tigl, str(path))
        print("AILERONS:", end=" ")
        describe(ailerons)

        if ailerons:
            first = (ailerons[0] if isinstance(ailerons, (list, tuple))
                     else next(iter(ailerons.values())))
            print("AILERON GEOMETRY:", end=" ")
            describe(extract_aileron_geometry(tigl, first))
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        traceback.print_exc(limit=3)   # show where it failed
    finally:
        # Always release the handles, even after an error
        if tigl is not None:
            tigl.close()
        if tixi is not None:
            tixi.close()