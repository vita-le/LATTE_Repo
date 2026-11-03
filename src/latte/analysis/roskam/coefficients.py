# src/latte/analysis/roskam/coefficients.py
"""Port of Hinge_Coeff.m: Roskam hinge-moment derivatives Cha and Chd.

Every intermediate value keeps the MATLAB name (RoskamCoeff.*), so the two
codes can be compared line by line.
"""
import math
import warnings
from dataclasses import dataclass

from latte.analysis.roskam import charts


class RoskamModelWarning(UserWarning):
    """The model is applied outside the conditions it was derived for."""


@dataclass(frozen=True)
class RoskamGeometry:
    b: float                # wing span [m]
    lambda_c4_deg: float    # sweep of the quarter-chord line [deg]
    lambda_hl_deg: float    # sweep of the hinge line [deg]
    y_i: float              # inboard edge of the aileron, spanwise [m]
    y_o: float              # outboard edge of the aileron, spanwise [m]
    aspect_ratio: float
    c_aileron: float        # control-surface chord (hinge to TE plus balance) [m]
    mac: float              # mean aerodynamic chord [m]
    hinge: float            # hinge position, fraction of c_aileron from the LE
    # Chord used for cf_ratio = c_aileron / reference chord. None -> MAC, like the
    # MATLAB code; pass the local wing chord at the aileron for Roskam's definition.
    cf_reference_chord: float | None = None
    # Absolute airfoil thickness at the hinge line [m], used in the balance ratio
    # (thesis: "absolute thickness of the control surface at the hinge line"). None -> t/c * c_aileron,
    # which is what the MATLAB code does.
    hinge_thickness_m: float | None = None


@dataclass(frozen=True)
class RoskamAirfoil:
    t_c: float              # thickness ratio
    phi_te_1_deg: float     # trailing-edge angle, upper/first value [deg]
    phi_te_2_deg: float     # trailing-edge angle, second value [deg]
    # Nose shape of the control surface: 'sharp', 'elliptic' or 'round'
    # (balance charts); 'elliptic' is what the MATLAB code uses.
    nose_type: str = "elliptic"


@dataclass(frozen=True)
class RoskamFlight:
    mach: float
    delta_deg: float
    reynolds: float         # based on MAC


@dataclass(frozen=True)
class RoskamCoefficients:
    cha: float              # dCh/dalpha [1/rad]
    chd: float              # dCh/ddelta [1/rad]
    values: dict            # all intermediates, MATLAB names (RoskamCoeff.*)


def _tand(angle_deg):
    return math.tan(math.radians(angle_deg))


def _cosd(angle_deg):
    return math.cos(math.radians(angle_deg))


