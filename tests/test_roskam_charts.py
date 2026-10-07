# tests/test_roskam_charts.py
import warnings

import pytest

from latte.analysis.roskam.charts import (
    RoskamRangeWarning,
    get_ad,
    get_chalpha_theory,
    get_clalpha_correction,
)


def test_chalpha_theory_values():
    assert get_chalpha_theory(0.288, 0.10) == pytest.approx(-0.51892)
    assert get_chalpha_theory(0.3, 0.0) == pytest.approx(-0.604)


def test_chalpha_theory_warns_out_of_range():
    with pytest.warns(RoskamRangeWarning):
        get_chalpha_theory(0.3, 0.2)


def test_clalpha_correction_on_reference_lines():
    assert get_clalpha_correction(0.1, 1e6) == pytest.approx(0.80)
    assert get_clalpha_correction(0.1, 1e7) == pytest.approx(0.86)


def test_clalpha_correction_interpolates_in_log_re():
    # Half a decade between 1e6 and 1e7: average of the two lines
    assert get_clalpha_correction(0.1, 10 ** 6.5) == pytest.approx(0.83)


def test_clalpha_correction_extrapolates_with_warning():
    with pytest.warns(RoskamRangeWarning):
        value = get_clalpha_correction(0.1, 1e9)
    assert value == pytest.approx(0.93)


def test_in_range_calls_do_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")   # any warning becomes an exception
        get_clalpha_correction(0.1, 5e6)
        get_chalpha_theory(0.288, 0.10)
        get_ad(15.0, 0.25)


def test_ad_grid_points():
    assert get_ad(0.0, 0.3) == pytest.approx(0.56)
    assert get_ad(50.0, 0.4) == pytest.approx(0.40)


def test_ad_interpolates():
    # Midway between cf/c = 0.2 and 0.3, and between 10 and 20 deg
    assert get_ad(15.0, 0.25) == pytest.approx(0.49)


def test_ad_negative_deflection_is_clamped_like_matlab():
    with pytest.warns(RoskamRangeWarning):
        assert get_ad(-10.0, 0.3) == pytest.approx(get_ad(0.0, 0.3))


def test_ad_use_abs():
    assert get_ad(-10.0, 0.3, use_abs=True) == pytest.approx(get_ad(10.0, 0.3))


def test_ad_clamps_out_of_range_with_warning():
    with pytest.warns(RoskamRangeWarning):
        assert get_ad(60.0, 0.5) == pytest.approx(0.40)