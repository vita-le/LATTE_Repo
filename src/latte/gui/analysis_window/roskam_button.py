import tkinter as tk
from tkinter import messagebox

from latte.gui.style import (
    CARD_BACKGROUND,
    TEXT,
    PRIMARY,
    FONT_BUTTON,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
)


class RoskamButton:

    def __init__(
        self,
        parent,
        cpacs_file,
        configuration,
    ):

        self.cpacs_file = cpacs_file
        self.configuration = configuration

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

    def run(self):

        messagebox.showinfo(
            "Roskam Analysis",
            (
                "Roskam analysis will be implemented here.\n\n"
                f"CPACS: {self.cpacs_file.name}\n"
                f"Configuration: {self.configuration}"
            ),
        )