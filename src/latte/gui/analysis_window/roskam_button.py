# src/latte/gui/analysis_window/roskam_button.py
"""Roskam analysis button: options, case building, background run and results."""
import tkinter as tk
from tkinter import messagebox

from latte.analysis.roskam.solver import RoskamSolver
from latte.gui.analysis_window.results_window import ProgressDialog, ResultsWindow
from latte.gui.analysis_window.worker import AnalysisWorker
from latte.gui.style import (
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
    CARD_BACKGROUND,
    FONT_BUTTON,
    FONT_NORMAL,
    PRIMARY,
    SECONDARY_TEXT,
    TEXT,
)


class RoskamOptionsDialog:
    """Modal dialog: nose type, cf/c definition and constant hinge-moment offset."""

    NOSE_TYPES = ("elliptic", "round", "sharp")

    def __init__(self, parent):
        self.result = None
        self.window = tk.Toplevel(parent)
        self.window.title("Roskam options")
        self.window.resizable(False, False)
        self.window.configure(bg=CARD_BACKGROUND)
        self.window.transient(parent)

        self.nose = tk.StringVar(value="elliptic")
        self.reference = tk.StringVar(value="local")
        self.offset = tk.StringVar(value="0")

        body = tk.Frame(self.window, bg=CARD_BACKGROUND)
        body.pack(padx=25, pady=(20, 8))

        def label(row, text):
            tk.Label(body, text=text, font=FONT_NORMAL, fg=TEXT, bg=CARD_BACKGROUND,
                     anchor="w").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 15))

        label(0, "Nose shape of the control surface")
        menu = tk.OptionMenu(body, self.nose, *self.NOSE_TYPES)
        menu.config(font=FONT_NORMAL, bg="#F4F6F8", relief="flat", width=12)
        menu.grid(row=0, column=1, sticky="w")

        label(1, "cf/c reference chord")
        ref_frame = tk.Frame(body, bg=CARD_BACKGROUND)
        ref_frame.grid(row=1, column=1, sticky="w")
        for text, value in (("Local wing chord", "local"), ("MAC", "mac")):
            tk.Radiobutton(
                ref_frame, text=text, value=value, variable=self.reference, font=FONT_NORMAL,
                fg=TEXT, bg=CARD_BACKGROUND, activebackground=CARD_BACKGROUND,
                selectcolor=CARD_BACKGROUND,
            ).pack(anchor="w")

        label(2, "Hinge-moment offset [N*m]")
        tk.Entry(body, textvariable=self.offset, width=12, font=FONT_NORMAL).grid(
            row=2, column=1, sticky="w")

        tk.Label(
            self.window, text="Offset = hinge moment at alpha = delta = 0 (default 0).",
            font=("Segoe UI", 9), fg=SECONDARY_TEXT, bg=CARD_BACKGROUND,
        ).pack(padx=25, anchor="w")

        buttons = tk.Frame(self.window, bg=CARD_BACKGROUND)
        buttons.pack(pady=(10, 20))
        for text, command in (("Run", self._ok), ("Cancel", self.window.destroy)):
            tk.Button(
                buttons, text=text, command=command, width=10, font=("Segoe UI", 9, "bold"),
                fg="white", bg=PRIMARY, activebackground=PRIMARY, activeforeground="white",
                relief="flat", cursor="hand2",
            ).pack(side="left", padx=8)

    def _ok(self):
        try:
            offset = float(self.offset.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Roskam options", "The offset must be a number.", parent=self.window)
            return
        self.result = {
            "nose_type": self.nose.get(),
            "use_local_chord_ratio": self.reference.get() == "local",
            "offset_nm": offset,
        }
        self.window.destroy()

    def show(self):
        try:
            self.window.grab_set()
        except tk.TclError:
            pass
        self.window.wait_window()
        return self.result


class RoskamButton:

    def __init__(self, parent, cpacs_file, configuration, flight_panel=None):
        self.cpacs_file = cpacs_file
        self.configuration = configuration
        self.flight_panel = flight_panel

        self.button = tk.Button(
            parent,
            text="Roskam Analysis",
            command=self.run,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            font=FONT_BUTTON,
            bg=CARD_BACKGROUND,
            fg=TEXT,
            activebackground=PRIMARY,
            activeforeground="white",
            disabledforeground="#98A2B3",
            relief="solid",
            bd=1,
            cursor="hand2",
        )

    def pack(self, **kwargs):
        self.button.pack(**kwargs)

    @property
    def toplevel(self):
        return self.button.winfo_toplevel()

    # -----------------------------------------------------
    # Flow: conditions -> options -> cases -> background run -> results
    # -----------------------------------------------------

    def run(self):
        if self.flight_panel is None:
            messagebox.showerror("Roskam Analysis", "No flight-condition panel is connected.")
            return
        try:
            conditions = self.flight_panel.get_conditions()
        except ValueError as error:
            messagebox.showerror("Flight conditions", str(error))
            return

        options = RoskamOptionsDialog(self.toplevel).show()
        if options is None:
            return

        cases = self.build_cases(options)
        if cases:
            self.start_analysis(cases, conditions)

    def build_cases(self, options):
        """One RoskamCase per aileron of the file; None if nothing can be analysed."""
        # Imported here: they need TiGL, which is only loaded when an analysis starts
        from latte.analysis.roskam.case import build_case
        from latte.core.cpacs_document import CPACSDocument
        from latte.core.errors import InvalidCPACSError

        cases, problems = {}, []
        self.button.config(cursor="watch")
        self.button.update_idletasks()
        try:
            with CPACSDocument(self.cpacs_file, self.configuration) as doc:
                ailerons = doc.ailerons
                if not ailerons:
                    messagebox.showinfo(
                        "Roskam Analysis", "No ailerons were found in the selected CPACS configuration."
                    )
                    return None
                for aileron in ailerons:
                    try:
                        cases[aileron["uid"]] = build_case(doc, aileron, **options)
                    except (ValueError, KeyError, NotImplementedError) as error:
                        problems.append(f"{aileron['uid']}: {error}")
        except InvalidCPACSError as error:
            messagebox.showerror("Invalid CPACS file", str(error))
            return None
        except Exception as error:
            messagebox.showerror(
                "Roskam Analysis", f"Unable to read the geometry.\n\n{type(error).__name__}: {error}"
            )
            return None
        finally:
            self.button.config(cursor="hand2")

        if problems:
            kind = messagebox.showwarning if cases else messagebox.showerror
            kind("Roskam Analysis", ("Some ailerons were skipped:\n\n" if cases else "") + "\n".join(problems))
        return cases or None

    def start_analysis(self, cases, conditions):
        """Run the solver in a background thread and open the results when finished."""
        worker = AnalysisWorker(
            [(label, RoskamSolver(case)) for label, case in cases.items()], conditions
        )
        info = (f"{self.cpacs_file.name}   |   Configuration: {self.configuration}   |   "
                f"{len(conditions)} condition(s)")

        def on_done(results, cancelled):
            ResultsWindow(self.toplevel, "Roskam hinge moments", info, cases, results, cancelled)

        def on_error(message):
            messagebox.showerror("Roskam Analysis", f"Unexpected error:\n\n{message}")

        ProgressDialog(self.toplevel, worker, on_done, on_error, title="Roskam analysis")