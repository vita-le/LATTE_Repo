# src/latte/analysis/runner.py
"""Run a solver over a list of flight conditions (single condition = list of length 1)."""
from latte.analysis.base import HingeMomentResult


def run_conditions(solver, conditions, progress_cb=None, should_cancel=None):
    """Run the solver on each condition and return the list of results.

    A condition that cannot be computed (e.g. Mach >= 1 for Roskam) gives a result
    with .error set instead of stopping the whole loop.
    progress_cb(done, total) is called after each condition; should_cancel() -> True
    stops the loop early (the results computed so far are returned).
    """
    results = []
    total = len(conditions)
    for i, condition in enumerate(conditions):
        if should_cancel is not None and should_cancel():
            break
        try:
            results.append(solver.run(condition))
        except (ValueError, ArithmeticError) as error:
            results.append(HingeMomentResult.failed(solver.name, condition, str(error)))
        if progress_cb is not None:
            progress_cb(i + 1, total)
    return results