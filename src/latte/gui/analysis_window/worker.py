# gui/analysis_window/worker.py
from PySide6.QtCore import QObject, Signal

class AnalysisWorker(QObject):
    progress = Signal(int, int)    # done, total
    finished = Signal(list)        # list of HingeMomentResult

    def __init__(self, solver, wing, aileron, conditions):
        super().__init__()
        self.solver, self.wing, self.aileron, self.conditions = solver, wing, aileron, conditions

    def run(self):
        from latte.analysis.runner import run_loop
        results = run_loop(self.solver, self.wing, self.aileron, self.conditions,
                           progress_cb=lambda d, t: self.progress.emit(d, t))
        self.finished.emit(results)