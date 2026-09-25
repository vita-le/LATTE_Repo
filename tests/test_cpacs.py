from pathlib import Path

from tixi3 import tixi3wrapper
from tigl3 import tigl3wrapper


def print_children(tixi, path):

    print(f"\n   Contents of: {path}")

    try:
        n = tixi.getNumberOfChildNodes(path)

        print(f"   Number of child nodes: {n}")

        for i in range(1, n + 1):

            try:
                name = tixi.getChildNodeName(path, i)
                print(f"      {i}: {name}")

            except Exception as error:
                print(f"      {i}: ERROR: {error}")

    except Exception as error:

        print(f"   ERROR: {error}")


def test_cpacs(filename):

    filename = Path(filename)

    print(f"\nTesting: {filename}")
    print("-" * 60)

    tixi = tixi3wrapper.Tixi3()

    try:

        # ---------------------------------------------------------
        # 1. Open XML
        # ---------------------------------------------------------

        print("1. Opening XML with TiXI...")

        tixi.open(str(filename))

        print("   OK")

        # ---------------------------------------------------------
        # 2. CPACS version
        # ---------------------------------------------------------

        print("2. Reading CPACS version...")

        if tixi.checkElement("/cpacs/header/version"):

            version = tixi.getTextElement(
                "/cpacs/header/version"
            )

            print(f"   CPACS version: {version}")

        else:

            print("   CPACS version node not found")

        # ---------------------------------------------------------
        # 3. Inspect vehicles
        # ---------------------------------------------------------

        print("3. Inspecting vehicles...")

        if not tixi.checkElement("/cpacs/vehicles"):

            print("   /cpacs/vehicles not found")

        else:

            print("   /cpacs/vehicles exists")

            # Aircraft
            if tixi.checkElement(
                "/cpacs/vehicles/aircraft"
            ):

                print_children(
                    tixi,
                    "/cpacs/vehicles/aircraft"
                )

            else:

                print(
                    "   /cpacs/vehicles/aircraft not found"
                )

            # Rotorcraft
            if tixi.checkElement(
                "/cpacs/vehicles/rotorcraft"
            ):

                print_children(
                    tixi,
                    "/cpacs/vehicles/rotorcraft"
                )

            else:

                print(
                    "   /cpacs/vehicles/rotorcraft not found"
                )

        # ---------------------------------------------------------
        # 4. Open with TiGL
        # ---------------------------------------------------------

        print("\n4. Opening with TiGL...")

        tigl = tigl3wrapper.Tigl3()

        tigl.open(tixi, "")

        print("   OK")

        print(
            f"   Number of wings: {tigl.getWingCount()}"
        )

        tigl.close()

    except Exception as error:

        print("\nERROR:")
        print(error)

    finally:

        tixi.close()


if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "python -m src.core.test_cpacs file.xml"
        )

        raise SystemExit(1)

    test_cpacs(sys.argv[1])