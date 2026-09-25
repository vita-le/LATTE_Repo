import sys
from pathlib import Path

import matplotlib.pyplot as plt

from src.core.WingGeo import (
    DEFAULT_CPACS,
    open_cpacs,
    extract_all_wings,
)


def set_axes_equal(ax):
    """
    Make X, Y and Z axes use the same physical scale.

    This ensures that:
        1 m in X = 1 m in Y = 1 m in Z

    This is important for checking the actual proportions
    of the aircraft geometry.
    """
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    z_range = abs(z_limits[1] - z_limits[0])

    x_middle = sum(x_limits) / 2
    y_middle = sum(y_limits) / 2
    z_middle = sum(z_limits) / 2

    radius = 0.5 * max(x_range, y_range, z_range)

    ax.set_xlim3d(
        x_middle - radius,
        x_middle + radius
    )

    ax.set_ylim3d(
        y_middle - radius,
        y_middle + radius
    )

    ax.set_zlim3d(
        z_middle - radius,
        z_middle + radius
    )


def plot_wing_geometry(cpacs_file):
    """Plot all wing geometries contained in a CPACS file."""

    tigl, tixi = open_cpacs(cpacs_file)

    try:
        wings = extract_all_wings(tigl)

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection="3d")

        for wing in wings:

            wing_uid = wing["uid"]

            for segment in wing["segments"]:

                stations = segment["stations"]

                # -------------------------------------------------
                # Leading edge
                # -------------------------------------------------

                le_x = [
                    s["leading_edge"][0]
                    for s in stations
                ]

                le_y = [
                    s["leading_edge"][1]
                    for s in stations
                ]

                le_z = [
                    s["leading_edge"][2]
                    for s in stations
                ]

                # -------------------------------------------------
                # Trailing edge
                # -------------------------------------------------

                te_x = [
                    s["trailing_edge"][0]
                    for s in stations
                ]

                te_y = [
                    s["trailing_edge"][1]
                    for s in stations
                ]

                te_z = [
                    s["trailing_edge"][2]
                    for s in stations
                ]

                # Plot leading edge
                ax.plot(
                    le_x,
                    le_y,
                    le_z,
                    marker="o",
                    linewidth=2,
                    label=f"{wing_uid} LE",
                )

                # Plot trailing edge
                ax.plot(
                    te_x,
                    te_y,
                    te_z,
                    marker="o",
                    linewidth=2,
                    label=f"{wing_uid} TE",
                )

                # -------------------------------------------------
                # Chord lines
                # -------------------------------------------------

                for station in stations:

                    le = station["leading_edge"]
                    te = station["trailing_edge"]

                    ax.plot(
                        [le[0], te[0]],
                        [le[1], te[1]],
                        [le[2], te[2]],
                        linewidth=1,
                        alpha=0.5,
                    )

        # ---------------------------------------------------------
        # Axis labels
        # ---------------------------------------------------------

        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.set_zlabel("Z [m]")

        ax.set_title("CPACS Aircraft Geometry")

        # ---------------------------------------------------------
        # Equal physical scale
        # ---------------------------------------------------------

        set_axes_equal(ax)

        # ---------------------------------------------------------
        # Grid
        # ---------------------------------------------------------

        ax.grid(True)

        # ---------------------------------------------------------
        # View
        # ---------------------------------------------------------

        ax.view_init(
            elev=20,
            azim=-60,
        )

        ax.legend()

        plt.tight_layout()
        plt.show()

    finally:
        tigl.close()
        tixi.close()


def main():

    if len(sys.argv) > 1:
        cpacs = Path(sys.argv[1])
    else:
        cpacs = Path(DEFAULT_CPACS)

        print(
            f"Using default CPACS: {cpacs}"
        )

    if not cpacs.is_file():
        raise FileNotFoundError(
            f"CPACS file not found: {cpacs}"
        )

    plot_wing_geometry(cpacs)


if __name__ == "__main__":
    main()
