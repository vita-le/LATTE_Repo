# src/latte/core/airfoil_import.py
"""Convert airfoil coordinate files (.dat) into CPACS wingAirfoil elements."""
import re

_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"      # accepts "35." and ".5"
_NUMBER_ROW = re.compile(rf"^\s*({_NUMBER})[\s,;]+({_NUMBER})\s*$")


def parse_dat(text: str):
    """Return (name, x, z) from the text of a .dat file.

    Supported formats:
      Selig:    name line, then points TE -> upper surface -> LE -> lower surface -> TE
      Lednicer: name line, a "n_upper n_lower" line, upper LE -> TE, lower LE -> TE
    The result is always ordered TE -> upper -> LE -> lower -> TE.
    """
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty airfoil file")
    name = lines[0].strip()
    rows = []
    for line in lines[1:]:
        match = _NUMBER_ROW.match(line)
        if match:
            rows.append((float(match.group(1)), float(match.group(2))))
    if len(rows) < 10:
        raise ValueError("Fewer than 10 coordinate rows found: not an airfoil file?")

    if rows[0][0] > 1.5 and rows[0][1] > 1.5:            # Lednicer: point counts first
        n_upper, n_lower = int(rows[0][0]), int(rows[0][1])
        points = rows[1:]
        if len(points) != n_upper + n_lower:
            raise ValueError(
                f"Lednicer file declares {n_upper}+{n_lower} points but has {len(points)}"
            )
        upper, lower = points[:n_upper], points[n_upper:]
        points = upper[::-1] + lower[1:]                  # TE -> upper -> LE -> lower
    else:
        points = rows

    x = [p[0] for p in points]
    z = [p[1] for p in points]
    if max(x) > 1.5 or min(x) < -0.05:
        raise ValueError("x coordinates are not normalised to the chord (expected 0..1)")
    return name, x, z


def airfoil_xml(uid: str, name: str, x, z, indent: str = "        ") -> str:
    """The <wingAirfoil> element for these points."""
    def vector(values):
        return ";".join(repr(float(v)) for v in values)

    zeros = [0.0] * len(x)
    i = indent
    return (
        f'{i}<wingAirfoil uID="{uid}">\n'
        f"{i}  <name>{name}</name>\n"
        f"{i}  <description>Imported from a .dat file by LATTE</description>\n"
        f"{i}  <pointList>\n"
        f'{i}    <x mapType="vector">{vector(x)}</x>\n'
        f'{i}    <y mapType="vector">{vector(zeros)}</y>\n'
        f'{i}    <z mapType="vector">{vector(z)}</z>\n'
        f"{i}  </pointList>\n"
        f"{i}</wingAirfoil>\n"
    )


def insert_airfoil(cpacs_text: str, snippet: str, uid: str) -> str:
    """Insert the element before </wingAirfoils>, leaving the rest of the file untouched."""
    if re.search(rf'<wingAirfoil\b[^>]*uID="{re.escape(uid)}"', cpacs_text):
        raise ValueError(f"Airfoil {uid!r} is already defined in the file")
    marker = "</wingAirfoils>"
    if marker not in cpacs_text:
        raise ValueError("The file has no <wingAirfoils> section")
    return cpacs_text.replace(marker, snippet + "      " + marker, 1)