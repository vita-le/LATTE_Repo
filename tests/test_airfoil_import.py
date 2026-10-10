# tests/test_airfoil_import.py
import math

import numpy as np
import pytest

from latte.core.airfoil import airfoil_properties
from latte.core.airfoil_import import airfoil_xml, insert_airfoil, parse_dat
from latte.core.cpacs_airfoil import cpacs_airfoil_properties, list_airfoil_uids


def naca0010():
    beta = np.linspace(0, math.pi, 60)
    x = 0.5 * (1 - np.cos(beta))
    yt = 5 * 0.10 * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2
                     + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    return x, yt


def selig_text():
    x, yt = naca0010()
    xs = np.concatenate([x[::-1], x[1:]])
    zs = np.concatenate([yt[::-1], -yt[1:]])             # TE -> upper -> LE -> lower
    rows = "\n".join(f"  {a:.6f}  {b:.6f}" for a, b in zip(xs, zs))
    return "NACA 0010 test\n" + rows + "\n"


def lednicer_text():
    x, yt = naca0010()
    n = len(x)
    upper = "\n".join(f"  {a:.6f}  {b:.6f}" for a, b in zip(x, yt))
    lower = "\n".join(f"  {a:.6f}  {-b:.6f}" for a, b in zip(x, yt))
    return f"NACA 0010 test\n  {n}.  {n}.\n\n{upper}\n\n{lower}\n"


def test_selig_parse_keeps_order():
    name, x, z = parse_dat(selig_text())
    assert name == "NACA 0010 test"
    assert x[0] == pytest.approx(1.0) and x[-1] == pytest.approx(1.0)
    assert z[1] > 0                                       # starts on the upper surface


def test_lednicer_gives_the_same_contour_as_selig():
    _, xs, zs = parse_dat(selig_text())
    _, xl, zl = parse_dat(lednicer_text())
    assert xl == pytest.approx(xs, abs=1e-6)
    assert zl == pytest.approx(zs, abs=1e-6)


def test_properties_of_imported_airfoil():
    _, x, z = parse_dat(selig_text())
    assert airfoil_properties(x, z).t_c == pytest.approx(0.10, abs=2e-3)


def test_bad_files_are_rejected():
    with pytest.raises(ValueError):
        parse_dat("name\n1 2\n3 4\n")
    with pytest.raises(ValueError):
        parse_dat("")
    with pytest.raises(ValueError):                       # x not normalised (e.g. in mm)
        parse_dat("name\n" + "\n".join(f"{100 * i:.1f} {i:.1f}" for i in range(20)))


CPACS = """<cpacs><vehicles><profiles><wingAirfoils>
      <wingAirfoil uID="OTHER"><pointList><x>1;0</x><z>0;0</z></pointList></wingAirfoil>
      </wingAirfoils></profiles></vehicles></cpacs>
"""


def test_insert_airfoil_end_to_end(tmp_path):
    name, x, z = parse_dat(selig_text())
    new = insert_airfoil(CPACS, airfoil_xml("N64210.DAT", name, x, z), "N64210.DAT")
    path = tmp_path / "fixed.xml"
    path.write_text(new)
    assert list_airfoil_uids(path) == ["N64210.DAT", "OTHER"]
    assert cpacs_airfoil_properties(path, "N64210.DAT").t_c == pytest.approx(0.10, abs=2e-3)
    assert new.count("OTHER") == CPACS.count("OTHER")     # rest of the file untouched


def test_insert_refuses_duplicates_and_missing_section():
    snippet = airfoil_xml("OTHER", "x", [1, 0.5, 0], [0, 0.1, 0])
    with pytest.raises(ValueError):
        insert_airfoil(CPACS, snippet, "OTHER")
    with pytest.raises(ValueError):
        insert_airfoil("<cpacs/>", snippet, "NEW")