from pathlib import Path

from tigl3 import tigl3wrapper
from tixi3 import tixi3wrapper


DEFAULT_CPACS = "examples/GripenECPACS.xml"
N_STATIONS = 10


def point(p):
    """Convert a TIGL point to an (x, y, z) tuple."""
    if hasattr(p, "x"):
        return p.x, p.y, p.z

    return tuple(p[:3])


def distance(p1, p2):
    """Calculate Euclidean distance between two 3D points."""
    return sum((a - b) ** 2 for a, b in zip(p1, p2)) ** 0.5


def open_cpacs(filename, configuration=None):
    """Open a CPACS file with TiXI and TiGL."""

    tixi = tixi3wrapper.Tixi3()
    tixi.open(str(filename))

    tigl = tigl3wrapper.Tigl3()

    if configuration is None:
        tigl.open(tixi, "")
    else:
        tigl.open(tixi, configuration)

    return tigl, tixi

def extract_wing(tigl, wing_uid, n=N_STATIONS):
    """
    Extract wing geometry from CPACS.

    Returns a dictionary containing:
        - wing_uid
        - span
        - area
        - segments

    Each segment contains a list of spanwise stations.
    """

    wing = tigl.wingGetIndex(wing_uid)

    span = tigl.wingGetSpan(wing_uid)
    area = tigl.wingGetReferenceArea(wing, 0)

    segments = []

    # ---------------------------------------------------------
    # Component segment
    # ---------------------------------------------------------

    if tigl.wingGetComponentSegmentCount(wing) > 0:

        n_component_segments = tigl.wingGetComponentSegmentCount(wing)

        for cs_index in range(1, n_component_segments + 1):

            cs_uid = tigl.wingGetComponentSegmentUID(
                wing,
                cs_index
            )

            stations = []

            for i in range(n):
                eta = i / (n - 1)

                le = point(
                    tigl.wingComponentSegmentGetPoint(
                        cs_uid,
                        eta,
                        0.0
                    )
                )

                te = point(
                    tigl.wingComponentSegmentGetPoint(
                        cs_uid,
                        eta,
                        1.0
                    )
                )

                stations.append({
                    "eta": eta,
                    "leading_edge": le,
                    "trailing_edge": te,
                    "chord": distance(le, te),
                })

            segments.append({
                "uid": cs_uid,
                "stations": stations,
            })

    # ---------------------------------------------------------
    # Physical segments
    # ---------------------------------------------------------

    else:

        n_segments = tigl.wingGetSegmentCount(wing)

        for seg_index in range(1, n_segments + 1):

            seg_uid = tigl.wingGetSegmentUID(
                wing,
                seg_index
            )

            stations = []

            for i in range(n):
                eta = i / (n - 1)

                le = point(
                    tigl.wingGetChordPoint(
                        wing,
                        seg_index,
                        eta,
                        0.0
                    )
                )

                te = point(
                    tigl.wingGetChordPoint(
                        wing,
                        seg_index,
                        eta,
                        1.0
                    )
                )

                stations.append({
                    "eta": eta,
                    "leading_edge": le,
                    "trailing_edge": te,
                    "chord": distance(le, te),
                })

            segments.append({
                "uid": seg_uid,
                "stations": stations,
            })

    return {
        "uid": wing_uid,
        "span": span,
        "area": area,
        "segments": segments,
    }


def extract_all_wings(tigl, n=N_STATIONS):
    """Extract geometry of all wings in the CPACS model."""

    wings = []

    n_wings = tigl.getWingCount()

    for wing_index in range(1, n_wings + 1):

        uid = tigl.wingGetUID(wing_index)

        wing = extract_wing(
            tigl,
            uid,
            n
        )

        wings.append(wing)

    return wings