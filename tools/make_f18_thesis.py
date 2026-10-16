# tools/make_f18_thesis.py
"""Build a standard CPACS of the F/A-18 SRA wing of the thesis (Table 4.1).

Starts from examples/F18SRA_cpacs.xml (fuselage, tail and profiles are kept) and rewrites
the wing as a trapezoid (root 4.04 m, tip 1.68 m, half span 6.155 m, sweep c/4 20 deg,
dihedral -3 deg) with one aileron (y 4.03-5.87 m, cf/c 0.288, hinge at 25% of its chord).

Example:
  python tools/make_f18_thesis.py --dat examples/naca64a210.dat
"""
import argparse
from pathlib import Path

from lxml import etree

from latte.core.airfoil import airfoil_properties
from latte.core.airfoil_import import parse_dat
from latte.core.cpacs_wing import build_wing_model, schema_errors

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--dat", type=Path, required=True, help="airfoil coordinates (.dat), e.g. NACA 64A210")
    parser.add_argument("--cpacs", type=Path, default=ROOT / "examples" / "F18SRA_cpacs.xml")
    parser.add_argument("--out", type=Path, default=ROOT / "examples" / "F18SRA_thesis.xml")
    parser.add_argument("--schema", type=Path, default=ROOT / "examples" / "cpacs_schema.xsd")
    parser.add_argument("--airfoil-uid", default="N64210.DAT", help="uID used by the wing sections")
    parser.add_argument("--keep-other-devices", action="store_true", help="keep flaps, slats and spoilers")
    parser.add_argument("--standard-only", action="store_true",
                        help="drop the MATLAB-specific fields (y_i, y_o, reference_S)")
    args = parser.parse_args()

    if args.out.resolve() == args.cpacs.resolve():
        parser.error("--out must differ from --cpacs (the original is never overwritten)")

    name, x, z = parse_dat(args.dat.read_text(encoding="utf-8", errors="replace"))
    props = airfoil_properties(x, z)
    print(f"Airfoil {name}: {len(x)} points, t/c={props.t_c:.4f}, "
          f"Phi1={props.phi_te_1_deg:.2f} deg, Phi2={props.phi_te_2_deg:.2f} deg")

    tree = etree.parse(str(args.cpacs))
    summary = build_wing_model(
        tree.getroot(), "wing", "AileronUID", airfoil=(name, x, z), airfoil_uid=args.airfoil_uid,
        keep_other_devices=args.keep_other_devices, keep_matlab_fields=not args.standard_only,
    )
    tree.write(str(args.out), xml_declaration=True, encoding="UTF-8")
    print(f"Aileron: eta {summary['eta_inner']:.4f} -> {summary['eta_outer']:.4f}, "
          f"xsiLE {summary['xsi_le']:.3f}, hingeXsi {summary['hinge_xsi']:.4f}")
    print(f"Written {args.out}")

    if args.schema.exists():
        names = sorted({m.split("'")[1] for _, m in schema_errors(args.out, args.schema) if "'" in m})
        print("Elements not in the CPACS schema:", ", ".join(names) or "none")
    else:
        print(f"(schema {args.schema} not found: validation skipped)")


if __name__ == "__main__":
    main()