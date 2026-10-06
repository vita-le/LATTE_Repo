# tests/test_document.py
import pytest

from latte.core.cpacs_document import CPACSDocument
from latte.core.errors import InvalidCPACSError

# file name -> (number of wings, number of ailerons)
VALID = {
    "cs23_base.xml": (4, 1),
    "DLH_CPACS.xml": (3, 2),
    "GripenECPACS.xml": (3, 0),   # valid file without ailerons
}
INVALID = ["F18SRA_cpacs.xml", "TEST_CPACS.xml"]


@pytest.mark.parametrize("name", VALID)
def test_valid_document(examples_dir, name):
    n_wings, n_ailerons = VALID[name]
    with CPACSDocument(examples_dir / name) as doc:
        assert len(doc.wings) == n_wings
        assert len(doc.ailerons) == n_ailerons


def test_aileron_geometry(examples_dir):
    with CPACSDocument(examples_dir / "cs23_base.xml") as doc:
        geo = doc.aileron_geometry(doc.ailerons[0])
        assert len(geo["inner"]["hinge"]) == 3
        assert len(geo["outer"]["hinge"]) == 3


@pytest.mark.parametrize("name", INVALID)
def test_invalid_document_raises_readable_error(examples_dir, name):
    with pytest.raises(InvalidCPACSError) as info:
        CPACSDocument(examples_dir / name)
    # The message must name the problem, not just say "error"
    assert "Airfoil" in str(info.value)


def test_close_is_idempotent(examples_dir):
    doc = CPACSDocument(examples_dir / "cs23_base.xml")
    doc.close()
    doc.close()   # must not raise