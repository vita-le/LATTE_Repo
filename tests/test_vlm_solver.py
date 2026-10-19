# tests/test_vlm_solver.py
from pathlib import Path

import numpy as np
import pytest

from latte.analysis.vlm.lattice import Lattice
from latte.analysis.vlm.solver import (
    compressibility_factor,
    freestream,
    hinge_moment,
    induced_velocity,
    moment_about_axis,
    panel_forces,
    solve_circulation,
)

DATA = np.load(Path(__file__).parent / "data" / "tornado_lattice_cases.npz")
FAR = 1.0e4


def rectangular_wing(aspect_ratio, nx=4, ny=20, chord=1.0):
    """Flat rectangular wing (chord 1, span = AR), uniform panels, horseshoes in the Tornado layout."""
    span = aspect_ratio * chord
    y_edges = np.linspace(-span / 2, span / 2, ny + 1)
    x_edges = np.linspace(0.0, chord, nx + 1)
    colloc, normals, vortex = [], [], []
    for j in range(ny):
        y0, y1 = y_edges[j], y_edges[j + 1]
        for i in range(nx):
            x0, x1 = x_edges[i], x_edges[i + 1]
            xb = x0 + 0.25 * (x1 - x0)
            colloc.append([x0 + 0.75 * (x1 - x0), 0.5 * (y0 + y1), 0.0])
            normals.append([0.0, 0.0, 1.0])
            vortex.append([[FAR, y0, 0.0], [chord, y0, 0.0], [chord, y0, 0.0], [xb, y0, 0.0],
                           [xb, y1, 0.0], [chord, y1, 0.0], [chord, y1, 0.0], [FAR, y1, 0.0]])
    return Lattice(np.array(colloc), np.array(normals), np.array(vortex)), span * chord


def lift_coefficient(aspect_ratio, alpha_deg, nx=4, ny=20):
    lattice, area = rectangular_wing(aspect_ratio, nx, ny)
    v_inf = freestream(50.0, np.radians(alpha_deg))
    gamma = solve_circulation(lattice, v_inf)
    forces = panel_forces(lattice, gamma, v_inf, rho=1.225)
    return forces[:, 2].sum() / (0.5 * 1.225 * 50.0 ** 2 * area)


def test_lift_slope_of_a_high_aspect_ratio_wing():
    slope = lift_coefficient(20.0, 2.0) / np.radians(2.0)
    helmbold = 2 * np.pi * 20.0 / (2 + np.sqrt(4 + 20.0 ** 2))          # 5.69
    assert slope == pytest.approx(helmbold, rel=0.04)


def test_lift_is_linear_in_alpha_and_zero_at_zero_alpha():
    assert lift_coefficient(8.0, 0.0) == pytest.approx(0.0, abs=1e-12)
    # Fz is the z component of the force: a cos(alpha) factor (0.18% between 2 and 4 deg) breaks exact linearity
    assert lift_coefficient(8.0, 4.0) == pytest.approx(2 * lift_coefficient(8.0, 2.0), rel=5e-3)


def test_lift_slope_grows_with_aspect_ratio():
    assert lift_coefficient(4.0, 2.0) < lift_coefficient(8.0, 2.0) < lift_coefficient(16.0, 2.0)


def test_symmetric_wing_has_symmetric_circulation():
    lattice, _ = rectangular_wing(6.0, nx=3, ny=10)
    gamma = solve_circulation(lattice, freestream(40.0, np.radians(3.0)))
    grid = gamma.reshape(10, 3)
    assert grid == pytest.approx(grid[::-1], rel=1e-9)


def test_a_point_on_a_segment_is_not_singular():
    vortex = np.array([[[0, 0, 0], [1, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0], [3, 0, 0], [3, 0, 0], [4, 0, 0]]], float)
    velocity = induced_velocity(np.array([[2.5, 0.0, 0.0]]), vortex)    # on the bound vortex itself
    assert np.all(np.isfinite(velocity)) and np.allclose(velocity, 0.0)


def test_compressibility_factor():
    assert compressibility_factor(0.0) == 1.0
    assert compressibility_factor(0.6) == pytest.approx(1.25)
    with pytest.raises(ValueError):
        compressibility_factor(1.0)


def test_moment_about_axis():
    forces = np.array([[0.0, 0.0, 10.0], [0.0, 0.0, 5.0]])
    points = np.array([[2.0, 1.0, 0.0], [1.0, 3.0, 0.0]])
    axis_a, axis_b = np.array([0.0, 0.0, 0.0]), np.array([0.0, 4.0, 0.0])        # hinge along y
    # moment about +y of a z force at arm x: r x F = (0*F-.., ) -> -x*Fz : -(2*10) and -(1*5)
    assert moment_about_axis(forces, points, axis_a, axis_b, np.array([0, 1])) == pytest.approx(-25.0)
    assert moment_about_axis(forces, points, axis_a, axis_b, np.array([1])) == pytest.approx(-5.0)


def test_reference_dataset_contents():
    assert len(DATA["cases"]) == 5 and DATA["colloc0"].shape == (256, 3) and DATA["vortex0"].shape == (256, 8, 3)


@pytest.mark.parametrize("k", range(5))
def test_hinge_moment_matches_tornado_on_its_own_lattice(k):
    lattice = Lattice(DATA[f"colloc{k}"], DATA[f"normals{k}"], DATA[f"vortex{k}"])
    speed, rho, alpha, mach, _delta = DATA[f"state{k}"]
    axis_a, axis_b = DATA[f"axis{k}"]
    moment = hinge_moment(lattice, DATA["flap_panels"], axis_a, axis_b, speed, alpha, rho, mach)
    reference = DATA[f"m_ref{k}"][0]
    assert moment == pytest.approx(reference, rel=0.025, abs=5.0)