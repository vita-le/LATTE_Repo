# tools/dat_to_cpacs.py
"""Add an airfoil from a .dat file to a CPACS file.

Examples:
  python tools/dat_to_cpacs.py n64210.dat --uid N64210.DAT
  python tools/dat_to_cpacs.py n64210.dat --uid N64210.DAT --cpacs examples/F18SRA_cpacs.xml --out examples/F18SRA_fixed.xml
"""
import argparse
from pathlib import Path

from latte.core.airfoil import airfoil_properties
from latte.core.airfoil_import import airfoil_xml, insert_airfoil, parse_dat


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("dat", type=Path, help="airfoil coordinate file (Selig or Lednicer)")
    parser.add_argument("--uid", required=True, help="uID the CPACS file expects for this airfoil")
    parser.add_argument("--cpacs", type=Path, help="CPACS file to modify (a copy is written to --out)")
    parser.add_argument("--out", type=Path, help="output CPACS file")
    args = parser.parse_args()

    name, x, z = parse_dat(args.dat.read_text(encoding="utf-8", errors="replace"))
    props = airfoil_properties(x, z)
    print(f"{name}: {len(x)} points, t/c={props.t_c:.4f}, "
          f"Phi1={props.phi_te_1_deg:.2f} deg, Phi2={props.phi_te_2_deg:.2f} deg")
    snippet = airfoil_xml(args.uid, name, x, z)

    if args.cpacs is None:
        print(snippet)
        return
    if args.out is None or args.out.resolve() == args.cpacs.resolve():
        parser.error("--out is required and must differ from --cpacs (the original is never overwritten)")
    text = args.cpacs.read_text(encoding="utf-8")
    args.out.write_text(insert_airfoil(text, snippet, args.uid), encoding="utf-8")
    print(f"Written {args.out}")


if __name__ == "__main__":
    main()