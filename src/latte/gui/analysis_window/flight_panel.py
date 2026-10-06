# src/latte/gui/analysis_window/flight_panel.py
"""Tk panel to define a single flight condition or a loop of conditions."""
import tkinter as tk
from tkinter import messagebox

from latte.core.flight_state import build_conditions, flow_summary
from latte.gui.style import (
    CARD_BACKGROUND,
    TEXT,
    SECONDARY_TEXT,
    PRIMARY,
    FONT_SECTION,
    FONT_LABEL,
    FONT_NORMAL,
)

# name, label, default start, default stop, default n
FIELDS = [
    ("mach", "Mach [-]", "0.3", "0.5", "3"),
    ("altitude", "Altitude [m]", "0", "5000", "3"),
    ("alpha", "Alpha [deg]", "0", "6", "3"),
]


class FlightConditionPanel:
    """Reads the fields and builds the list of FlightCondition objects."""

    def __init__(self, parent):
        self.conditions = []

        self.frame = tk.Frame(
            parent,
            bg=CARD_BACKGROUND,
            highlightbackground="#D0D5DD",
            highlightthickness=1,
        )

        tk.Label(
            self.frame, text="FLIGHT CONDITIONS", font=FONT_SECTION,
            fg=TEXT, bg=CARD_BACKGROUND,
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(15, 5))

        # Single / Loop selector
        self.mode = tk.StringVar(value="single")
        mode_row = tk.Frame(self.frame, bg=CARD_BACKGROUND)
        mode_row.grid(row=1, column=0, columnspan=4, sticky="w", padx=20)
        for text, value in (("Single condition", "single"), ("Loop conditions", "loop")):
            tk.Radiobutton(
                mode_row, text=text, value=value, variable=self.mode,
                command=self._on_mode_change, font=FONT_NORMAL,
                fg=TEXT, bg=CARD_BACKGROUND, activebackground=CARD_BACKGROUND,
                selectcolor=CARD_BACKGROUND,
            ).pack(side="left", padx=(0, 15))

        # Column headers
        for col, text in enumerate(("", "Value / Start", "Stop", "Points")):
            tk.Label(
                self.frame, text=text, font=FONT_LABEL,
                fg=SECONDARY_TEXT, bg=CARD_BACKGROUND,
            ).grid(row=2, column=col, sticky="w", padx=(20 if col == 0 else 5, 5))

        # One row of three entries per variable
        self.entries = {}
        for row, (name, label, start, stop, n) in enumerate(FIELDS, start=3):
            tk.Label(
                self.frame, text=label, font=FONT_NORMAL,
                fg=TEXT, bg=CARD_BACKGROUND, anchor="w", width=14,
            ).grid(row=row, column=0, sticky="w", padx=(20, 5), pady=3)
            row_entries = []
            for col, default in enumerate((start, stop, n), start=1):
                entry = tk.Entry(self.frame, width=10, font=FONT_NORMAL)
                entry.insert(0, default)
                entry.grid(row=row, column=col, padx=5, pady=3, sticky="w")
                row_entries.append(entry)
            self.entries[name] = tuple(row_entries)

        # Apply button and result text
        tk.Button(
            self.frame, text="Apply", command=self.apply, font=("Segoe UI", 9, "bold"),
            fg="white", bg=PRIMARY, activebackground=PRIMARY,
            activeforeground="white", relief="flat", cursor="hand2", width=12,
        ).grid(row=6, column=0, sticky="w", padx=20, pady=(10, 5))

        self.summary_label = tk.Label(
            self.frame, text="No flight condition applied yet", font=FONT_NORMAL,
            fg=SECONDARY_TEXT, bg=CARD_BACKGROUND, justify="left", anchor="w",
        )
        self.summary_label.grid(
            row=7, column=0, columnspan=4, sticky="w", padx=20, pady=(0, 15)
        )

        self._on_mode_change()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    # -----------------------------------------------------
    # Behaviour
    # -----------------------------------------------------

    def _on_mode_change(self):
        # Stop and Points are only used in loop mode
        state = "normal" if self.mode.get() == "loop" else "disabled"
        for _, stop_entry, n_entry in self.entries.values():
            stop_entry.config(state=state)
            n_entry.config(state=state)

    def _read(self, name):
        start_entry, stop_entry, n_entry = self.entries[name]
        try:
            start = float(start_entry.get())
            if self.mode.get() == "single":
                return start
            return (start, float(stop_entry.get()), int(n_entry.get()))
        except ValueError:
            raise ValueError(f"Invalid number in field '{name}'") from None

    def get_conditions(self):
        """Return the list of FlightCondition; raises ValueError if input is invalid."""
        return build_conditions(
            self._read("mach"),
            self._read("altitude"),
            self._read("alpha"),
        )

    def apply(self):
        try:
            self.conditions = self.get_conditions()
        except ValueError as error:
            messagebox.showerror("Flight conditions", str(error))
            return

        first = flow_summary(self.conditions[0])
        text = (
            f"{len(self.conditions)} condition(s)\n"
            f"First: V = {first['true_airspeed_m_s']:.1f} m/s,  "
            f"rho = {first['density_kg_m3']:.4f} kg/m3,  "
            f"q = {first['dynamic_pressure_pa']:.0f} Pa"
        )
        self.summary_label.config(text=text, fg=TEXT)