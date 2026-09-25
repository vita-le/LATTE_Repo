import matplotlib.pyplot as plt


def set_axes_equal(ax):
    """
    Make X, Y and Z axes use the same physical scale.

    This ensures that:
        1 m in X = 1 m in Y = 1 m in Z
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

    radius = 0.5 * max(
        x_range,
        y_range,
        z_range,
    )

    ax.set_xlim3d(
        x_middle - radius,
        x_middle + radius,
    )

    ax.set_ylim3d(
        y_middle - radius,
        y_middle + radius,
    )

    ax.set_zlim3d(
        z_middle - radius,
        z_middle + radius,
    )


def plot_wing_with_ailerons(
    wing,
    ailerons_geometry,
    configuration=None,
):
    """
    Plot only the wing associated with the ailerons.

    The wing is shown as a light wireframe.
    Ailerons and hinge lines are highlighted.

    Parameters
    ----------
    wing : dict
        Wing geometry from extract_wing().

    ailerons_geometry : list[dict]
        Aileron geometries from extract_aileron_geometry().

    configuration : str, optional
        CPACS configuration name.
    """

    fig = plt.figure(
        figsize=(12, 8)
    )

    ax = fig.add_subplot(
        111,
        projection="3d",
    )

    # ==========================================================
    # MAIN WING WIREFRAME
    # ==========================================================

    for segment in wing["segments"]:

        stations = segment["stations"]

        # Leading edge
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

        ax.plot(
            le_x,
            le_y,
            le_z,
            linewidth=0.8,
            alpha=0.35,
        )

        # Trailing edge
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

        ax.plot(
            te_x,
            te_y,
            te_z,
            linewidth=0.8,
            alpha=0.35,
        )

        # Chord lines
        for station in stations:

            le = station["leading_edge"]
            te = station["trailing_edge"]

            ax.plot(
                [le[0], te[0]],
                [le[1], te[1]],
                [le[2], te[2]],
                linewidth=0.5,
                alpha=0.20,
            )

    # ==========================================================
    # AILERONS
    # ==========================================================

    for aileron in ailerons_geometry:

        uid = aileron["uid"]

        inner = aileron["inner"]
        outer = aileron["outer"]

        inner_le = inner["leading_edge"]
        inner_hinge = inner["hinge"]
        inner_te = inner["trailing_edge"]

        outer_le = outer["leading_edge"]
        outer_hinge = outer["hinge"]
        outer_te = outer["trailing_edge"]

        # Aileron perimeter
        points = [
            inner_le,
            inner_hinge,
            inner_te,
            outer_te,
            outer_hinge,
            outer_le,
            inner_le,
        ]

        ax.plot(
            [p[0] for p in points],
            [p[1] for p in points],
            [p[2] for p in points],
            linewidth=2.5,
            marker="o",
            markersize=4,
            label=uid,
        )

        # Hinge line
        ax.plot(
            [inner_hinge[0], outer_hinge[0]],
            [inner_hinge[1], outer_hinge[1]],
            [inner_hinge[2], outer_hinge[2]],
            linewidth=3.5,
        )

        # Aileron leading edge
        ax.plot(
            [inner_le[0], outer_le[0]],
            [inner_le[1], outer_le[1]],
            [inner_le[2], outer_le[2]],
            linewidth=2,
        )

        # Aileron trailing edge
        ax.plot(
            [inner_te[0], outer_te[0]],
            [inner_te[1], outer_te[1]],
            [inner_te[2], outer_te[2]],
            linewidth=2,
        )

    # ==========================================================
    # AXES
    # ==========================================================

    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Z [m]")

    if configuration is not None:

        ax.set_title(
            f"CPACS Wing and Ailerons - {configuration}"
        )

    else:

        ax.set_title(
            "CPACS Wing and Ailerons"
        )

    set_axes_equal(ax)

    ax.grid(True)

    ax.view_init(
        elev=20,
        azim=-60,
    )

    ax.legend()

    plt.tight_layout()

    plt.show()


def plot_ailerons_top_view(
    wing,
    ailerons_geometry,
    configuration=None,
):
    """
    Plot the wing and ailerons in a 2D top view.

    The geometry is projected onto the X-Y plane.

    Parameters
    ----------
    wing : dict
        Wing geometry from extract_wing().

    ailerons_geometry : list[dict]
        Aileron geometries from extract_aileron_geometry().

    configuration : str, optional
        CPACS configuration name.
    """

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    # ==========================================================
    # MAIN WING WIREFRAME
    # ==========================================================

    for segment in wing["segments"]:

        stations = segment["stations"]

        # Leading edge
        le_x = [
            s["leading_edge"][0]
            for s in stations
        ]

        le_y = [
            s["leading_edge"][1]
            for s in stations
        ]

        ax.plot(
            le_x,
            le_y,
            linewidth=1.0,
            alpha=0.35,
        )

        # Trailing edge
        te_x = [
            s["trailing_edge"][0]
            for s in stations
        ]

        te_y = [
            s["trailing_edge"][1]
            for s in stations
        ]

        ax.plot(
            te_x,
            te_y,
            linewidth=1.0,
            alpha=0.35,
        )

        # Chord lines
        for station in stations:

            le = station["leading_edge"]
            te = station["trailing_edge"]

            ax.plot(
                [le[0], te[0]],
                [le[1], te[1]],
                linewidth=0.5,
                alpha=0.20,
            )

    # ==========================================================
    # AILERONS
    # ==========================================================

    for aileron in ailerons_geometry:

        uid = aileron["uid"]

        inner = aileron["inner"]
        outer = aileron["outer"]

        inner_le = inner["leading_edge"]
        inner_hinge = inner["hinge"]
        inner_te = inner["trailing_edge"]

        outer_le = outer["leading_edge"]
        outer_hinge = outer["hinge"]
        outer_te = outer["trailing_edge"]

        # Aileron perimeter
        points = [
            inner_le,
            inner_hinge,
            inner_te,
            outer_te,
            outer_hinge,
            outer_le,
            inner_le,
        ]

        ax.plot(
            [p[0] for p in points],
            [p[1] for p in points],
            linewidth=2.5,
            marker="o",
            markersize=4,
            label=uid,
        )

        # Hinge line
        ax.plot(
            [inner_hinge[0], outer_hinge[0]],
            [inner_hinge[1], outer_hinge[1]],
            linewidth=3.5,
        )

        # Aileron leading edge
        ax.plot(
            [inner_le[0], outer_le[0]],
            [inner_le[1], outer_le[1]],
            linewidth=2,
        )

        # Aileron trailing edge
        ax.plot(
            [inner_te[0], outer_te[0]],
            [inner_te[1], outer_te[1]],
            linewidth=2,
        )

    # ==========================================================
    # AXES
    # ==========================================================

    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")

    if configuration is not None:

        ax.set_title(
            f"Aileron Top View - {configuration}"
        )

    else:

        ax.set_title(
            "Aileron Top View"
        )

    ax.set_aspect(
        "equal",
        adjustable="box",
    )

    ax.grid(True)

    ax.legend()

    plt.tight_layout()

    plt.show()