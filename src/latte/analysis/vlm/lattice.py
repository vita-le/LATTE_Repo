# src/latte/analysis/vlm/lattice.py
"""Vortex lattice description: collocation points, normals and horseshoe vortices."""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Lattice:
    """A set of n panels, each with one horseshoe vortex.

    colloc:  (n, 3) control points (3/4 of the panel chord, mid-span)
    normals: (n, 3) unit normals at the control points
    vortex:  (n, 8, 3) horseshoe polyline of every panel, in the Tornado layout:
             far leg end, TE, TE, bound start, bound end, TE, TE, far leg end
             (the circulation runs along the polyline; bound vortex = points 3 -> 4)
    Axes: x aft, y to the right, z up.
    """

    colloc: np.ndarray
    normals: np.ndarray
    vortex: np.ndarray

    def __post_init__(self):
        n = len(self.colloc)
        if self.colloc.shape != (n, 3) or self.normals.shape != (n, 3) or self.vortex.shape != (n, 8, 3):
            raise ValueError("Lattice arrays must have shapes (n,3), (n,3) and (n,8,3)")

    @property
    def size(self) -> int:
        return len(self.colloc)

    @property
    def bound_start(self) -> np.ndarray:
        return self.vortex[:, 3, :]

    @property
    def bound_end(self) -> np.ndarray:
        return self.vortex[:, 4, :]

    @property
    def bound_mid(self) -> np.ndarray:
        return 0.5 * (self.bound_start + self.bound_end)