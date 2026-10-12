# tests/test_export_worker.py
import csv
import queue

import pytest

from latte.analysis.export import CSV_COLUMNS, write_csv
from latte.analysis.roskam.solver import RoskamSolver
from latte.analysis.runner import run_conditions
from latte.core.flight_state import FlightCondition, build_conditions
from latte.gui.analysis_window.worker import AnalysisWorker
from test_roskam_solver import CASE


def drain(worker, timeout=10.0):
    messages = []
    while True:
        message = worker.queue.get(timeout=timeout)
        messages.append(message)
        if message[0] in ("done", "error"):
            return messages


def test_csv_export(tmp_path):
    conditions = [FlightCondition(0.5, 0.0, 2.0, 0.0, 10.0), FlightCondition(1.3, 0.0, 2.0)]
    results = {"AIL": run_conditions(RoskamSolver(CASE), conditions)}
    path = tmp_path / "out.csv"
    assert write_csv(path, results) == 2

    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert list(rows[0].keys()) == CSV_COLUMNS
    assert rows[0]["aileron"] == "AIL" and rows[0]["status"] == "OK"
    assert float(rows[0]["hinge_moment_Nm"]) == pytest.approx(results["AIL"][0].hinge_moment_nm)
    assert "subsonic" in rows[1]["status"] and rows[1]["Cha_per_rad"] == ""    # failed condition


def test_worker_reports_progress_and_results():
    conditions = build_conditions((0.3, 0.6, 4), 0.0, 2.0, 5.0)
    worker = AnalysisWorker([("A", RoskamSolver(CASE)), ("B", RoskamSolver(CASE))], conditions)
    worker.start()
    messages = drain(worker)
    progress = [m for m in messages if m[0] == "progress"]
    assert [m[1] for m in progress] == list(range(1, 9))         # 2 solvers x 4 conditions
    assert all(m[2] == 8 for m in progress)
    kind, results, cancelled = messages[-1]
    assert kind == "done" and not cancelled
    assert set(results) == {"A", "B"} and len(results["A"]) == 4


def test_worker_cancel_returns_partial_results():
    conditions = build_conditions((0.2, 0.9, 200), 0.0, 2.0, 5.0)
    worker = AnalysisWorker([("A", RoskamSolver(CASE))], conditions)
    worker.cancel()                                              # cancelled before starting
    worker.start()
    kind, results, cancelled = drain(worker)[-1]
    assert kind == "done" and cancelled and len(results["A"]) < 200


def test_worker_reports_unexpected_errors_instead_of_hanging():
    class Broken:
        name = "Broken"

        def run(self, condition):
            raise RuntimeError("bug")

    worker = AnalysisWorker([("A", Broken())], [FlightCondition(0.3, 0.0, 0.0)])
    worker.start()
    kind, message = drain(worker)[-1]
    assert kind == "error" and "RuntimeError: bug" in message