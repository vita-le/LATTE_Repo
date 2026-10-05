# tests/test_cpacs_loading.py
from pathlib import Path

import pytest

from latte.core.cpacs_config import get_cpacs_configurations  # adjust to your real class/function name

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
FILES = ["cs23_base.xml", "DLH_CPACS.xml", "F18SRA_cpacs.xml",
         "GripenECPACS.xml", "TEST_CPACS.xml"]


@pytest.mark.parametrize("name", FILES)
def test_cpacs_opens(name):
    # Each example file must load without raising
    cfg = get_cpacs_configurations(EXAMPLES / name)
    assert cfg is not None