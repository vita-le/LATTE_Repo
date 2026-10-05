import tkinter as tk

from latte.gui.analysis_window.window_2 import AnalysisWindow

from latte.gui.style import (
    CARD_BACKGROUND,
    TEXT,
    FONT_BUTTON,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
)


class AnalysisButton:

    def __init__(
        self,
        parent,
        get_cpacs,
    ):

        self.get_cpacs = get_cpacs

        self.button = tk.Button(
            parent,
            text="Analysis",
            command=self.open_analysis,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            font=FONT_BUTTON,
            bg=CARD_BACKGROUND,
            fg=TEXT,
            activebackground="#1F5A7A",
            activeforeground="white",
            disabledforeground="#98A2B3",
            relief="solid",
            bd=1,
            cursor="hand2",
        )

    def pack(self, **kwargs):

        self.button.pack(**kwargs)

    def enable(self):

        self.button.config(
            state="normal"
        )

    def open_analysis(self):

        cpacs_file, configuration = self.get_cpacs()

        if cpacs_file is None:
            return

        AnalysisWindow(
            self.button.winfo_toplevel(),
            cpacs_file,
            configuration,
        )