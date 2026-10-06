# src/latte/core/flight_state.py
"""Flight condition, ISA atmosphere and derived flow quantities."""
import math
import itertools
from dataclasses import dataclass

# ISA formulas below are valid up to 20 km (isothermal layer 11-20 km)
MAX_ALTITUDE_M = 20000.0
MIN_ALTITUDE_M = -1000.0
MAX_CONDITIONS = 5000  # guard against accidental huge loops


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
        if not MIN_ALTITUDE_M <= self.altitude_m <= MAX_ALTITUDE_M:
            raise ValueError(
                f"Altitude must be between {MIN_ALTITUDE_M:.0f} m "
                f"and {MAX_ALTITUDE_M:.0f} m (ISA range supported)"
            )


def isa_atmosphere(altitude_m: float) -> dict[str, float]:
    """International Standard Atmosphere, valid from -1 km to 20 km."""
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


def dynamic_viscosity(temperature_k: float) -> float:
    """Dynamic viscosity [Pa*s] from Sutherland's law."""
    mu_ref, t_ref, s = 1.716e-5, 273.15, 110.4
    return mu_ref * (temperature_k / t_ref) ** 1.5 * (t_ref + s) / (temperature_k + s)


def true_airspeed(cond: FlightCondition) -> float:
    """True airspeed [m/s]."""
    return cond.mach * isa_atmosphere(cond.altitude_m)["a"]


def dynamic_pressure(cond: FlightCondition) -> float:
    """Dynamic pressure q = 0.5 * rho * V^2 [Pa]."""
    rho = isa_atmosphere(cond.altitude_m)["rho"]
    return 0.5 * rho * true_airspeed(cond) ** 2


def reynolds_number(cond: FlightCondition, length_m: float) -> float:
    """Reynolds number based on a reference length (e.g. a chord) [m]."""
    if length_m <= 0:
        raise ValueError("Reference length must be positive")
    atm = isa_atmosphere(cond.altitude_m)
    mu = dynamic_viscosity(atm["T"])
    return atm["rho"] * true_airspeed(cond) * length_m / mu


def flow_summary(cond: FlightCondition, length_m: float | None = None) -> dict[str, float]:
    """All derived quantities in one dict, ready to show in the GUI."""
    atm = isa_atmosphere(cond.altitude_m)
    summary = {
        "temperature_k": atm["T"],
        "pressure_pa": atm["p"],
        "density_kg_m3": atm["rho"],
        "speed_of_sound_m_s": atm["a"],
        "true_airspeed_m_s": true_airspeed(cond),
        "dynamic_pressure_pa": dynamic_pressure(cond),
    }
    if length_m is not None:
        summary["reynolds"] = reynolds_number(cond, length_m)
    return summary

    MAX_CONDITIONS = 5000  # guard against accidental huge loops


def range_values(start: float, stop: float, n: int) -> list[float]:
    """n evenly spaced values from start to stop (both included)."""
    if n < 1:
        raise ValueError("Number of points must be at least 1")
    if n == 1:
        return [start]
    step = (stop - start) / (n - 1)
    return [start + i * step for i in range(n)]


def _as_values(spec) -> list[float]:
    """A plain number gives one value; a (start, stop, n) tuple gives a range."""
    if isinstance(spec, (tuple, list)):
        start, stop, n = spec
        return range_values(float(start), float(stop), int(n))
    return [float(spec)]


def build_conditions(mach, altitude_m, alpha_deg, beta_deg: float = 0.0) -> list[FlightCondition]:
    """Cartesian product of the given values.

    Each of mach, altitude_m, alpha_deg is either a number (single value)
    or a (start, stop, n) tuple (loop). A list of length 1 is a single condition.
    """
    machs = _as_values(mach)
    alts = _as_values(altitude_m)
    alphas = _as_values(alpha_deg)

    total = len(machs) * len(alts) * len(alphas)
    if total > MAX_CONDITIONS:
        raise ValueError(
            f"{total} conditions requested, the maximum is {MAX_CONDITIONS}"
        )

    return [
        FlightCondition(m, h, a, beta_deg)
        for m, h, a in itertools.product(machs, alts, alphas)
    ]