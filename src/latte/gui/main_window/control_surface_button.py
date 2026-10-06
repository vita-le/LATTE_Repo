import tkinter as tk
from tkinter import messagebox

from latte.core.cpacs_document import CPACSDocument
from latte.core.errors import InvalidCPACSError

from latte.visualization.plot_control_surface import (
    plot_wing_with_ailerons,
    plot_ailerons_top_view,
)

from latte.gui.style import (
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

    # =========================================================
    # Find wing associated with ailerons
    # =========================================================

    def find_wing_for_ailerons(
        self,
        wings,
        ailerons,
    ):
        """
        Find the wing containing the component segment
        used by the ailerons.

        The aileron parent_uid refers to a component
        segment, not directly to a wing UID.
        """

        if not ailerons:

            raise ValueError(
                "No ailerons were found in the selected "
                "CPACS configuration."
            )

        aileron_parent_uids = {
            aileron["parent_uid"]
            for aileron in ailerons
        }

        for wing in wings:

            for segment in wing["segments"]:

                if segment["uid"] in aileron_parent_uids:

                    return wing

        raise ValueError(
            "Could not find the wing associated with "
            "the detected aileron component segment(s): "
            f"{sorted(aileron_parent_uids)}"
        )

    # =========================================================
    # Run
    # =========================================================
    
    def run(self):

        cpacs_file, configuration = self.get_cpacs()

        if cpacs_file is None:
            return

        try:
            # The document closes TiGL/TiXI automatically at the end of the block
            with CPACSDocument(cpacs_file, configuration) as doc:

                wings = doc.wings
                ailerons = doc.ailerons

                if not ailerons:
                    messagebox.showinfo(
                        "Control Surfaces",
                        (
                            "No ailerons were found in the "
                            "selected CPACS configuration."
                        ),
                    )
                    return

                wing = self.find_wing_for_ailerons(wings, ailerons)

                # Plain dictionaries: safe to use after the document is closed
                ailerons_geometry = [
                    doc.aileron_geometry(aileron)
                    for aileron in ailerons
                ]

            # -------------------------------------------------
            # 3D plot (CPACS already closed)
            # -------------------------------------------------

            plot_wing_with_ailerons(
                wing,
                ailerons_geometry,
                configuration,
            )

            # -------------------------------------------------
            # 2D top view
            # -------------------------------------------------

            plot_ailerons_top_view(
                wing,
                ailerons_geometry,
                configuration,
            )

        except InvalidCPACSError as error:
            # Readable message listing the exact problems
            messagebox.showerror("Invalid CPACS file", str(error))

        except Exception as error:
            messagebox.showerror(
                "Control Surface Error",
                (
                    "Unable to generate the control surface "
                    "visualization.\n\n"
                    f"{type(error).__name__}: {error}"
                ),
            )