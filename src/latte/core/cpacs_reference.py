# src/latte/core/cpacs_reference.py
"""Reference quantities declared in a CPACS file."""
import xml.etree.ElementTree as ET
from pathlib import Path


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def read_reference_area(path, configuration=None):
    """Reference area <model>/<reference>/<area> in m2, or None if the file does not declare it.

    configuration: uID of the model to use; by default the first aircraft model, then the
    first rotorcraft model.
    """
    root = ET.parse(str(Path(path))).getroot()
    models = []
    for kind in ("aircraft", "rotorcraft"):
        for container in root.iter():
            if _local(container.tag) == kind:
                models += [m for m in container if _local(m.tag) == "model"]
    if configuration is not None:
        models = [m for m in models if m.get("uID") == configuration] or models
    for model in models[:1]:                     # only the selected / first model
        for reference in model:
            if _local(reference.tag) == "reference":
                for child in reference:
                    if _local(child.tag) == "area" and child.text and child.text.strip():
                        try:
                            value = float(child.text)
                        except ValueError:
                            return None
                        return value if value > 0 else None
    return None