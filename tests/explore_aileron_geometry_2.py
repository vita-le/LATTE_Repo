from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


FILES = [
    ROOT / "examples" / "DLH_CPACS.xml",
    ROOT / "examples" / "F18SRA_cpacs.xml",
]


def strip_namespace(tag):
    return tag.split("}", 1)[-1]


def print_element(element, level=0):

    indent = "  " * level

    tag = strip_namespace(element.tag)

    attributes = ""

    for key, value in element.attrib.items():
        attributes += f' {key}="{value}"'

    text = (
        element.text.strip()
        if element.text and element.text.strip()
        else ""
    )

    if text:
        print(
            f"{indent}{tag}{attributes}: {text}"
        )
    else:
        print(
            f"{indent}{tag}{attributes}"
        )

    for child in element:
        print_element(
            child,
            level + 1,
        )


def inspect_aileron(cpacs_file):

    print("\n")
    print("=" * 80)
    print(cpacs_file.name)
    print("=" * 80)

    tree = ET.parse(cpacs_file)
    root = tree.getroot()

    for element in root.iter():

        if strip_namespace(element.tag) != "trailingEdgeDevice":
            continue

        name = None

        for child in element:

            if strip_namespace(child.tag) == "name":
                name = child.text

        if name is None:
            continue

        if "aileron" not in name.lower():
            continue

        uid = element.attrib.get("uID")

        print("\n")
        print("-" * 80)
        print(f"AILERON: {uid}")
        print("-" * 80)

        outer_shape = None

        for child in element:

            if strip_namespace(child.tag) == "outerShape":
                outer_shape = child

        if outer_shape is None:
            continue

        for border in outer_shape:

            border_name = strip_namespace(
                border.tag
            )

            if border_name not in [
                "innerBorder",
                "outerBorder",
            ]:
                continue

            print(f"\n[{border_name}]")

            for child in border:

                tag = strip_namespace(
                    child.tag
                )

                if tag not in [
                    "etaLE",
                    "etaTE",
                    "xsiLE",
                    "y_i",
                    "y_o",
                ]:
                    continue

                print_element(
                    child,
                    level=1,
                )


def main():

    for cpacs_file in FILES:

        try:
            inspect_aileron(
                cpacs_file
            )

        except Exception as e:

            print(
                f"ERROR: "
                f"{type(e).__name__}: {e}"
            )


if __name__ == "__main__":
    main()