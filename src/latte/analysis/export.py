# src/latte/analysis/export.py
"""Write analysis results to CSV."""
import csv
from pathlib import Path

CSV_COLUMNS = [
    "aileron", "method", "mach", "altitude_m", "alpha_deg", "delta_deg",
    "Cha_per_rad", "Chd_per_rad", "Ch", "hinge_moment_Nm", "status", "warnings",
]


def result_row(label, result) -> dict:
    c = result.condition
    return {
        "aileron": label,
        "method": result.method,
        "mach": c.mach,
        "altitude_m": c.altitude_m,
        "alpha_deg": c.alpha_deg,
        "delta_deg": c.delta_deg,
        "Cha_per_rad": result.cha,
        "Chd_per_rad": result.chd,
        "Ch": result.ch,
        "hinge_moment_Nm": result.hinge_moment_nm,
        "status": "OK" if result.ok else result.error,
        "warnings": " | ".join(result.warnings),
    }


def write_csv(path, results_by_label: dict, delimiter: str = ",") -> int:
    """Write {aileron label: [HingeMomentResult]} to a UTF-8 CSV file; returns the row count."""
    rows = [
        result_row(label, result)
        for label, results in results_by_label.items()
        for result in results
    ]
    with open(Path(path), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, delimiter=delimiter)
        writer.writeheader()
        writer.writerows({k: ("" if v is None else v) for k, v in row.items()} for row in rows)
    return len(rows)