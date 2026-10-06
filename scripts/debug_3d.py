# scripts/debug_3d.py
"""Run the 3D view without the GUI to see the full traceback."""
from pathlib import Path

from latte.core.cpacs_document import CPACSDocument
from latte.visualization.plot_wing import plot_wing_geometry

path = Path(__file__).resolve().parent.parent / "examples" / "cs23_base.xml"

# Same steps as geometry_button.py, but errors are not caught
with CPACSDocument(path, "AircraftModel") as doc:
    wings = doc.wings

print("wings:", len(wings))
plot_wing_geometry(wings, "AircraftModel")