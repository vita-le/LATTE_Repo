import tkinter as tk

from .roskam_button import RoskamButton
from .tornado_button import TornadoButton
from .flight_panel import FlightConditionPanel

from latte.gui.style import (
    BACKGROUND,
    CARD_BACKGROUND,
    TEXT,
    SECONDARY_TEXT,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_SECTION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)


class AnalysisWindow:
    """LATTE aerodynamic analysis window."""

    def __init__(
        self,
        parent,
        cpacs_file,
        configuration,
    ):

        self.cpacs_file = cpacs_file
        self.configuration = configuration

        self.window = tk.Toplevel(parent)

        self.window.title("LATTE - Analysis")
        self.window.geometry(
            f"{WINDOW_WIDTH - 100}x{WINDOW_HEIGHT - 100}"
        )
        self.window.minsize(
            650,
            450,
        )

        self.window.configure(
            bg=BACKGROUND
        )

        self.center_window()

        self.create_widgets()

    def center_window(self):

        self.window.update_idletasks()

        width = self.window.winfo_width()
        height = self.window.winfo_height()

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.window.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def create_widgets(self):

        header = tk.Frame(
            self.window,
            bg=BACKGROUND,
        )

        header.pack(
            fill="x",
            padx=35,
            pady=(30, 20),
        )

        title = tk.Label(
            header,
            text="Aerodynamic Analysis",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BACKGROUND,
        )

        title.pack(
            anchor="w"
        )

        subtitle = tk.Label(
            header,
            text="Select an analysis method",
            font=FONT_SUBTITLE,
            fg=SECONDARY_TEXT,
            bg=BACKGROUND,
        )

        subtitle.pack(
            anchor="w",
            pady=(2, 0),
        )

        model_section = tk.Frame(
            self.window,
            bg=CARD_BACKGROUND,
            highlightbackground="#D0D5DD",
            highlightthickness=1,
        )

        model_section.pack(
            fill="x",
            padx=35,
            pady=10,
        )

        model_title = tk.Label(
            model_section,
            text="CPACS MODEL",
            font=FONT_SECTION,
            fg=TEXT,
            bg=CARD_BACKGROUND,
        )

        model_title.pack(
            anchor="w",
            padx=20,
            pady=(15, 5),
        )

        model_label = tk.Label(
            model_section,
            text=(
                f"{self.cpacs_file.name}"
                f"   |   Configuration: {self.configuration}"
            ),
            font=FONT_SUBTITLE,
            fg=SECONDARY_TEXT,
            bg=CARD_BACKGROUND,
            anchor="w",
        )

        model_label.pack(
            fill="x",
            padx=20,
            pady=(0, 15),
        )
       
        self.flight_panel = FlightConditionPanel(self.window)

        self.flight_panel.pack(
            fill="x",
            padx=35,
            pady=10,
        )

        analysis_section = tk.Frame(
            self.window,
            bg=BACKGROUND,
        )

        analysis_section.pack(
            fill="x",
            padx=35,
            pady=(25, 10),
        )

        analysis_title = tk.Label(
            analysis_section,
            text="ANALYSIS METHODS",
            font=FONT_SECTION,
            fg=TEXT,
            bg=BACKGROUND,
        )

        analysis_title.pack(
            anchor="w",
            pady=(0, 12),
        )

        buttons_frame = tk.Frame(
            analysis_section,
            bg=BACKGROUND,
        )

        buttons_frame.pack(
            fill="x",
        )

        self.roskam_button = RoskamButton(
            buttons_frame,
            self.cpacs_file,
            self.configuration,
        )

        self.roskam_button.pack(
            side="left",
            padx=(0, 10),
            expand=True,
            fill="x",
        )

        self.tornado_button = TornadoButton(
            buttons_frame,
            self.cpacs_file,
            self.configuration,
        )

        self.tornado_button.pack(
            side="left",
            padx=(10, 0),
            expand=True,
            fill="x",
        )