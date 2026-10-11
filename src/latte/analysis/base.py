# src/latte/analysis/base.py
"""Interface shared by all hinge-moment solvers (Roskam, VLM, ...)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from latte.core.flight_state import FlightCondition


@dataclass(frozen=True)
class HingeMomentResult:
    """Result of one solver run for one flight condition."""

    method: str
    condition: FlightCondition
    cha: float | None = None              # dCh/dalpha [1/rad]
    chd: float | None = None              # dCh/ddelta [1/rad]
    ch: float | None = None               # hinge-moment coefficient
    hinge_moment_nm: float | None = None  # [N*m]
    details: dict = field(default_factory=dict)      # method-specific intermediate values
    warnings: tuple = ()                  # model/range warnings raised during the run
    error: str | None = None              # set when the condition could not be computed

    @property
    def ok(self) -> bool:
        return self.error is None

    @classmethod
    def failed(cls, method, condition, message):
        return cls(method=method, condition=condition, error=message)


class Solver(ABC):
    """A solver is built once for one aileron (geometry, airfoil) and run many times."""

    name: str = "solver"

    @abstractmethod
    def run(self, condition: FlightCondition) -> HingeMomentResult:
        """Compute derivatives and hinge moment for one flight condition."""