# src/latte/analysis/roskam/solver.py
"""Semi-empirical (Roskam Part VI) hinge-moment solver."""
import warnings

from latte.analysis.base import HingeMomentResult, Solver
from latte.analysis.hinge_moment import hinge_moment
from latte.analysis.roskam.case import RoskamCase
from latte.analysis.roskam.coefficients import RoskamFlight, hinge_coefficients
from latte.core.flight_state import FlightCondition, reynolds_number


class RoskamSolver(Solver):
    name = "Roskam"

    def __init__(self, case: RoskamCase):
        self.case = case

    def run(self, condition: FlightCondition) -> HingeMomentResult:
        case = self.case
        reynolds = reynolds_number(condition, case.reynolds_length_m)
        flight = RoskamFlight(condition.mach, condition.delta_deg, reynolds)

        # Collect the model/range warnings so the GUI can show them with the result
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            coefficients = hinge_coefficients(case.geometry, case.airfoil, flight)

        ch, moment = hinge_moment(
            coefficients.cha, coefficients.chd, condition,
            case.aileron_area_m2, case.aileron_chord_m, case.offset_nm,
        )
        details = dict(coefficients.values)
        details["Reynolds"] = reynolds
        return HingeMomentResult(
            method=self.name,
            condition=condition,
            cha=coefficients.cha,
            chd=coefficients.chd,
            ch=ch,
            hinge_moment_nm=moment,
            details=details,
            warnings=tuple(dict.fromkeys(str(w.message) for w in caught)),   # unique, ordered
        )