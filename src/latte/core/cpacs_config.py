from pathlib import Path
import xml.etree.ElementTree as ET


def get_cpacs_configurations(filename):
    """
    Return the available CPACS vehicle configurations.

    Each configuration is returned as a dictionary containing:
        - type
        - uid
    """

    filename = Path(filename)

    tree = ET.parse(filename)
    root = tree.getroot()

    configurations = []

    # Find /cpacs/vehicles
    vehicles = None

    for child in root:
        if child.tag.split("}")[-1] == "vehicles":
            vehicles = child
            break

    if vehicles is None:
        raise ValueError(
            "The CPACS file does not contain /cpacs/vehicles."
        )

    # Look for aircraft and rotorcraft
    for vehicle in vehicles:

        vehicle_type = vehicle.tag.split("}")[-1]

        if vehicle_type not in ("aircraft", "rotorcraft"):
            continue

        for model in vehicle:

            model_type = model.tag.split("}")[-1]

            if model_type != "model":
                continue

            uid = model.attrib.get("uID")

            if uid:
                configurations.append({
                    "type": vehicle_type,
                    "uid": uid,
                })

    if not configurations:
        raise ValueError(
            "No aircraft or rotorcraft configurations "
            "were found in the CPACS file."
        )

    return configurations