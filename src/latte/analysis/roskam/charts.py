# charts.py (sketch)
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.interpolate import interp1d

DATA_DIR = Path(__file__).parent / "data"


class Chart1D:
    """One digitized chart y = f(x), loaded from a two-column CSV."""

    def __init__(self, filename, name):
        data = np.loadtxt(DATA_DIR / filename, delimiter=",", skiprows=1)
        self.name = name
        self._f = interp1d(data[:, 0], data[:, 1], kind="linear")
        self.x_min, self.x_max = data[0, 0], data[-1, 0]

    def __call__(self, x):
        if not self.x_min <= x <= self.x_max:
            raise ValueError(
                f"{self.name}: x={x:.4g} outside digitized range "
                f"[{self.x_min:.4g}, {self.x_max:.4g}]"
            )
        return float(self._f(x))