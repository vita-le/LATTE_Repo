import tkinter as tk

from .cpacs_selector import CPACSSelector
from .geometry_button import GeometryButton
from .control_surface_button import ControlSurfaceButton
from .analysis_button import AnalysisButton

from latte.gui.style import (
    BACKGROUND,
    CARD_BACKGROUND,
    TEXT,
    SECONDARY_TEXT,
    SUCCESS,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_SECTION,
    FONT_STATUS,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)


class MainWindow:
    """Main LATTE application window."""

    def __init__(self, root):

        self.root = root

        self.root.title("LATTE")
        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )
        self.root.minsize(
            750,
            500,
        )

        self.root.configure(
            bg=BACKGROUND
        )

        self.cpacs_file = None
        self.configuration = None

        self.center_window()

        self.create_widgets()

    # ---------------------------------------------------------
    # Window
    # ---------------------------------------------------------

    def center_window(self):

        self.root.update_idletasks()

        width = self.root.winfo_width()
        height = self.root.winfo_height()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    # ---------------------------------------------------------
    # Main UI
    # ---------------------------------------------------------

    def create_widgets(self):

        # =====================================================
        # Header
        # =====================================================

        header = tk.Frame(
            self.root,
            bg=BACKGROUND,
        )

        header.pack(
            fill="x",
            padx=40,
            pady=(35, 25),
        )

        title = tk.Label(
            header,
            text="LATTE",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BACKGROUND,
        )

        title.pack(
            anchor="w"
        )

        subtitle = tk.Label(
            header,
            text="Aircraft Aerodynamic Analysis",
            font=FONT_SUBTITLE,
            fg=SECONDARY_TEXT,
            bg=BACKGROUND,
        )

        subtitle.pack(
            anchor="w",
            pady=(2, 0),
        )

        # =====================================================
        # CPACS section
        # =====================================================

        cpacs_section = tk.Frame(
            self.root,
            bg=CARD_BACKGROUND,
            highlightbackground="#D0D5DD",
            highlightthickness=1,
        )

        cpacs_section.pack(
            fill="x",
            padx=40,
            pady=10,
        )

        cpacs_title = tk.Label(
            cpacs_section,
            text="CPACS MODEL",
            font=FONT_SECTION,
            fg=TEXT,
            bg=CARD_BACKGROUND,
        )

        cpacs_title.pack(
            anchor="w",
            padx=25,
            pady=(20, 10),
        )

        self.cpacs_selector = CPACSSelector(
            cpacs_section,
            self.set_cpacs,
        )

        self.cpacs_selector.pack(
            fill="x",
            padx=15,
            pady=(0, 20),
        )

        # =====================================================
        # Operations section
        # =====================================================

        operations_section = tk.Frame(
            self.root,
            bg=BACKGROUND,
        )

        operations_section.pack(
            fill="x",
            padx=40,
            pady=(25, 10),
        )

        operations_title = tk.Label(
            operations_section,
            text="OPERATIONS",
            font=FONT_SECTION,
            fg=TEXT,
            bg=BACKGROUND,
        )

        operations_title.pack(
            anchor="w",
            pady=(0, 12),
        )

        operations_frame = tk.Frame(
            operations_section,
            bg=BACKGROUND,
        )

        operations_frame.pack(
            fill="x",
        )

        # -----------------------------------------------------
        # Geometry
        # -----------------------------------------------------

        self.geometry_button = GeometryButton(
            operations_frame,
            self.get_cpacs,
        )

        self.geometry_button.pack(
            side="left",
            padx=(0, 10),
            expand=True,
            fill="x",
        )

        # -----------------------------------------------------
        # Control surfaces
        # -----------------------------------------------------

        self.control_surface_button = ControlSurfaceButton(
            operations_frame,
            self.get_cpacs,
        )

        self.control_surface_button.pack(
            side="left",
            padx=10,
            expand=True,
            fill="x",
        )

        # -----------------------------------------------------
        # Analysis
        # -----------------------------------------------------

        self.analysis_button = AnalysisButton(
            operations_frame,
            self.get_cpacs,
        )

        self.analysis_button.pack(
            side="left",
            padx=(10, 0),
            expand=True,
            fill="x",
        )

        # =====================================================
        # Status bar
        # =====================================================

        status_frame = tk.Frame(
            self.root,
            bg=CARD_BACKGROUND,
            highlightbackground="#D0D5DD",
            highlightthickness=1,
        )

        status_frame.pack(
            fill="x",
            padx=40,
            pady=(25, 30),
            side="bottom",
        )

        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=("Segoe UI", 10),
            fg=SECONDARY_TEXT,
            bg=CARD_BACKGROUND,
        )

        self.status_indicator.pack(
            side="left",
            padx=(15, 5),
            pady=12,
        )

        self.status_label = tk.Label(
            status_frame,
            text="Select a CPACS file to begin.",
            font=FONT_STATUS,
            fg=SECONDARY_TEXT,
            bg=CARD_BACKGROUND,
            anchor="w",
        )

        self.status_label.pack(
            side="left",
            fill="x",
            expand=True,
            pady=12,
        )

    # ---------------------------------------------------------
    # CPACS
    # ---------------------------------------------------------

    def set_cpacs(
        self,
        cpacs_file,
        configuration,
    ):

        self.cpacs_file = cpacs_file
        self.configuration = configuration

        self.status_indicator.config(
            fg=SUCCESS
        )

        self.status_label.config(
            text=(
                f"{cpacs_file.name}   |   "
                f"Configuration: {configuration}"
            ),
            fg=TEXT,
        )

        self.geometry_button.enable()
        self.control_surface_button.enable()
        self.analysis_button.enable()

    def get_cpacs(self):

        return (
            self.cpacs_file,
            self.configuration,
        )