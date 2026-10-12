# src/latte/gui/analysis_window/results_window.py
"""Progress dialog and results window for hinge-moment analyses."""
import queue
import tkinter as tk
from collections import Counter
from tkinter import filedialog, messagebox, ttk

from latte.analysis.export import write_csv
from latte.gui.style import (
    BACKGROUND,
    CARD_BACKGROUND,
    FONT_NORMAL,
    FONT_SUBTITLE,
    FONT_TITLE,
    PRIMARY,
    SECONDARY_TEXT,
    TEXT,
)

# key, heading, width
COLUMNS = (
    ("mach", "Mach", 70),
    ("altitude", "Altitude [m]", 115),
    ("alpha", "Alpha [deg]", 110),
    ("delta", "Delta [deg]", 110),
    ("cha", "Cha [1/rad]", 115),
    ("chd", "Chd [1/rad]", 115),
    ("ch", "Ch [-]", 100),
    ("moment", "Hinge moment [N*m]", 175),
    ("status", "Status", 260),
)
STATUS_MAX_CHARS = 45           # longer messages are cut in the table


def _button(parent, text, command):
    return tk.Button(
        parent, text=text, command=command, font=("Segoe UI", 9, "bold"), fg="white",
        bg=PRIMARY, activebackground=PRIMARY, activeforeground="white",
        relief="flat", cursor="hand2", width=14,
    )


def format_row(result) -> tuple:
    """Strings shown in the table for one HingeMomentResult."""
    c = result.condition
    head = (f"{c.mach:.3f}", f"{c.altitude_m:.0f}", f"{c.alpha_deg:.2f}", f"{c.delta_deg:.2f}")
    if not result.ok:
        # Short form in the table (text before the first colon); full text in the Warnings tab
        message = result.error.split(":")[0].strip()
        if len(message) > STATUS_MAX_CHARS:
            message = message[:STATUS_MAX_CHARS - 3] + "..."
        return head + ("", "", "", "", message)
    status = "OK" if not result.warnings else f"OK ({len(result.warnings)} warning(s))"
    return head + (
        f"{result.cha:.4f}", f"{result.chd:.4f}", f"{result.ch:.5f}",
        f"{result.hinge_moment_nm:.1f}", status,
    )


class ProgressDialog:
    """Modal progress bar with a Cancel button; polls the worker queue."""

    def __init__(self, parent, worker, on_done, on_error, title="Analysis"):
        self.worker, self.on_done, self.on_error = worker, on_done, on_error
        self._finished = False

        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.resizable(False, False)
        self.window.configure(bg=CARD_BACKGROUND)
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

        self.label = tk.Label(
            self.window, text="Running...", font=FONT_NORMAL, fg=TEXT, bg=CARD_BACKGROUND
        )
        self.label.pack(padx=30, pady=(20, 8))
        self.bar = ttk.Progressbar(self.window, length=360, mode="determinate", maximum=100)
        self.bar.pack(padx=30, pady=4)
        _button(self.window, "Cancel", self.cancel).pack(pady=(10, 20))

        try:
            self.window.grab_set()
        except tk.TclError:          # window not yet viewable (e.g. hidden root): not essential
            pass

        self.worker.start()
        self._poll()

    def cancel(self):
        self.worker.cancel()
        self.label.config(text="Cancelling...")

    def _poll(self):
        try:
            while True:
                message = self.worker.queue.get_nowait()
                kind = message[0]
                if kind == "progress":
                    _, done, total = message
                    self.bar["value"] = 100.0 * done / max(total, 1)
                    self.label.config(text=f"{done} / {total} conditions")
                elif kind == "done":
                    self._close()
                    self.on_done(message[1], message[2])
                    return
                elif kind == "error":
                    self._close()
                    self.on_error(message[1])
                    return
        except queue.Empty:
            pass
        if not self._finished:
            self.window.after(60, self._poll)

    def _close(self):
        self._finished = True
        try:
            self.window.grab_release()
        except tk.TclError:
            pass
        self.window.destroy()


