# src/latte/core/cpacs_edit.py
"""Small text-level edits of CPACS files (the rest of the file is left untouched)."""
import re

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def _element(text, name):
    """First <name ...>...</name> in text (group 1 = inner text)."""
    match = re.search(rf"<{name}\b[^>]*>(.*?)</{name}>", text, re.S)
    if match is None:
        raise ValueError(f"<{name}> not found")
    return match


def _number_span(text, name):
    """(start, end) of the number held by <name> in text, or None.

    Accepts both  <xsiLE>0.7</xsiLE>  and the nested form
    <xsiLE><xsi>0.7</xsi><referenceUID>...</referenceUID></xsiLE>  (also with <eta>).
    """
    el = re.search(rf"<{name}\b[^>]*>(.*?)</{name}>", text, re.S)
    if el is None:
        return None
    inner, offset = el.group(1), el.start(1)
    nested = re.search(rf"<(?:xsi|eta)\b[^>]*>\s*({_NUM})\s*</(?:xsi|eta)>", inner)
    if nested:
        return offset + nested.start(1), offset + nested.end(1)
    plain = re.fullmatch(rf"\s*({_NUM})\s*", inner)
    if plain:
        return offset + plain.start(1), offset + plain.end(1)
    return None


def set_aileron_hinge(cpacs_text: str, aileron_uid: str, fraction: float):
    """Move the hinge line of a trailing-edge device.

    fraction: hinge position as a fraction of the control-surface chord measured
    from its leading edge (0 = hinge on the leading edge, i.e. no nose balance).
    The surface extends from xsiLE to the trailing edge (xsi = 1), so
    hingeXsi = xsiLE + fraction * (1 - xsiLE) on the inner and outer border.

    Returns (new_text, {"inner": hingeXsi, "outer": hingeXsi}).
    """
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must be between 0 and 1 (exclusive)")

    device = re.search(
        rf'(<trailingEdgeDevice\b[^>]*\buID="{re.escape(aileron_uid)}"[^>]*>)(.*?)(</trailingEdgeDevice>)',
        cpacs_text, re.S,
    )
    if device is None:
        raise KeyError(f"trailingEdgeDevice {aileron_uid!r} not found")

    block = device.group(2)
    new_hinge = {}
    for side in ("inner", "outer"):
        border = _element(block, f"{side}Border").group(1)
        span = _number_span(border, "xsiLE")
        if span is None:
            raise ValueError(
                f"{side}Border: cannot read a number from <xsiLE>. Content found: "
                f"{' '.join(border.split())[:300]!r}"
            )
        xsi_le = float(border[span[0]:span[1]])
        new_hinge[side] = float(f"{xsi_le + fraction * (1.0 - xsi_le):.10g}")   # no float noise

        point = _element(block, f"{side}HingePoint")
        point_span = _number_span(point.group(1), "hingeXsi")
        if point_span is None:
            raise ValueError(
                f"{side}HingePoint: cannot read a number from <hingeXsi>. Content found: "
                f"{' '.join(point.group(1).split())[:300]!r}"
            )
        start, end = point.start(1) + point_span[0], point.start(1) + point_span[1]
        block = block[:start] + f"{new_hinge[side]:.10g}" + block[end:]

    new_text = cpacs_text[: device.start(2)] + block + cpacs_text[device.end(2):]
    return new_text, new_hinge
    