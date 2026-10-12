# tests/test_gui_smoke.py
"""Creates the real Tk widgets (hidden root). Skipped when there is no display."""
import time
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")

from latte.analysis.roskam.solver import RoskamSolver                      # noqa: E402
from latte.analysis.runner import run_conditions                            # noqa: E402
from latte.core.flight_state import FlightCondition                         # noqa: E402
from latte.gui.analysis_window.flight_panel import FlightConditionPanel     # noqa: E402
from latte.gui.analysis_window.results_window import ResultsWindow, format_row  # noqa: E402
from latte.gui.analysis_window.roskam_button import RoskamButton, RoskamOptionsDialog  # noqa: E402
from test_roskam_solver import CASE                                         # noqa: E402


@pytest.fixture
def root():
    try:
        window = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available")
    window.withdraw()
    yield window
    window.destroy()


def toplevels(root):
    return [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]


def test_flight_panel_single_and_loop(root):
    panel = FlightConditionPanel(root)
    single = panel.get_conditions()
    assert len(single) == 1
    assert (single[0].mach, single[0].altitude_m, single[0].alpha_deg, single[0].delta_deg) == (0.3, 0.0, 0.0, 10.0)

    panel.mode.set("loop")
    panel._on_mode_change()
    assert len(panel.get_conditions()) == 3 ** 4                  # mach x altitude x alpha x delta

    panel.entries["delta"][0].delete(0, "end")
    panel.entries["delta"][0].insert(0, "abc")
    with pytest.raises(ValueError, match="delta"):
        panel.get_conditions()


def test_format_row():
    ok = RoskamSolver(CASE).run(FlightCondition(0.5, 0.0, 2.0, 0.0, 10.0))
    assert format_row(ok)[0] == "0.500" and format_row(ok)[-1].startswith("OK (")
    bad = run_conditions(RoskamSolver(CASE), [FlightCondition(1.4, 0.0, 0.0)])[0]
    assert format_row(bad)[4:8] == ("", "", "", "") and "subsonic" in format_row(bad)[-1]


def test_results_window_content(root):
    conditions = [FlightCondition(0.4, 0.0, 0.0, 0.0, 10.0), FlightCondition(0.6, 0.0, 0.0, 0.0, 10.0),
                  FlightCondition(1.3, 0.0, 0.0)]
    results = {"A1": run_conditions(RoskamSolver(CASE), conditions),
               "A2": run_conditions(RoskamSolver(CASE), conditions[:1])}
    window = ResultsWindow(root, "Roskam hinge moments", "info", {"A1": CASE, "A2": CASE}, results)

    assert len(window.tree.get_children()) == 3
    assert "error" in window.tree.item(window.tree.get_children()[2], "tags")
    assert "Aspect ratio" in window.inputs_text.get("1.0", "end")
    assert "subsonic" in window.warnings_text.get("1.0", "end")

    window.selected.set("A2")                                    # switch aileron
    window._show()
    assert len(window.tree.get_children()) == 1


def test_options_dialog_result(root):
    dialog = RoskamOptionsDialog(root)
    dialog.nose.set("round")
    dialog.reference.set("mac")
    dialog.offset.set("-400,5")                                  # decimal comma accepted
    dialog._ok()
    assert dialog.result == {"nose_type": "round", "use_local_chord_ratio": False, "offset_nm": -400.5}


def test_start_analysis_opens_results_window(root):
    panel = FlightConditionPanel(root)
    frame = tk.Frame(root)
    button = RoskamButton(frame, Path("model.xml"), "AircraftModel", panel)
    button.start_analysis({"AIL": CASE}, panel.get_conditions())

    deadline = time.time() + 15
    while time.time() < deadline:
        root.update()
        if any(w.title() == "Roskam hinge moments" for w in toplevels(root)):
            break
        time.sleep(0.02)
    titles = [w.title() for w in toplevels(root)]
    assert "Roskam hinge moments" in titles
    assert "Roskam analysis" not in titles                       # progress dialog closed itself