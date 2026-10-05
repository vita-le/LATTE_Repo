import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from latte.core.wing_geo import open_cpacs
from latte.core.cpacs_config import get_cpacs_configurations

from latte.gui.style import (
    CARD_BACKGROUND,
    TEXT,
    SECONDARY_TEXT,
    PRIMARY,
    FONT_LABEL,
    FONT_NORMAL,
)


class CPACSSelector:
    """CPACS file selection and configuration widget."""

    def __init__(
        self,
        parent,
        callback,
    ):

        self.callback = callback

        self.cpacs_file = None
        self.configurations = []
        self.selected_configuration = None

        self.frame = tk.Frame(
            parent,
            bg=CARD_BACKGROUND,
        )

        # =====================================================
        # File row
        # =====================================================

        file_frame = tk.Frame(
            self.frame,
            bg=CARD_BACKGROUND,
        )

        file_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        file_label = tk.Label(
            file_frame,
            text="CPACS file",
            font=FONT_LABEL,
            fg=TEXT,
            bg=CARD_BACKGROUND,
            width=15,
            anchor="w",
        )

        file_label.pack(
            side="left",
        )

        self.label = tk.Label(
            file_frame,
            text="No CPACS file selected",
            font=FONT_NORMAL,
            fg=SECONDARY_TEXT,
            bg="#F4F6F8",
            anchor="w",
            padx=10,
            pady=7,
        )

        self.label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10),
        )

        self.button = tk.Button(
            file_frame,
            text="Browse",
            command=self.select_file,
            width=12,
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=PRIMARY,
            activebackground=PRIMARY,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        )

        self.button.pack(
            side="right",
        )

        # =====================================================
        # Configuration row
        # =====================================================

        self.configuration_frame = tk.Frame(
            self.frame,
            bg=CARD_BACKGROUND,
        )

        configuration_label = tk.Label(
            self.configuration_frame,
            text="Configuration",
            font=FONT_LABEL,
            fg=TEXT,
            bg=CARD_BACKGROUND,
            width=15,
            anchor="w",
        )

        configuration_label.pack(
            side="left",
        )

        self.configuration_var = tk.StringVar()

        self.configuration_menu = tk.OptionMenu(
            self.configuration_frame,
            self.configuration_var,
            "",
        )

        self.configuration_menu.config(
            font=FONT_NORMAL,
            bg="#F4F6F8",
            fg=TEXT,
            activebackground="#E5E7EB",
            relief="flat",
            width=30,
        )

        self.configuration_menu.pack(
            side="left",
        )

    def pack(self, **kwargs):

        self.frame.pack(**kwargs)

    # =========================================================
    # Configuration
    # =========================================================

    def select_configuration(
        self,
        configuration,
    ):

        self.selected_configuration = configuration

        self.configuration_var.set(
            configuration
        )

        if self.cpacs_file is not None:

            self.callback(
                self.cpacs_file,
                self.selected_configuration,
            )

    # =========================================================
    # File selection
    # =========================================================

    def select_file(self):

        filename = filedialog.askopenfilename(
            title="Select CPACS file",
            filetypes=[
                ("CPACS files", "*.xml"),
                ("XML files", "*.xml"),
                ("All files", "*.*"),
            ],
        )

        if not filename:
            return

        cpacs_file = Path(filename)

        # -----------------------------------------------------
        # Find configurations
        # -----------------------------------------------------

        try:

            configurations = get_cpacs_configurations(
                cpacs_file
            )

        except Exception as error:

            messagebox.showerror(
                "CPACS Error",
                (
                    "Unable to read the CPACS configurations.\n\n"
                    f"{error}"
                ),
            )

            return

        if not configurations:

            messagebox.showerror(
                "CPACS Error",
                "No valid CPACS configuration was found.",
            )

            return

        # -----------------------------------------------------
        # Store
        # -----------------------------------------------------

        self.cpacs_file = cpacs_file
        self.configurations = configurations

        # -----------------------------------------------------
        # Single configuration
        # -----------------------------------------------------

        if len(configurations) == 1:

            self.selected_configuration = (
                configurations[0]["uid"]
            )

            self.configuration_frame.pack_forget()

        # -----------------------------------------------------
        # Multiple configurations
        # -----------------------------------------------------

        else:

            menu = self.configuration_menu["menu"]

            menu.delete(
                0,
                "end",
            )

            for configuration in configurations:

                uid = configuration["uid"]
                vehicle_type = configuration["type"]

                label = (
                    f"{uid} ({vehicle_type})"
                )

                menu.add_command(
                    label=label,
                    command=lambda value=uid:
                        self.select_configuration(value),
                )

            self.selected_configuration = (
                configurations[0]["uid"]
            )

            self.configuration_var.set(
                self.selected_configuration
            )

            self.configuration_frame.pack(
                fill="x",
                pady=(5, 0),
            )

        # -----------------------------------------------------
        # Validate with TiGL
        # -----------------------------------------------------

        try:

            tigl, tixi = open_cpacs(
                cpacs_file,
                self.selected_configuration,
            )

            try:

                tigl.getWingCount()

            finally:

                tigl.close()
                tixi.close()

        except Exception as error:

            messagebox.showerror(
                "CPACS Error",
                (
                    "Unable to load the selected CPACS "
                    "configuration.\n\n"
                    f"{error}"
                ),
            )

            return

        # -----------------------------------------------------
        # Update GUI
        # -----------------------------------------------------

        self.label.config(
            text=cpacs_file.name,
            fg=TEXT,
        )

        self.callback(
            cpacs_file,
            self.selected_configuration,
        )