from pathlib import Path

from src.core.WingGeo import open_cpacs
from src.core.aileron import (
    extract_ailerons,
    extract_aileron_geometry,
)


ROOT = Path(__file__).resolve().parents[1]

CPACS_FILE = ROOT / "examples" / "DLH_CPACS.xml"
CONFIGURATION = "AircraftModel"


def main():

    tigl, tixi = open_cpacs(
        CPACS_FILE,
        CONFIGURATION,
    )

    ailerons = extract_ailerons(
        tigl,
        CPACS_FILE,
    )

    print("=" * 80)
    print("AILERON GEOMETRY TEST")
    print("=" * 80)

    for aileron in ailerons:

        geometry = extract_aileron_geometry(
            tigl,
            aileron,
        )

        print("\n" + "-" * 80)
        print(f"UID: {geometry['uid']}")
        print("-" * 80)

        print("\nInner:")
        print(
            "  LE:",
            geometry["inner"]["leading_edge"],
        )
        print(
            "  Hinge:",
            geometry["inner"]["hinge"],
        )
        print(
            "  TE:",
            geometry["inner"]["trailing_edge"],
        )

        print("\nOuter:")
        print(
            "  LE:",
            geometry["outer"]["leading_edge"],
        )
        print(
            "  Hinge:",
            geometry["outer"]["hinge"],
        )
        print(
            "  TE:",
            geometry["outer"]["trailing_edge"],
        )


if __name__ == "__main__":
    main()