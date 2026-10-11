# tools/set_aileron_hinge.py
"""Write a copy of a CPACS file with the hinge of one aileron at a given chord fraction.

The example files have the hinge almost on the aileron leading edge (no aerodynamic
balance), where the Roskam balance ratio is not defined. This makes a usable copy.

Example:
  python tools/set_aileron_hinge.py examples/cs23_base.xml --aileron AileronUID --out examples/cs23_balanced.xml
"""
import argparse
from pathlib import Path

from latte.core.cpacs_edit import set_aileron_hinge


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("cpacs", type=Path)
    parser.add_argument("--aileron", required=True, help="uID of the trailingEdgeDevice")
    parser.add_argument("--fraction", type=float, default=0.25,
                        help="hinge position, fraction of the aileron chord from its LE (default 0.25)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.out.resolve() == args.cpacs.resolve():
        parser.error("--out must differ from the input file (the original is never overwritten)")
    text = args.cpacs.read_text(encoding="utf-8")
    new_text, hinge = set_aileron_hinge(text, args.aileron, args.fraction)
    args.out.write_text(new_text, encoding="utf-8")
    print(f"hingeXsi set to inner={hinge['inner']:.4f}, outer={hinge['outer']:.4f}")
    print(f"Written {args.out}")


if __name__ == "__main__":
    main()