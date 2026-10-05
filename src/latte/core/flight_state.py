# core/flight_state.py
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class FlightCondition:
    mach: float
    altitude_m: float
    alpha_deg: float
    beta_deg: float = 0.0

    def __post_init__(self):
        # Fail early on invalid input instead of deep inside a solver
        if self.mach <= 0:
            raise ValueError("Mach must be positive")
        if not -1000 <= self.altitude_m <= 25000:
            raise ValueError("Altitude outside the supported ISA range")

def isa_atmosphere(altitude_m: float) -> dict[str, float]:
    """International Standard Atmosphere, troposphere + lower stratosphere."""
    g, R = 9.80665, 287.05287
    if altitude_m <= 11000:
        T = 288.15 - 0.0065 * altitude_m
        p = 101325.0 * (T / 288.15) ** (g / (0.0065 * R))
    else:
        T = 216.65
        p11 = 101325.0 * (216.65 / 288.15) ** (g / (0.0065 * R))
        p = p11 * math.exp(-g * (altitude_m - 11000) / (R * T))
    rho = p / (R * T)
    a = math.sqrt(1.4 * R * T)
    return {"T": T, "p": p, "rho": rho, "a": a}

def true_airspeed(cond: FlightCondition) -> float:
    return cond.mach * isa_atmosphere(cond.altitude_m)["a"]