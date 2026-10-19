# src/latte/analysis/vlm/solver.py
"""Vortex lattice solver: Biot-Savart influence, circulation, forces and hinge moment."""
import math

import numpy as np

from latte.analysis.vlm.lattice import Lattice

_TINY = 1e-12


def induced_velocity(points: np.ndarray, vortex: np.ndarray) -> np.ndarray:
    """Velocity induced at m points by n horseshoes of unit circulation -> (m, n, 3).

    Every horseshoe is the polyline of its 8 points; each straight segment contributes
    with the finite-segment Biot-Savart law (zero-length segments and points lying on
    the segment line contribute nothing).
    """
    p = points[:, None, None, :]                      # (m, 1, 1, 3)
    a = vortex[None, :, :-1, :]                       # (1, n, 7, 3) segment starts
    b = vortex[None, :, 1:, :]                        # segment ends
    r0, r1, r2 = b - a, p - a, p - b
    cross = np.cross(r1, r2)
    cross2 = np.einsum("...k,...k->...", cross, cross)
    n1 = np.linalg.norm(r1, axis=-1)
    n2 = np.linalg.norm(r2, axis=-1)
    dot = (np.einsum("...k,...k->...", r1, r0) / np.maximum(n1, _TINY)
           - np.einsum("...k,...k->...", r2, r0) / np.maximum(n2, _TINY))
    valid = (np.linalg.norm(r0, axis=-1) > _TINY) & (cross2 > _TINY)
    factor = np.where(valid, dot / np.maximum(cross2, _TINY), 0.0)
    return (factor[..., None] * cross).sum(axis=2) / (4.0 * math.pi)


def freestream(speed: float, alpha_rad: float) -> np.ndarray:
    """Velocity of the air relative to the aircraft (x aft, z up)."""
    return speed * np.array([math.cos(alpha_rad), 0.0, math.sin(alpha_rad)])


def solve_circulation(lattice: Lattice, v_inf: np.ndarray) -> np.ndarray:
    """Circulation of every horseshoe from the no-penetration condition."""
    influence = induced_velocity(lattice.colloc, lattice.vortex)         # (n, n, 3)
    matrix = np.einsum("ijk,ik->ij", influence, lattice.normals)
    return np.linalg.solve(matrix, -(lattice.normals @ v_inf))


def panel_forces(lattice: Lattice, gamma: np.ndarray, v_inf: np.ndarray, rho: float) -> np.ndarray:
    """Kutta-Joukowski force on every bound vortex, with the local induced velocity: (n, 3)."""
    mid = lattice.bound_mid
    induced = np.einsum("ijk,j->ik", induced_velocity(mid, lattice.vortex), gamma)
    velocity = v_inf[None, :] + induced
    return rho * gamma[:, None] * np.cross(velocity, lattice.bound_end - lattice.bound_start)


def moment_about_axis(forces, points, axis_a, axis_b, panels) -> float:
    """Moment of the forces of `panels`, applied at `points`, about the line a -> b [N*m]."""
    axis = axis_b - axis_a
    axis = axis / np.linalg.norm(axis)
    arms = points[panels] - axis_a
    return float(np.sum(np.cross(arms, forces[panels]) @ axis))


def compressibility_factor(mach: float) -> float:
    """Prandtl-Glauert factor 1/sqrt(1 - M^2) applied to the loads (matches Tornado)."""
    if not 0.0 <= mach < 1.0:
        raise ValueError("The vortex lattice with Prandtl-Glauert is subsonic only: Mach must be < 1")
    return 1.0 / math.sqrt(1.0 - mach ** 2)


def hinge_moment(lattice, panels, axis_a, axis_b, speed, alpha_rad, rho, mach) -> float:
    """Hinge moment of the panels of a control surface about its hinge line [N*m]."""
    v_inf = freestream(speed, alpha_rad)
    gamma = solve_circulation(lattice, v_inf)
    forces = panel_forces(lattice, gamma, v_inf, rho)
    return moment_about_axis(forces, lattice.bound_mid, axis_a, axis_b, panels) * compressibility_factor(mach)