class ResultsWindow:
    """Table of results, inputs and warnings; one selectable entry per aileron."""

    def __init__(self, parent, title, info, cases, results, cancelled=False):
        self.cases, self.results = cases, results
        labels = list(results)

        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("1230x640")
        self.window.minsize(900, 400)
        self.window.configure(bg=BACKGROUND)

        tk.Label(self.window, text=title, font=FONT_TITLE, fg=TEXT, bg=BACKGROUND).pack(
            anchor="w", padx=25, pady=(18, 0)
        )
        subtitle = info + ("   |   CANCELLED: partial results" if cancelled else "")
        tk.Label(
            self.window, text=subtitle, font=FONT_SUBTITLE,
            fg="#B42318" if cancelled else SECONDARY_TEXT, bg=BACKGROUND,
        ).pack(anchor="w", padx=25, pady=(2, 8))

        self.selected = tk.StringVar(value=labels[0])
        if len(labels) > 1:
            row = tk.Frame(self.window, bg=BACKGROUND)
            row.pack(anchor="w", padx=25, pady=(0, 6))
            tk.Label(row, text="Aileron", font=FONT_NORMAL, fg=TEXT, bg=BACKGROUND).pack(side="left")
            box = ttk.Combobox(
                row, textvariable=self.selected, values=labels, state="readonly", width=26
            )
            box.pack(side="left", padx=8)
            box.bind("<<ComboboxSelected>>", lambda _event: self._show())

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=25, pady=6)

        # Tab 1: results table
        table_frame = tk.Frame(notebook, bg=CARD_BACKGROUND)
        notebook.add(table_frame, text="Results")
        self.tree = ttk.Treeview(table_frame, columns=[c[0] for c in COLUMNS], show="headings")
        for key, heading, width in COLUMNS:
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, minwidth=width,
                             anchor="w" if key == "status" else "e", stretch=(key == "status"))
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.tag_configure("error", foreground="#B42318")

        # Tab 2 and 3: inputs and warnings (read-only text)
        self.inputs_text = self._text_tab(notebook, "Inputs")
        self.warnings_text = self._text_tab(notebook, "Warnings")

        buttons = tk.Frame(self.window, bg=BACKGROUND)
        buttons.pack(fill="x", padx=25, pady=(4, 16))
        _button(buttons, "Export CSV", self.export_csv).pack(side="left")
        _button(buttons, "Close", self.window.destroy).pack(side="right")

        self._show()

    @staticmethod
    def _text_tab(notebook, title):
        frame = tk.Frame(notebook, bg=CARD_BACKGROUND)
        notebook.add(frame, text=title)
        text = tk.Text(frame, font=("Consolas", 10), wrap="word", state="disabled",
                       bg=CARD_BACKGROUND, fg=TEXT, relief="flat", padx=12, pady=10)
        text.pack(fill="both", expand=True)
        return text

    @staticmethod
    def _set_text(widget, content):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")

    def _show(self):
        label = self.selected.get()
        results = self.results[label]

        self.tree.delete(*self.tree.get_children())
        for result in results:
            self.tree.insert("", "end", values=format_row(result), tags=("" if result.ok else "error",))

        case = self.cases.get(label)
        if case is not None:
            lines = [f"{name:36s} {value if isinstance(value, str) else format(value, '.5g')}"
                     for name, value in case.summary().items()]
            lines.append(f"{'Offset at alpha=delta=0 [N*m]':36s} {case.offset_nm:g}")
            self._set_text(self.inputs_text, "\n".join(lines))

        counts = Counter(w for r in results for w in r.warnings)
        errors = Counter(r.error for r in results if not r.ok)
        parts = [f"{n} x  {message}" for message, n in errors.items()]
        parts += [f"{n} x  {message}" for message, n in counts.items()]
        self._set_text(self.warnings_text, "\n\n".join(parts) if parts else "No warnings.")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            parent=self.window, title="Export results", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            rows = write_csv(path, self.results)
        except OSError as error:
            messagebox.showerror("Export", f"Unable to write the file.\n\n{error}", parent=self.window)
            return
        messagebox.showinfo("Export", f"{rows} rows written to\n{path}", parent=self.window)