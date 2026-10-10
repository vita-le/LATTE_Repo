# tests/test_airfoil.py
import math

import numpy as np
import pytest

from latte.core.airfoil import airfoil_properties


def half_thickness(x, t=0.12):
    """NACA 4-digit half-thickness distribution (open trailing edge)."""
    return 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2
                    + 0.2843 * x ** 3 - 0.1015 * x ** 4)


def contour(t=0.12, camber=0.0, n=200, reverse=False):
    """Closed contour TE -> upper -> LE -> lower -> TE (cosine spacing)."""
    beta = np.linspace(0, math.pi, n)
    x = 0.5 * (1 - np.cos(beta))
    yt = half_thickness(x, t)
    zc = camber * 4 * x * (1 - x)                      # simple parabolic camber line
    xs = np.concatenate([x[::-1], x[1:]])
    zs = np.concatenate([(zc + yt)[::-1], (zc - yt)[1:]])
    return (xs[::-1], zs[::-1]) if reverse else (xs, zs)


def expected_tan_half(t, x_start, x_end=0.99):
    return (half_thickness(x_start, t) - half_thickness(x_end, t)) / (x_end - x_start)


def test_naca0012_thickness():
    props = airfoil_properties(*contour(0.12))
    assert props.t_c == pytest.approx(0.12, abs=1e-3)


def test_trailing_edge_angles_match_analytic_values():
    props = airfoil_properties(*contour(0.12))
    for phi, x_start in ((props.phi_te_1_deg, 0.90), (props.phi_te_2_deg, 0.95)):
        assert math.tan(math.radians(phi / 2)) == pytest.approx(
            expected_tan_half(0.12, x_start), rel=2e-2
        )


def test_thicker_airfoil_has_larger_angle():
    thin = airfoil_properties(*contour(0.06))
    thick = airfoil_properties(*contour(0.15))
    assert thick.phi_te_1_deg > thin.phi_te_1_deg
    assert thick.t_c > thin.t_c


def test_camber_does_not_change_thickness_or_angles():
    plain = airfoil_properties(*contour(0.10, camber=0.0))
    cambered = airfoil_properties(*contour(0.10, camber=0.04))
    assert cambered.t_c == pytest.approx(plain.t_c, abs=1e-4)
    assert cambered.phi_te_1_deg == pytest.approx(plain.phi_te_1_deg, abs=0.05)


def test_point_order_and_scale_do_not_matter():
    base = airfoil_properties(*contour(0.12))
    reversed_ = airfoil_properties(*contour(0.12, reverse=True))
    x, z = contour(0.12)
    scaled = airfoil_properties(3.0 * x + 7.0, 3.0 * z)        # chord 3 m, shifted
    for other in (reversed_, scaled):
        assert other.t_c == pytest.approx(base.t_c)
        assert other.phi_te_1_deg == pytest.approx(base.phi_te_1_deg)


def test_too_few_points_rejected():
    with pytest.raises(ValueError):
        airfoil_properties([0, 0.5, 1.0], [0, 0.1, 0])