# src/latte/core/errors.py
"""Project-specific exceptions, so the GUI can show readable messages."""


class LatteError(Exception):
    """Base class for all errors raised by LATTE."""


class InvalidCPACSError(LatteError):
    """The CPACS file is inconsistent and cannot be processed."""

    def __init__(self, filename, problems):
        # 'problems' is a list of human-readable strings
        self.filename = str(filename)
        self.problems = list(problems)
        details = "\n".join(f" - {p}" for p in self.problems)
        super().__init__(f"Invalid CPACS file {self.filename}:\n{details}")