def hinge_coefficients(
    geo: RoskamGeometry,
    airfoil: RoskamAirfoil,
    flight: RoskamFlight,
) -> RoskamCoefficients:
    """Compute Cha and Chd exactly as Hinge_Coeff.m does."""
    if flight.mach >= 1.0:
        raise ValueError("Roskam method is subsonic only: Mach must be < 1")

    # ---- basic derived parameters
    t_c = airfoil.t_c
    cf = geo.c_aileron * (1 - geo.hinge)          # hinge -> TE
    cb = geo.c_aileron * geo.hinge                # LE -> hinge
    reference_chord = geo.cf_reference_chord or geo.mac
    cf_ratio = geo.c_aileron / reference_chord    # NB: MATLAB uses c_aileron, not cf
    eta_i = geo.y_i / (geo.b / 2)
    eta_o = geo.y_o / (geo.b / 2)
    # thickness at the hinge line used by the balance ratio
    tc = geo.hinge_thickness_m if geo.hinge_thickness_m is not None else t_c * geo.c_aileron
    cos_l = _cosd(geo.lambda_c4_deg)
    cos_hl = _cosd(geo.lambda_hl_deg)
    ar = geo.aspect_ratio
    tan_phi1 = _tand(airfoil.phi_te_1_deg / 2)
    tan_phi2 = _tand(airfoil.phi_te_2_deg / 2)
    tan_phi_avg = _tand((airfoil.phi_te_1_deg + airfoil.phi_te_2_deg) / 2 / 2)

    # ---- Cha
    cha_theory = charts.get_chalpha_theory(cf_ratio, t_c)
    cla_theory = charts.get_clalpha_theory(t_c)
    cla_ratio = charts.get_clalpha_correction(tan_phi1, flight.reynolds)
    cha1_ratio = charts.get_chalpha_correction(cf_ratio, cla_ratio)
    cha1 = cha1_ratio * cha_theory

    # Thickness correction (only if t/c and tan(Phi_TE/2) disagree)
    if abs(t_c - tan_phi_avg) < 1e-2:
        check = 0
        cha2 = cha1
    else:
        warnings.warn(
            f"t/c={t_c:.4g} differs from tan(Phi_TE_avg/2)={tan_phi_avg:.4g}: "
            "thickness correction applied",
            RoskamModelWarning, stacklevel=2,
        )
        check = 1
        cha2 = cha1 + 2 * cla_theory * (1 - cla_ratio) * (tan_phi2 - t_c)

    # Balance correction
    br_squared = (cb / cf) ** 2 - (tc / (2 * cf)) ** 2
    if br_squared < 0:
        raise ValueError(
            "Roskam is not applicable: the hinge is too close to the control-surface "
            f"leading edge (cb/cf = {cb / cf:.3f}, it must exceed tc/(2cf) = {tc / (2 * cf):.3f}). "
            "The balance charts need a control surface with aerodynamic balance."
        )
    br = math.sqrt(br_squared)
    cha_balance_ratio = charts.get_balance_effect_chalpha(br, airfoil.nose_type)
    cha_balance = cha2 * cha_balance_ratio

    # Mach correction
    cha_m = cha_balance / math.sqrt(1 - flight.mach ** 2)

    # Finite-wing correction
    term1 = charts.get_ar_correction_alpha(ar)
    b2 = charts.get_b2(cf_ratio, cb / cf)
    kai = charts.get_ka(eta_i)
    kao = charts.get_ka(eta_o)
    ka = (kai * (1 - eta_i) - kao * (1 - eta_o)) / (eta_o - eta_i)
    cla = cla_ratio * cla_theory
    delta_cha = term1 * cla * b2 * ka * cos_l
    cha = ar * cos_l / (ar + 2 * cos_l) * cha_m + delta_cha

    # ---- Chd
    a_d = charts.get_ad(flight.delta_deg, cf_ratio)
    chd1_ratio = charts.get_chdelta_correction(cf_ratio, cla_ratio)
    chd_theory = charts.get_chdelta_theory(cf_ratio, t_c)
    chd1 = chd1_ratio * chd_theory
    cld_theory = charts.get_cldelta_theory(cf_ratio, t_c)
    # NB: MATLAB passes tand(Phi_TE_1/2) as first argument (probably meant cf_ratio)
    cld_ratio = charts.get_cldelta_correction(tan_phi1, cla_ratio)

    if check == 0:
        chd2 = chd1
    else:
        chd2 = chd1 + 2 * cld_theory * (1 - cld_ratio) * (tan_phi2 - t_c)

    chd_balance_ratio = charts.get_balance_effect_chdelta(br, airfoil.nose_type)
    chd_balance = chd2 * chd_balance_ratio
    chd_m = chd_balance / math.sqrt(1 - flight.mach ** 2)

    term2 = charts.get_ar_correction_delta(ar, cf_ratio)
    kdi = charts.get_kd(eta_i)
    kdo = charts.get_kd(eta_o)
    kd = (kdi * (1 - eta_i) - kdo * (1 - eta_o)) / (eta_o - eta_i)
    cld = cld_ratio * cld_theory
    delta_chd = term2 * cld * b2 * kd * cos_l

    chd = cos_l * cos_hl * (
        chd_m + a_d * cha_m * (2 * cos_l) / (ar + 2 * cos_l) + delta_chd
    )

    values = {
        "cf": cf, "cb": cb, "cf_ratio": cf_ratio, "eta_i": eta_i, "eta_o": eta_o, "tc": tc,
        "Cha_theory": cha_theory, "Cla": cla, "Cla_ratio": cla_ratio, "Cla_theory": cla_theory,
        "Cha1_ratio": cha1_ratio, "Cha1": cha1, "Cha2": cha2, "BR": br,
        "Cha_balance_ratio": cha_balance_ratio, "Cha_balance": cha_balance, "Cha_M": cha_m,
        "term1": term1, "B2": b2, "Kai": kai, "Kao": kao, "Ka": ka,
        "Delta_Cha": delta_cha, "Cha_final": cha,
        "a_d": a_d, "Chd1_ratio": chd1_ratio, "Chd_theory": chd_theory, "Chd1": chd1,
        "Cld_theory": cld_theory, "Cld": cld, "Cld_ratio": cld_ratio, "Chd2": chd2,
        "Chd_balance_ratio": chd_balance_ratio, "Chd_balance": chd_balance, "Chd_M": chd_m,
        "term2": term2, "Kdi": kdi, "Kdo": kdo, "Kd": kd,
        "Delta_Chd": delta_chd, "Chd_final": chd,
    }
    return RoskamCoefficients(cha=cha, chd=chd, values=values)