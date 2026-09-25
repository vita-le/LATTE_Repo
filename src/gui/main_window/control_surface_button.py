import tkinter as tk
from tkinter import messagebox

from src.core.WingGeo import (
    open_cpacs,
    extract_all_wings,
)

from src.core.aileron import (
    extract_ailerons,
    extract_aileron_geometry,
)

from src.visualization.plot_control_surface import (
    plot_wing_with_ailerons,
    plot_ailerons_top_view,
)

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

        tigl = None
        tixi = None

        try:

            # -------------------------------------------------
            # Open CPACS
            # -------------------------------------------------

            tigl, tixi = open_cpacs(
                cpacs_file,
                configuration,
            )

            # -------------------------------------------------
            # Extract wings
            # -------------------------------------------------

            wings = extract_all_wings(
                tigl
            )

            # -------------------------------------------------
            # Extract ailerons
            # -------------------------------------------------

            ailerons = extract_ailerons(
                tigl,
                cpacs_file,
            )

            if not ailerons:

                messagebox.showinfo(
                    "Control Surfaces",
                    (
                        "No ailerons were found in the "
                        "selected CPACS configuration."
                    ),
                )

                return

            # -------------------------------------------------
            # Find associated wing
            # -------------------------------------------------

            wing = self.find_wing_for_ailerons(
                wings,
                ailerons,
            )

            # -------------------------------------------------
            # Extract aileron geometry
            # -------------------------------------------------

            ailerons_geometry = []

            for aileron in ailerons:

                geometry = extract_aileron_geometry(
                    tigl,
                    aileron,
                )

                ailerons_geometry.append(
                    geometry
                )

            # -------------------------------------------------
            # Close CPACS before plotting
            # -------------------------------------------------

            tigl.close()
            tixi.close()

            tigl = None
            tixi = None

            # -------------------------------------------------
            # 3D plot
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

        except Exception as error:

            messagebox.showerror(
                "Control Surface Error",
                (
                    "Unable to generate the control surface "
                    "visualization.\n\n"
                    f"{type(error).__name__}: {error}"
                ),
            )

        finally:

            # -------------------------------------------------
            # Safety cleanup
            # -------------------------------------------------

            if tigl is not None:

                try:
                    tigl.close()
                except Exception:
                    pass

            if tixi is not None:

                try:
                    tixi.close()
                except Exception:
                    pass