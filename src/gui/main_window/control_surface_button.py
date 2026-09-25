import tkinter as tk
from tkinter import messagebox

from src.gui.style import (
    CARD_BACKGROUND,
    TEXT,
    FONT_BUTTON,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
)


class ControlSurfaceButton:

    def __init__(
        self,
        parent,
        get_cpacs,
    ):

        self.get_cpacs = get_cpacs

        self.button = tk.Button(
            parent,
            text="Control Surfaces",
            command=self.run,
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

    def run(self):

        cpacs_file, configuration = self.get_cpacs()

        if cpacs_file is None:
            return

        messagebox.showinfo(
            "Control Surfaces",
            (
                "Control surface visualization "
                "will be implemented here."
            ),
        )