from pathlib import Path
import xml.etree.ElementTree as ET


CPACS_FILES = [
    "examples/cs23_base.xml",
    "examples/DLH_CPACS.xml",
    "examples/F18SRA_cpacs.xml",
    "examples/GripenECPACS.xml",
]


def local_name(tag):
    return tag.split("}")[-1]


def is_aileron(element):
    """
    Check whether an XML element represents an aileron.
    """

    text = []

    for child in element.iter():

        if child.text:
            text.append(child.text.lower())

        text.extend(
            value.lower()
            for value in child.attrib.values()
        )

    return "aileron" in " ".join(text)


def print_tree(element, level=0):
    """
    Print the complete structure of one aileron,
    but without dumping the entire CPACS file.
    """

    indent = "    " * level

    tag = local_name(element.tag)

    attributes = ""

    for key, value in element.attrib.items():
        attributes += f' {key}="{value}"'

    text = ""

    if element.text and element.text.strip():
        text = f" = {element.text.strip()}"

    print(
        f"{indent}{tag}{attributes}{text}"
    )

    for child in element:
        print_tree(child, level + 1)


def analyse_file(filename):

    print()
    print("=" * 80)
    print(f"FILE: {filename}")
    print("=" * 80)

    path = Path(filename)

    if not path.exists():

        print("FILE NOT FOUND")
        return

    try:

        tree = ET.parse(path)
        root = tree.getroot()

    except Exception as error:

        print(f"XML ERROR: {error}")
        return

    ailerons = []

    for element in root.iter():

        tag = local_name(element.tag)

        if tag != "trailingEdgeDevice":
            continue

        if is_aileron(element):
            ailerons.append(element)

    if not ailerons:

        print()
        print("NO AILERON FOUND")
        return

    print()
    print(f"AILERONS FOUND: {len(ailerons)}")

    for index, aileron in enumerate(ailerons, start=1):

        uid = aileron.attrib.get("uID")

        print()
        print("-" * 80)
        print(f"AILERON #{index}")
        print("-" * 80)

        print(f"UID: {uid}")

        print()
        print("STRUCTURE")
        print("-" * 80)

        for child in aileron:
            print_tree(child, level=1)


def main():

    print("=" * 80)
    print("LATTE - AILERON EXPLORER")
    print("=" * 80)

    for filename in CPACS_FILES:
        analyse_file(filename)

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    main()