from pathlib import Path

from src.core.WingGeo import (
    open_cpacs,
    extract_all_wings,
)

from src.core.aileron import (
    extract_ailerons,
    extract_aileron_geometry,
)

from src.visualization.plot_control_surface import (
    plot_wing_with_ailerons,
    plot_ailerons_top_view,
)


ROOT = Path(__file__).resolve().parents[1]

CPACS_FILE = ROOT / "examples" / "DLH_CPACS.xml"

CONFIGURATION = "AircraftModel"


def find_wing_for_ailerons(
    wings,
    ailerons,
):
    """
    Find the wing containing the component segment
    used by the ailerons.

    The aileron parent_uid refers to a component
    segment, not directly to a wing UID.
    """

    if not ailerons:

        raise ValueError(
            "No ailerons found."
        )

    aileron_parent_uids = {
        aileron["parent_uid"]
        for aileron in ailerons
    }

    for wing in wings:

        for segment in wing["segments"]:

            if segment["uid"] in aileron_parent_uids:

                return wing

    raise ValueError(
        "Could not find the wing containing "
        f"the aileron component segment(s): "
        f"{sorted(aileron_parent_uids)}"
    )


def main():

    tigl, tixi = open_cpacs(
        CPACS_FILE,
        CONFIGURATION,
    )

    try:

        # ======================================================
        # EXTRACT WINGS
        # ======================================================

        wings = extract_all_wings(
            tigl
        )

        print(
            f"Wings found: {len(wings)}"
        )

        for wing in wings:

            print(
                f"  Wing: {wing['uid']}"
            )

        # ======================================================
        # EXTRACT AILERONS
        # ======================================================

        ailerons = extract_ailerons(
            tigl,
            CPACS_FILE,
        )

        print(
            f"Ailerons found: {len(ailerons)}"
        )

        for aileron in ailerons:

            print(
                f"  Aileron: {aileron['uid']}"
            )

            print(
                f"    Parent component segment: "
                f"{aileron['parent_uid']}"
            )

        # ======================================================
        # FIND ASSOCIATED WING
        # ======================================================

        wing = find_wing_for_ailerons(
            wings,
            ailerons,
        )

        print()
        print(
            f"Wing associated with ailerons: "
            f"{wing['uid']}"
        )

        # ======================================================
        # EXTRACT AILERON GEOMETRY
        # ======================================================

        ailerons_geometry = []

        for aileron in ailerons:

            geometry = extract_aileron_geometry(
                tigl,
                aileron,
            )

            ailerons_geometry.append(
                geometry
            )

        # ======================================================
        # 3D PLOT
        # ======================================================

        plot_wing_with_ailerons(
            wing,
            ailerons_geometry,
            CONFIGURATION,
        )

        # ======================================================
        # 2D TOP VIEW
        # ======================================================

        plot_ailerons_top_view(
            wing,
            ailerons_geometry,
            CONFIGURATION,
        )

    finally:

        tigl.close()
        tixi.close()


if __name__ == "__main__":
    main()