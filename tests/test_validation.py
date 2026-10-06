# tests/test_validation.py
import pytest

from latte.core.validation import find_missing_airfoils


@pytest.mark.parametrize("name", ["cs23_base.xml", "DLH_CPACS.xml", "GripenECPACS.xml"])
def test_valid_files_have_no_missing_airfoils(examples_dir, name):
    assert find_missing_airfoils(examples_dir / name) == []


def test_f18_missing_airfoil(examples_dir):
    assert "N64210.DAT" in find_missing_airfoils(examples_dir / "F18SRA_cpacs.xml")


def test_test_cpacs_missing_airfoil(examples_dir):
    assert "NACA0012" in find_missing_airfoils(examples_dir / "TEST_CPACS.xml")