# tests/conftest.py
from pathlib import Path

import pytest

from latte.core.wing_geo import open_cpacs

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
FILES = ["cs23_base.xml", "DLH_CPACS.xml", "F18SRA_cpacs.xml",
         "GripenECPACS.xml", "TEST_CPACS.xml"]


@pytest.fixture(scope="session")
def examples_dir():
    return EXAMPLES


@pytest.fixture(scope="session", params=FILES)
def cpacs_case(request):
    """Open each example once per session; yields (file_path, tigl, tixi)."""
    path = EXAMPLES / request.param
    # open_cpacs returns (tigl, tixi): keep BOTH references alive,
    # because TiGL works on the document owned by TiXI.
    tigl, tixi = open_cpacs(str(path))
    yield path, tigl, tixi
    # Cleanup: close TiGL first, then TiXI
    tigl.close()
    tixi.close()