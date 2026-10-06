import tkinter as tk
from tkinter import messagebox

from latte.visualization.plot_wing import plot_wing_geometry
from latte.core.cpacs_document import CPACSDocument
from latte.core.errors import InvalidCPACSError

from latte.gui.style import (
    CARD_BACKGROUND,
    PRIMARY,
    PRIMARY_HOVER,
    TEXT,
    FONT_BUTTON,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
)


class GeometryButton:

    def __init__(
        self,
        parent,
        get_cpacs,
    ):

        self.get_cpacs = get_cpacs

        self.button = tk.Button(
            parent,
            text="3D Geometry",
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

    def enable(self):

        self.button.config(
            state="normal"
        )
        
    def run(self):

        cpacs_file, configuration = self.get_cpacs()

        if cpacs_file is None:
            return

        try:
            # The document closes TiGL/TiXI automatically at the end of the block
            with CPACSDocument(cpacs_file, configuration) as doc:
                wings = doc.wings  # plain dictionaries, safe after closing

            # Plot after the CPACS is closed
            plot_wing_geometry(wings, configuration)

        except InvalidCPACSError as error:
            # Readable message listing the exact problems
            messagebox.showerror("Invalid CPACS file", str(error))

        except Exception as error:
            messagebox.showerror(
                "Visualization Error",
                (
                    "Unable to generate the 3D geometry.\n\n"
                    f"{type(error).__name__}: {error}"
                ),
            )