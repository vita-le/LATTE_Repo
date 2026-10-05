# analysis/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from latte.core.flight_state import FlightCondition

@dataclass
class HingeMomentResult:
    method: str                                   # "Roskam" or "VLM"
    condition: FlightCondition
    derivatives: dict[str, float] = field(default_factory=dict)
    hinge_moment_nm: float = 0.0

class Solver(ABC):
    name: str

    @abstractmethod
    def run(self, wing_geometry, aileron, condition: FlightCondition) -> HingeMomentResult:
        """Compute derivatives and hinge moment for one flight condition."""