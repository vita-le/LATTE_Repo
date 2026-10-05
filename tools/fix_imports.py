# tools/fix_imports.py
"""One-off script: rewrite old 'src.*' imports to 'latte.*'."""
import re
from pathlib import Path

ROOT = Path("src/latte")

# (regex, replacement) pairs, applied in order
PATTERNS = [
    # "from src.core.x import y"  ->  "from latte.core.x import y"
    (re.compile(r"\b(from|import)\s+src\."), r"\1 latte."),
    # Module was renamed WingGeo.py -> wing_geo.py
    (re.compile(r"\blatte\.core\.WingGeo\b"), "latte.core.wing_geo"),
]

for path in ROOT.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    new_text = text
    for pattern, replacement in PATTERNS:
        new_text = pattern.sub(replacement, new_text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"fixed: {path}")