# tests/test_cpacs_edit.py
import pytest

from latte.core.cpacs_edit import set_aileron_hinge

XML = """<cpacs>
<trailingEdgeDevice uID="Flap">
  <outerShape><innerBorder><etaLE>0.1</etaLE><xsiLE>0.8</xsiLE></innerBorder>
  <outerBorder><etaLE>0.5</etaLE><xsiLE>0.8</xsiLE></outerBorder></outerShape>
  <path><innerHingePoint><hingeXsi>0.71</hingeXsi><hingeRelHeight>0.5</hingeRelHeight></innerHingePoint>
  <outerHingePoint><hingeXsi>0.71</hingeXsi><hingeRelHeight>0.5</hingeRelHeight></outerHingePoint></path>
</trailingEdgeDevice>
<trailingEdgeDevice uID="AileronUID">
  <outerShape>
    <innerBorder><etaLE>0.61</etaLE><xsiLE>0.70</xsiLE></innerBorder>
    <outerBorder><etaLE>0.87</etaLE><xsiLE>0.60</xsiLE></outerBorder>
  </outerShape>
  <path>
    <innerHingePoint><hingeXsi>0.71</hingeXsi><hingeRelHeight>0.5</hingeRelHeight></innerHingePoint>
    <outerHingePoint><hingeXsi>0.71</hingeXsi><hingeRelHeight>0.5</hingeRelHeight></outerHingePoint>
  </path>
</trailingEdgeDevice>
</cpacs>"""


def test_hinge_moves_to_requested_fraction_of_the_aileron_chord():
    new, hinge = set_aileron_hinge(XML, "AileronUID", 0.25)
    assert hinge["inner"] == pytest.approx(0.70 + 0.25 * 0.30)     # 0.775
    assert hinge["outer"] == pytest.approx(0.60 + 0.25 * 0.40)     # 0.70
    assert "<hingeXsi>0.775</hingeXsi>" in new
    assert "<hingeXsi>0.7</hingeXsi>" in new


def test_other_devices_and_the_rest_of_the_file_are_untouched():
    new, _ = set_aileron_hinge(XML, "AileronUID", 0.25)
    flap_before = XML[: XML.index('uID="AileronUID"')]
    flap_after = new[: new.index('uID="AileronUID"')]
    assert flap_before == flap_after                                # the Flap block is identical
    assert new.count("<hingeRelHeight>0.5</hingeRelHeight>") == 4


def test_invalid_requests():
    with pytest.raises(KeyError):
        set_aileron_hinge(XML, "Nope", 0.25)
    with pytest.raises(ValueError):
        set_aileron_hinge(XML, "AileronUID", 0.0)
    with pytest.raises(ValueError):
        set_aileron_hinge(XML, "AileronUID", 1.0)


def test_missing_border_is_reported():
    broken = XML.replace("<innerBorder><etaLE>0.61</etaLE><xsiLE>0.70</xsiLE></innerBorder>", "")
    with pytest.raises(ValueError):
        set_aileron_hinge(broken, "AileronUID", 0.25)


NESTED = """<cpacs><trailingEdgeDevice uID="Ail" extra="x">
  <outerShape>
    <innerBorder uID="b1">
      <etaLE><eta>0.61</eta><referenceUID>wing_Cseg</referenceUID></etaLE>
      <xsiLE><xsi>0.70</xsi><referenceUID>wing_Cseg</referenceUID></xsiLE>
    </innerBorder>
    <outerBorder>
      <etaLE><eta>0.87</eta><referenceUID>wing_Cseg</referenceUID></etaLE>
      <xsiLE><xsi>0.60</xsi><referenceUID>wing_Cseg</referenceUID></xsiLE>
    </outerBorder>
  </outerShape>
  <path>
    <innerHingePoint><hingeXsi>0.71</hingeXsi><hingeRelHeight>0.5</hingeRelHeight></innerHingePoint>
    <outerHingePoint><hingeXsi><xsi>0.61</xsi></hingeXsi><hingeRelHeight>0.5</hingeRelHeight></outerHingePoint>
  </path>
</trailingEdgeDevice></cpacs>"""


def test_nested_cpacs_structure_and_attributes_are_supported():
    new, hinge = set_aileron_hinge(NESTED, "Ail", 0.25)
    assert hinge["inner"] == pytest.approx(0.775)
    assert hinge["outer"] == pytest.approx(0.70)
    assert "<hingeXsi>0.775</hingeXsi>" in new                  # plain form edited in place
    assert "<hingeXsi><xsi>0.7</xsi></hingeXsi>" in new         # nested form edited in place
    assert new.count("<referenceUID>wing_Cseg</referenceUID>") == 4   # nothing else touched


def test_unreadable_xsi_gives_a_diagnostic_with_the_content():
    odd = NESTED.replace("<xsi>0.70</xsi>", "<other>seven</other>")
    with pytest.raises(ValueError, match="Content found"):
        set_aileron_hinge(odd, "Ail", 0.25)