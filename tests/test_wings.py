# tests/test_wings.py
import pytest

from latte.core.wing_geo import extract_all_wings

# Files known to be broken for now (invalid CPACS data)
KNOWN_BROKEN = {"F18SRA_cpacs.xml", "TEST_CPACS.xml"}


@pytest.fixture
def wings(cpacs_case):
    path, tigl, tixi = cpacs_case
    if path.name in KNOWN_BROKEN:
        pytest.xfail(f"{path.name}: invalid CPACS data, not handled yet")
    return extract_all_wings(tigl)


def test_wings_not_empty(wings):
    assert len(wings) > 0


def test_wing_keys(wings):
    for wing in wings:
        assert {"uid", "span", "area", "segments"} <= set(wing.keys())


def test_wing_dimensions_positive(wings):
    for wing in wings:
        assert wing["span"] > 0
        assert wing["area"] > 0
        assert len(wing["segments"]) >= 1