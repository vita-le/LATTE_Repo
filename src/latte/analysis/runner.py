# analysis/runner.py
import numpy as np
from .base import FlightCondition

def make_loop_conditions(mach_range, alt_range, alpha_range):
    """Build the Cartesian product of the given (start, stop, n) ranges."""
    machs = np.linspace(*mach_range)
    alts = np.linspace(*alt_range)
    alphas = np.linspace(*alpha_range)
    return [FlightCondition(m, h, a) for m in machs for h in alts for a in alphas]

def run_loop(solver, wing, aileron, conditions, progress_cb=None):
    results = []
    for i, cond in enumerate(conditions):
        results.append(solver.run(wing, aileron, cond))
        if progress_cb:
            progress_cb(i + 1, len(conditions))   # lets the GUI update a progress bar
    return results