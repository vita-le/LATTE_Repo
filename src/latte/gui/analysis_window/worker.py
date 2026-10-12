# src/latte/gui/analysis_window/worker.py
"""Background thread that runs solvers; the Tk window polls .queue (no Tk code here)."""
import queue
import threading

from latte.analysis.runner import run_conditions


class AnalysisWorker:
    """Runs [(label, solver), ...] over the same conditions in a background thread.

    Messages put on .queue:
      ("progress", done, total)
      ("done", {label: [HingeMomentResult]}, cancelled)
      ("error", "ExceptionType: message")     # unexpected failure (a bug)
    """

    def __init__(self, solvers, conditions):
        self.solvers = list(solvers)
        self.conditions = list(conditions)
        self.queue = queue.Queue()
        self._cancel = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def cancel(self):
        self._cancel.set()

    def join(self, timeout=None):
        self._thread.join(timeout)

    def _run(self):
        try:
            total = len(self.solvers) * len(self.conditions)
            offset = 0
            results = {}
            for label, solver in self.solvers:
                results[label] = run_conditions(
                    solver,
                    self.conditions,
                    progress_cb=lambda done, _t, off=offset: self.queue.put(("progress", off + done, total)),
                    should_cancel=self._cancel.is_set,
                )
                offset += len(self.conditions)
            self.queue.put(("done", results, self._cancel.is_set()))
        except Exception as error:                      # a bug: report it, never hang the GUI
            self.queue.put(("error", f"{type(error).__name__}: {error}"))