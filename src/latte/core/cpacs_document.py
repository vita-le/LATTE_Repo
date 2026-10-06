# src/latte/core/cpacs_document.py
"""Single entry point to load a CPACS file and read its geometry."""
from pathlib import Path

from latte.core.aileron import extract_aileron_geometry, extract_ailerons
from latte.core.errors import InvalidCPACSError
from latte.core.validation import find_missing_airfoils
from latte.core.wing_geo import extract_all_wings, list_configurations, open_cpacs


class CPACSDocument:
    """Owns the TiXI/TiGL handles and gives access to wings and ailerons.

    Usage:
        with CPACSDocument("examples/cs23_base.xml") as doc:
            print(doc.wings, doc.ailerons)
    """

    def __init__(self, filename, configuration=None):
        self.path = Path(filename)
        self.configurations = list_configurations(self.path)
        self._wings = None
        self._ailerons = None
        self.tigl = None
        self.tixi = None

        # Check the XML BEFORE TiGL touches it, so errors are readable
        problems = [
            f"Airfoil '{uid}' is used by a wing but is not defined in the file"
            for uid in find_missing_airfoils(self.path)
        ]
        if problems:
            raise InvalidCPACSError(self.path, problems)

        self.tigl, self.tixi = open_cpacs(self.path, configuration)

    @property
    def wings(self):
        """List of wing dictionaries (uid, span, area, segments)."""
        if self._wings is None:
            try:
                self._wings = extract_all_wings(self.tigl)
            except Exception as exc:
                # Wrap TiGL errors so the GUI can show them
                raise InvalidCPACSError(
                    self.path, [f"TiGL could not build the wing geometry: {exc}"]
                ) from exc
        return self._wings

    @property
    def ailerons(self):
        """List of aileron dictionaries; empty if the file has none."""
        if self._ailerons is None:
            self._ailerons = extract_ailerons(self.tigl, str(self.path))
        return self._ailerons

    def aileron_geometry(self, aileron):
        """3D points (inner/outer: leading edge, hinge, trailing edge)."""
        return extract_aileron_geometry(self.tigl, aileron)

    def close(self):
        # Close TiGL first, then TiXI; safe to call more than once
        if self.tigl is not None:
            self.tigl.close()
            self.tigl = None
        if self.tixi is not None:
            self.tixi.close()
            self.tixi = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()