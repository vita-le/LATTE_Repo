# src/latte/core/validation.py
"""Checks on the CPACS XML that run BEFORE TiGL opens the file."""
import xml.etree.ElementTree as ET


def find_missing_airfoils(filename):
    """Return the sorted airfoil uIDs used by wings but never defined."""
    root = ET.parse(str(filename)).getroot()

    # Airfoils that are actually defined in the profiles section
    defined = {
        el.get("uID")
        for el in root.findall("./vehicles/profiles/wingAirfoils/wingAirfoil")
    }

    # Airfoils referenced by the wing elements
    used = set()
    for wings in root.findall("./vehicles/aircraft/model/wings"):
        for el in wings.iter("airfoilUID"):
            if el.text and el.text.strip():
                used.add(el.text.strip())

    return sorted(used - defined)