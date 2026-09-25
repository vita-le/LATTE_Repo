from pathlib import Path

from src.core.WingGeo import open_cpacs
from src.core.aileron import extract_ailerons


ROOT = Path(__file__).resolve().parents[1]

CPACS_FILE = ROOT / "examples" / "DLH_CPACS.xml"
CONFIGURATION = "AircraftModel"


def point_to_tuple(point):
    """Convert a TiGL point to a simple (x, y, z) tuple."""
    return (
        float(point[0]),
        float(point[1]),
        float(point[2]),
    )


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
    print("AILERON 3D GEOMETRY")
    print("=" * 80)

    for aileron in ailerons:

        print("\n" + "-" * 80)
        print(f"UID: {aileron['uid']}")
        print(f"Parent: {aileron['parent_uid']}")
        print("-" * 80)

        parent_uid = aileron["parent_uid"]

        # ---------------------------------------------------------
        # Aileron spanwise limits
        # ---------------------------------------------------------

        inner_eta = aileron["span"]["inner_eta_le"]
        outer_eta = aileron["span"]["outer_eta_le"]

        # ---------------------------------------------------------
        # Leading-edge chordwise positions
        # ---------------------------------------------------------

        inner_xsi = aileron["chord"]["inner_xsi_le"]
        outer_xsi = aileron["chord"]["outer_xsi_le"]

        print(f"Inner eta: {inner_eta}")
        print(f"Outer eta: {outer_eta}")
        print(f"Inner xsi LE: {inner_xsi}")
        print(f"Outer xsi LE: {outer_xsi}")

        # ---------------------------------------------------------
        # Leading edge
        # ---------------------------------------------------------

        inner_le = tigl.wingComponentSegmentGetPoint(
            parent_uid,
            inner_eta,
            inner_xsi,
        )

        outer_le = tigl.wingComponentSegmentGetPoint(
            parent_uid,
            outer_eta,
            outer_xsi,
        )

        print("\nLeading-edge points:")

        print(
            "Inner:",
            point_to_tuple(inner_le),
        )

        print(
            "Outer:",
            point_to_tuple(outer_le),
        )

        # ---------------------------------------------------------
        # Hinge line
        # ---------------------------------------------------------

        hinge = aileron["hinge"]

        inner_hinge_xsi = hinge["inner_xsi"]
        outer_hinge_xsi = hinge["outer_xsi"]

        inner_hinge = tigl.wingComponentSegmentGetPoint(
            parent_uid,
            inner_eta,
            inner_hinge_xsi,
        )

        outer_hinge = tigl.wingComponentSegmentGetPoint(
            parent_uid,
            outer_eta,
            outer_hinge_xsi,
        )

        print("\nHinge points:")

        print(
            "Inner:",
            point_to_tuple(inner_hinge),
        )

        print(
            "Outer:",
            point_to_tuple(outer_hinge),
        )

        # ---------------------------------------------------------
        # Trailing edge
        # ---------------------------------------------------------

        inner_te = tigl.wingComponentSegmentGetPoint(
            parent_uid,
            inner_eta,
            1.0,
        )

        outer_te = tigl.wingComponentSegmentGetPoint(
            parent_uid,
            outer_eta,
            1.0,
        )

        print("\nTrailing-edge points:")

        print(
            "Inner:",
            point_to_tuple(inner_te),
        )

        print(
            "Outer:",
            point_to_tuple(outer_te),
        )

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        print("\nAileron geometry summary:")

        print(
            "Inner LE:",
            point_to_tuple(inner_le),
        )

        print(
            "Outer LE:",
            point_to_tuple(outer_le),
        )

        print(
            "Inner Hinge:",
            point_to_tuple(inner_hinge),
        )

        print(
            "Outer Hinge:",
            point_to_tuple(outer_hinge),
        )

        print(
            "Inner TE:",
            point_to_tuple(inner_te),
        )

        print(
            "Outer TE:",
            point_to_tuple(outer_te),
        )


if __name__ == "__main__":
    main()