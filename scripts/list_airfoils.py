# scripts/list_airfoils.py
"""For every example CPACS, list its wing airfoils and how they are defined."""
import xml.etree.ElementTree as ET
from pathlib import Path

from latte.core.cpacs_airfoil import cpacs_airfoil_properties, list_airfoil_uids

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
FILES = ["cs23_base.xml", "DLH_CPACS.xml", "GripenECPACS.xml", "F18SRA_cpacs.xml", "TEST_CPACS.xml"]


def local(tag):
    return tag.rsplit("}", 1)[-1]


for name in FILES:
    path = EXAMPLES / name
    print("=" * 70)
    print(name)
    uids = list_airfoil_uids(path)
    print(f"  {len(uids)} wingAirfoil element(s)")
    root = ET.parse(path).getroot()
    children = {
        el.get("uID"): [local(c.tag) for c in el]
        for el in root.iter() if local(el.tag) == "wingAirfoil"
    }
    for uid in uids:
        try:
            p = cpacs_airfoil_properties(path, uid)
            print(f"  {uid:28s} OK    t/c={p.t_c:.4f}  Phi1={p.phi_te_1_deg:6.2f}  Phi2={p.phi_te_2_deg:6.2f}")
        except Exception as exc:
            print(f"  {uid:28s} FAIL  {type(exc).__name__}: {exc}  | children: {children[uid]}")