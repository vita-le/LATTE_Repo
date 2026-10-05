from xml.etree import ElementTree as ET


def _strip_namespace(tag):
    """Remove XML namespace from a tag."""
    return tag.split("}", 1)[-1]


def _find_text(element, tag_name):
    """Find the first descendant with the given tag name and return its text."""

    for child in element.iter():

        if _strip_namespace(child.tag) == tag_name:

            if child.text is not None:
                return child.text.strip()

    return None


def _find_float(element, tag_name):
    """Find the first descendant with the given tag name and convert to float."""

    value = _find_text(
        element,
        tag_name,
    )

    if value is None:
        return None

    try:
        return float(value)

    except ValueError:
        return None


def _find_child(parent, tag_name):
    """Find the first direct child with the given tag name."""

    if parent is None:
        return None

    for child in parent:

        if _strip_namespace(child.tag) == tag_name:
            return child

    return None


def _find_descendant(parent, tag_name):
    """Find the first descendant with the given tag name."""

    if parent is None:
        return None

    for child in parent.iter():

        if _strip_namespace(child.tag) == tag_name:
            return child

    return None


def _extract_border_data(border):
    """Extract spanwise and chordwise information from an aileron border."""

    if border is None:

        return {
            "eta_le": None,
            "eta_te": None,
            "xsi_le": None,
            "y": None,
        }

    eta_le_node = _find_descendant(
        border,
        "etaLE",
    )

    eta_te_node = _find_descendant(
        border,
        "etaTE",
    )

    xsi_le_node = _find_descendant(
        border,
        "xsiLE",
    )

    eta_le = None
    eta_te = None
    xsi_le = None
    y = None

    if eta_le_node is not None:

        eta_le = _find_float(
            eta_le_node,
            "eta",
        )

    if eta_te_node is not None:

        eta_te = _find_float(
            eta_te_node,
            "eta",
        )

    if xsi_le_node is not None:

        xsi_le = _find_float(
            xsi_le_node,
            "xsi",
        )

    y = _find_float(
        border,
        "y",
    )

    return {
        "eta_le": eta_le,
        "eta_te": eta_te,
        "xsi_le": xsi_le,
        "y": y,
    }


def _extract_hinge_data(path):
    """Extract inner and outer hinge data."""

    if path is None:

        return {
            "inner_xsi": None,
            "outer_xsi": None,
            "inner_height": None,
            "outer_height": None,
        }

    inner = _find_descendant(
        path,
        "innerHingePoint",
    )

    outer = _find_descendant(
        path,
        "outerHingePoint",
    )

    return {
        "inner_xsi": (
            _find_float(
                inner,
                "hingeXsi",
            )
            if inner is not None
            else None
        ),

        "outer_xsi": (
            _find_float(
                outer,
                "hingeXsi",
            )
            if outer is not None
            else None
        ),

        "inner_height": (
            _find_float(
                inner,
                "hingeRelHeight",
            )
            if inner is not None
            else None
        ),

        "outer_height": (
            _find_float(
                outer,
                "hingeRelHeight",
            )
            if outer is not None
            else None
        ),
    }


def _extract_deflection_data(aileron, tigl, uid):
    """
    Extract control parameters and hinge-line rotations.

    TiGL provides the minimum and maximum control parameters.
    The actual hinge-line rotations are read directly from CPACS.
    """

    minimum_control_parameter = None
    maximum_control_parameter = None

    try:

        minimum_control_parameter = float(
            tigl.controlSurfaceGetMinimumControlParameter(
                uid
            )
        )

    except Exception:
        pass

    try:

        maximum_control_parameter = float(
            tigl.controlSurfaceGetMaximumControlParameter(
                uid
            )
        )

    except Exception:
        pass

    neutral_control_parameter = 0.0

    steps = _find_descendant(
        aileron,
        "steps",
    )

    rotations = []

    if steps is not None:

        for step in steps:

            if _strip_namespace(step.tag) != "step":
                continue

            control_parameter = _find_float(
                step,
                "controlParameter",
            )

            hinge_rotation = _find_float(
                step,
                "hingeLineRotation",
            )

            if hinge_rotation is not None:

                rotations.append(
                    {
                        "control_parameter": control_parameter,
                        "hinge_rotation": hinge_rotation,
                    }
                )

    minimum_rotation = None
    neutral_rotation = None
    maximum_rotation = None

    for rotation in rotations:

        control_parameter = rotation[
            "control_parameter"
        ]

        hinge_rotation = rotation[
            "hinge_rotation"
        ]

        if control_parameter is None:
            continue

        if control_parameter == minimum_control_parameter:

            minimum_rotation = hinge_rotation

        if control_parameter == neutral_control_parameter:

            neutral_rotation = hinge_rotation

        if control_parameter == maximum_control_parameter:

            maximum_rotation = hinge_rotation

    return {
        "control_parameter": {
            "minimum": minimum_control_parameter,
            "neutral": neutral_control_parameter,
            "maximum": maximum_control_parameter,
        },

        "hinge_rotation": {
            "minimum": minimum_rotation,
            "neutral": neutral_rotation,
            "maximum": maximum_rotation,
        },
    }


