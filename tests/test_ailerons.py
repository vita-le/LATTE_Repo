# tests/test_ailerons.py
import pytest

from latte.core.aileron import extract_ailerons, extract_aileron_geometry

KNOWN_BROKEN = {"F18SRA_cpacs.xml", "TEST_CPACS.xml"}
EXPECTED_COUNT = {
    "cs23_base.xml": 1,
    "DLH_CPACS.xml": 2,
    "GripenECPACS.xml": 0,
}


@pytest.fixture
def ailerons(cpacs_case):
    path, tigl, tixi = cpacs_case
    if path.name in KNOWN_BROKEN:
        pytest.xfail(f"{path.name}: invalid CPACS data, not handled yet")
    return tigl, extract_ailerons(tigl, str(path))


def test_aileron_count(cpacs_case, ailerons):
    path, _, _ = cpacs_case
    _, found = ailerons
    assert len(found) == EXPECTED_COUNT[path.name]


def test_aileron_keys(ailerons):
    _, found = ailerons
    for ail in found:
        assert {"uid", "parent_uid", "span", "chord", "hinge"} <= set(ail.keys())


def test_aileron_geometry(ailerons):
    tigl, found = ailerons
    for ail in found:
        geo = extract_aileron_geometry(tigl, ail)
        for side in ("inner", "outer"):
            for point in ("leading_edge", "hinge", "trailing_edge"):
                assert len(geo[side][point]) == 3