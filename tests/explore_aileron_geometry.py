from pathlib import Path
from xml.etree import ElementTree as ET

from src.core.WingGeo import open_cpacs
from src.core.aileron import extract_ailerons


ROOT = Path(__file__).resolve().parents[1]

CONFIGURATIONS = {
    ROOT / "examples" / "DLH_CPACS.xml": "AircraftModel",
    ROOT / "examples" / "F18SRA_cpacs.xml": None,
}


def strip_namespace(tag):
    return tag.split("}", 1)[-1]


def print_control_surfaces(tigl, component_segment_uid):
    print("\n=== CONTROL SURFACES FROM TIGL ===")
    print(f"Component segment: {component_segment_uid}")

    try:
        count = tigl.getControlSurfaceCount(
            component_segment_uid
        )

        print(f"Count: {count}")

    except Exception as e:

        print(
            f"getControlSurfaceCount ERROR: "
            f"{type(e).__name__}: {e}"
        )

        return

    for index in range(1, count + 1):

        print(f"\n--- Control surface {index} ---")

        try:

            uid = tigl.getControlSurfaceUID(
                component_segment_uid,
                index,
            )

            print(f"UID: {uid}")

        except Exception as e:

            print(
                f"UID ERROR: "
                f"{type(e).__name__}: {e}"
            )

            continue

        try:

            surface_type = tigl.getControlSurfaceType(
                component_segment_uid,
                index,
            )

            print(f"Type: {surface_type}")

        except Exception as e:

            print(
                f"Type ERROR: "
                f"{type(e).__name__}: {e}"
            )


def print_component_segment_points(
    tigl,
    component_segment_uid,
):

    print("\n=== COMPONENT SEGMENT POINTS ===")
    print(f"UID: {component_segment_uid}")

    test_etas = [
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
    ]

    for eta in test_etas:

        print(f"\neta = {eta}")

        for xsi in [
            0.0,
            0.5,
            1.0,
        ]:

            try:

                point = tigl.wingComponentSegmentGetPoint(
                    component_segment_uid,
                    eta,
                    xsi,
                )

                print(
                    f"  xsi={xsi}: "
                    f"({point.x:.6f}, "
                    f"{point.y:.6f}, "
                    f"{point.z:.6f})"
                )

            except Exception as e:

                print(
                    f"  xsi={xsi}: "
                    f"ERROR {type(e).__name__}: {e}"
                )


def print_raw_aileron_xml(
    cpacs_file,
    aileron_uid,
):

    print("\n=== RAW AILERON XML ===")
    print(f"UID: {aileron_uid}")

    tree = ET.parse(cpacs_file)
    root = tree.getroot()

    for element in root.iter():

        if strip_namespace(element.tag) != "trailingEdgeDevice":
            continue

        uid = element.attrib.get("uID")

        if uid != aileron_uid:
            continue

        print("\n--- trailingEdgeDevice ---")

        for child in element:
            print_xml_tree(
                child,
                level=0,
            )

        return

    print("Aileron XML not found.")


def print_xml_tree(
    element,
    level=0,
):

    indent = "  " * level

    tag = strip_namespace(
        element.tag
    )

    attributes = ""

    for key, value in element.attrib.items():

        attributes += (
            f' {key}="{value}"'
        )

    text = (
        element.text.strip()
        if element.text
        and element.text.strip()
        else ""
    )

    if text:

        print(
            f"{indent}<{tag}{attributes}>"
            f"{text}</{tag}>"
        )

    else:

        print(
            f"{indent}<{tag}{attributes}>"
        )

    for child in element:

        print_xml_tree(
            child,
            level + 1,
        )

    if len(element):

        print(
            f"{indent}</{tag}>"
        )


def main():

    for cpacs_file, configuration in CONFIGURATIONS.items():

        print("\n\n")
        print("#" * 80)
        print(f"FILE: {cpacs_file.name}")
        print(f"CONFIGURATION: {configuration}")
        print("#" * 80)

        try:

            tigl, tixi = open_cpacs(
                cpacs_file,
                configuration,
            )

            ailerons = extract_ailerons(
                tigl,
                cpacs_file,
            )

            print(
                f"\nAilerons found: "
                f"{len(ailerons)}"
            )

            for aileron in ailerons:

                uid = aileron["uid"]
                parent_uid = aileron["parent_uid"]

                print("\n" + "=" * 80)
                print(f"AILERON: {uid}")
                print("=" * 80)

                print_control_surfaces(
                    tigl,
                    parent_uid,
                )

                print_component_segment_points(
                    tigl,
                    parent_uid,
                )

                print_raw_aileron_xml(
                    cpacs_file,
                    uid,
                )

        except Exception as e:

            print(
                f"\nERROR: "
                f"{type(e).__name__}: {e}"
            )


if __name__ == "__main__":
    main()