def extract_ailerons(tigl, cpacs_file):
    """
    Extract all explicit ailerons from a CPACS file.

    Parameters
    ----------
    tigl : tigl3wrapper.Tigl3
        Open TiGL object.

    cpacs_file : str or Path
        Path to the CPACS file.

    Returns
    -------
    list of dict
        Normalized aileron data.
    """

    tree = ET.parse(
        cpacs_file
    )

    root = tree.getroot()

    ailerons = []

    for element in root.iter():

        if _strip_namespace(element.tag) != "trailingEdgeDevice":
            continue

        # ---------------------------------------------------------
        # Identify actual ailerons
        # ---------------------------------------------------------

        name = _find_text(
            element,
            "name",
        )

        description = _find_text(
            element,
            "description",
        )

        text = " ".join(
            value.lower()
            for value in [
                name,
                description,
            ]
            if value is not None
        )

        if "aileron" not in text:
            continue

        # ---------------------------------------------------------
        # UID
        # ---------------------------------------------------------

        uid = element.attrib.get(
            "uID"
        )

        if uid is None:

            uid = _find_text(
                element,
                "uID",
            )

        # ---------------------------------------------------------
        # Parent component segment
        # ---------------------------------------------------------

        parent_uid = _find_text(
            element,
            "parentUID",
        )

        # ---------------------------------------------------------
        # Outer shape
        # ---------------------------------------------------------

        outer_shape = _find_descendant(
            element,
            "outerShape",
        )

        inner_border = None
        outer_border = None

        if outer_shape is not None:

            inner_border = _find_child(
                outer_shape,
                "innerBorder",
            )

            outer_border = _find_child(
                outer_shape,
                "outerBorder",
            )

        inner = _extract_border_data(
            inner_border,
        )

        outer = _extract_border_data(
            outer_border,
        )

        # ---------------------------------------------------------
        # Hinge
        # ---------------------------------------------------------

        path = _find_descendant(
            element,
            "path",
        )

        hinge = _extract_hinge_data(
            path
        )

        # ---------------------------------------------------------
        # Reference area
        # ---------------------------------------------------------

        reference_area = _find_float(
            element,
            "S_f",
        )

        # ---------------------------------------------------------
        # Deflection
        # ---------------------------------------------------------

        deflection = _extract_deflection_data(
            element,
            tigl,
            uid,
        )

        # ---------------------------------------------------------
        # Normalized aileron structure
        # ---------------------------------------------------------

        aileron = {

            "uid": uid,

            "name": name,

            "parent_uid": parent_uid,

            "source": "cpacs",

            "span": {

                "inner_eta_le": inner["eta_le"],

                "inner_eta_te": inner["eta_te"],

                "outer_eta_le": outer["eta_le"],

                "outer_eta_te": outer["eta_te"],

                "inner_y": inner["y"],

                "outer_y": outer["y"],
            },

            "chord": {

                "inner_xsi_le": inner["xsi_le"],

                "outer_xsi_le": outer["xsi_le"],
            },

            "hinge": hinge,

            "reference_area": reference_area,

            "deflection": deflection,
        }

        ailerons.append(
            aileron
        )

    return ailerons


def extract_aileron_geometry(tigl, aileron):
    """
    Extract the 3D geometry of one aileron using TiGL.

    The geometry is represented by the inner and outer
    leading-edge, hinge and trailing-edge points.

    Parameters
    ----------
    tigl : tigl3wrapper.Tigl3
        Open TiGL object.

    aileron : dict
        Aileron dictionary returned by extract_ailerons().

    Returns
    -------
    dict
        3D geometry of the aileron.
    """

    parent_uid = aileron[
        "parent_uid"
    ]

    # -------------------------------------------------------------
    # Spanwise positions
    # -------------------------------------------------------------

    inner_eta = aileron[
        "span"
    ][
        "inner_eta_le"
    ]

    outer_eta = aileron[
        "span"
    ][
        "outer_eta_le"
    ]

    # -------------------------------------------------------------
    # Leading-edge xsi
    # -------------------------------------------------------------

    inner_le_xsi = aileron[
        "chord"
    ][
        "inner_xsi_le"
    ]

    outer_le_xsi = aileron[
        "chord"
    ][
        "outer_xsi_le"
    ]

    # -------------------------------------------------------------
    # Hinge xsi
    # -------------------------------------------------------------

    inner_hinge_xsi = aileron[
        "hinge"
    ][
        "inner_xsi"
    ]

    outer_hinge_xsi = aileron[
        "hinge"
    ][
        "outer_xsi"
    ]

    # -------------------------------------------------------------
    # Leading edge
    # -------------------------------------------------------------

    inner_le = tigl.wingComponentSegmentGetPoint(
        parent_uid,
        inner_eta,
        inner_le_xsi,
    )

    outer_le = tigl.wingComponentSegmentGetPoint(
        parent_uid,
        outer_eta,
        outer_le_xsi,
    )

    # -------------------------------------------------------------
    # Hinge line
    # -------------------------------------------------------------

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

    # -------------------------------------------------------------
    # Trailing edge
    #
    # For the standard geometry currently supported,
    # xsi = 1.0 corresponds to the trailing edge.
    # -------------------------------------------------------------

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

    # -------------------------------------------------------------
    # Return geometry
    # -------------------------------------------------------------

    return {

        "uid": aileron["uid"],

        "parent_uid": parent_uid,

        "inner": {

            "leading_edge": tuple(
                inner_le
            ),

            "hinge": tuple(
                inner_hinge
            ),

            "trailing_edge": tuple(
                inner_te
            ),
        },

        "outer": {

            "leading_edge": tuple(
                outer_le
            ),

            "hinge": tuple(
                outer_hinge
            ),

            "trailing_edge": tuple(
                outer_te
            ),
        },
    }
