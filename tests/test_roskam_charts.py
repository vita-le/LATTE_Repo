# tests/test_roskam_charts.py
import warnings

import pytest

from latte.analysis.roskam import charts as c
from latte.analysis.roskam.charts import RoskamRangeWarning


# ---- Cl_alpha charts -------------------------------------------------------
def test_clalpha_theory_ends():
    assert c.get_clalpha_theory(0.0) == pytest.approx(6.28)
    assert c.get_clalpha_theory(0.2) == pytest.approx(7.30)


def test_clalpha_correction_reference_lines_and_log_interpolation():
    assert c.get_clalpha_correction(0.1, 1e6) == pytest.approx(0.80)
    assert c.get_clalpha_correction(0.1, 1e7) == pytest.approx(0.86)
    assert c.get_clalpha_correction(0.1, 10 ** 6.5) == pytest.approx(0.83)


def test_clalpha_correction_extrapolates_with_warning():
    with pytest.warns(RoskamRangeWarning):
        assert c.get_clalpha_correction(0.1, 1e9) == pytest.approx(0.93)


# ---- Ch_alpha charts -------------------------------------------------------
def test_chalpha_theory_values():
    assert c.get_chalpha_theory(0.288, 0.10) == pytest.approx(-0.51892)
    assert c.get_chalpha_theory(0.3, 0.0) == pytest.approx(-0.604)
    with pytest.warns(RoskamRangeWarning):
        c.get_chalpha_theory(0.3, 0.2)


def test_chalpha_correction():
    assert c.get_chalpha_correction(0.1, 0.7) == pytest.approx(-0.11)
    assert c.get_chalpha_correction(0.4, 1.0) == pytest.approx(1.0)
    assert c.get_chalpha_correction(0.15, 0.7) == pytest.approx(-0.0665)
    with pytest.warns(RoskamRangeWarning):
        assert c.get_chalpha_correction(0.5, 1.2) == pytest.approx(1.0)


def test_balance_effect_chalpha():
    assert c.get_balance_effect_chalpha(0.17, "elliptic") == pytest.approx(0.90)
    assert c.get_balance_effect_chalpha(0.5, "elliptic") == pytest.approx(0.20)
    assert c.get_balance_effect_chalpha(0.335, "elliptic") == pytest.approx(0.55)
    # Linear extrapolation below 0.18 is allowed (chart range 0.1-0.5): no warning
    assert c.get_balance_effect_chalpha(0.1, "sharp") == pytest.approx(1.175)
    with pytest.warns(RoskamRangeWarning):   # below 0.1 the chart is not covered
        assert c.get_balance_effect_chalpha(0.05, "sharp") == pytest.approx(1.284375)
    with pytest.raises(ValueError):
        c.get_balance_effect_chalpha(0.3, "pointy")


def test_ar_correction_alpha_hits_data_points():
    assert c.get_ar_correction_alpha(4) == pytest.approx(0.011)
    assert c.get_ar_correction_alpha(10) == pytest.approx(0.0035)
    value = c.get_ar_correction_alpha(5.0)
    assert 0.007 < value < 0.011          # between neighbouring data points


def test_b2_hits_data_points():
    assert c.get_b2(0.2, 0.3) == pytest.approx(0.78)
    assert c.get_b2(0.05, 0.0) == pytest.approx(0.50)
    assert c.get_b2(0.6, 0.6) == pytest.approx(0.98)


def test_b2_between_nodes_stays_between_neighbours():
    value = c.get_b2(0.288, 1 / 3)
    assert 0.78 < value < 1.10


def test_ka_hits_data_points():
    assert c.get_ka(0.4) == pytest.approx(1.7)
    assert c.get_ka(1.0) == pytest.approx(4.3)


# ---- Ch_delta charts -------------------------------------------------------
def test_ad():
    assert c.get_ad(0.0, 0.3) == pytest.approx(0.56)
    assert c.get_ad(15.0, 0.25) == pytest.approx(0.49)
    assert c.get_ad(-10.0, 0.3, use_abs=True) == pytest.approx(c.get_ad(10.0, 0.3))
    with pytest.warns(RoskamRangeWarning):   # negative delta clamped to 0, like MATLAB
        assert c.get_ad(-10.0, 0.3) == pytest.approx(c.get_ad(0.0, 0.3))
    with pytest.warns(RoskamRangeWarning):
        assert c.get_ad(60.0, 0.5) == pytest.approx(0.40)


def test_chdelta_theory():
    assert c.get_chdelta_theory(0.1, 0.0) == pytest.approx(-0.88)
    assert c.get_chdelta_theory(0.4, 0.15) == pytest.approx(-0.89)
    assert c.get_chdelta_theory(0.15, 0.0) == pytest.approx(-0.895)


def test_chdelta_correction():
    assert c.get_chdelta_correction(0.1, 0.6) == pytest.approx(0.66)
    assert c.get_chdelta_correction(0.4, 1.0) == pytest.approx(1.0)
    assert c.get_chdelta_correction(0.25, 0.6) == pytest.approx(0.56)


def test_cldelta_theory():
    assert c.get_cldelta_theory(1.0, 0.05) == pytest.approx(7.8)
    assert c.get_cldelta_theory(0.3, 0.065) == pytest.approx(7.95 * 0.3 ** 0.6)


def test_cldelta_correction():
    assert c.get_cldelta_correction(0.1, 0.7) == pytest.approx(0.15)
    assert c.get_cldelta_correction(0.6, 1.0) == pytest.approx(1.0)
    assert c.get_cldelta_correction(0.15, 0.7) == pytest.approx(0.19)


def test_balance_effect_chdelta():
    assert c.get_balance_effect_chdelta(0.30, "elliptic") == pytest.approx(0.70)
    assert c.get_balance_effect_chdelta(0.50, "low-drag") == pytest.approx(0.0)
    with pytest.raises(ValueError):
        c.get_balance_effect_chdelta(0.3, "pointy")


def test_ar_correction_delta():
    assert c.get_ar_correction_delta(4, 0.4) == pytest.approx(0.0155)
    assert c.get_ar_correction_delta(10, 0.6) == pytest.approx(0.0040)
    assert c.get_ar_correction_delta(2, 0.3) == pytest.approx(0.0330)   # linear in cf/c
    with pytest.warns(RoskamRangeWarning):
        assert c.get_ar_correction_delta(12, 0.4) == pytest.approx(0.0048)


def test_kd():
    assert c.get_kd(0.9) == pytest.approx(3.60)
    with pytest.warns(RoskamRangeWarning):
        assert c.get_kd(1.2) == pytest.approx(4.45)


# ---- General ---------------------------------------------------------------
def test_typical_in_range_inputs_do_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")    # any warning becomes an exception
        c.get_clalpha_correction(0.1, 5e6)
        c.get_chalpha_theory(0.288, 0.10)
        c.get_ad(15.0, 0.25)
        c.get_b2(0.288, 1 / 3)
        c.get_ka(0.5)
        c.get_kd(0.5)
        c.get_balance_effect_chdelta(0.3)