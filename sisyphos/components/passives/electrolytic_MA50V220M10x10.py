"""MA50V220M10x10 - 220 uF 50 V SMD aluminum electrolytic capacitor (10x10 mm).

Modeled as a custom polarized component (own ports/symbol/silk) from the LCSC/EasyEDA
footprint for C46550473, because the parts-DB polarized-capacitor path is broken in
this JITX build (PolarizedCapacitorSymbol .p bug). Footprint: two 4.5 x 1.65 mm pads
at x = +/-4.5 (9 mm pitch, matching the in-stock LCSC C3358 land pattern); 10.3 mm
body. Pad 1 = anode (+), pad 2 = cathode (-).
"""

import jitx
from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Polyline, Text
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row


class ElecPad(Pad):
    """SMD pad (4.5 x 1.65 mm)."""

    shape = rectangle(4.5, 1.65)
    soldermask = Soldermask(rectangle(4.5, 1.65))
    paste = Paste(rectangle(4.5, 1.65))


class MA50V220M10x10_LP(Landpattern):
    name = "CAP-SMD_BD10.0-L10.3-W10.3"
    p = {
        1: ElecPad().at(-4.5, 0.0),  # anode (+)  — 9 mm pitch (LCSC C3358)
        2: ElecPad().at(4.5, 0.0),  # cathode (-) — 9 mm pitch (LCSC C3358)
    }
    # Body outline (chamfered top-left/bottom-left), split top/bottom to leave gaps
    # for the pads — copied from the source footprint.
    silkscreen = [
        Silkscreen(
            Polyline(
                0.15,
                [
                    (5.23, 0.85),
                    (5.23, 5.23),
                    (-3.66, 5.23),
                    (-5.23, 3.66),
                    (-5.23, 0.85),
                ],
            )
        ),
        Silkscreen(
            Polyline(
                0.15,
                [
                    (5.23, -0.85),
                    (5.23, -5.23),
                    (-3.66, -5.23),
                    (-5.23, -3.66),
                    (-5.23, -0.85),
                ],
            )
        ),
        # '+' near the anode (pad 1, left)
        Silkscreen(Polyline(0.2, [(-4.22, 1.4), (-4.22, 3.4)])),
        Silkscreen(Polyline(0.2, [(-4.85, 2.4), (-3.6, 2.4)])),
        # '-' near the cathode (pad 2, right)
        Silkscreen(Polyline(0.2, [(3.6, 2.4), (4.85, 2.4)])),
    ]
    pin1_marker = Silkscreen(Circle(radius=0.3).at(-5.45, 5.15))
    reference_designator = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 6.2))
    value_label = Custom(Text(">VALUE", 1.0, Anchor.C).at(0.0, -6.2), name="Fab")
    courtyard = Courtyard(rectangle(14.0, 10.6))  # ±7.0 encloses ±6.75 pad reach


class MA50V220M10x10(jitx.Component):
    """jieerrui MA50V220M10x10 - 220 uF 50 V aluminum electrolytic (10x10 SMD)."""

    manufacturer = "jieerrui"
    mpn = "MA50V220M10x10"
    reference_designator_prefix = "C"
    datasheet = "https://www.lcsc.com/product-detail/C46550473.html"

    ANODE = Port()  # + (pad 1)
    CATHODE = Port()  # - (pad 2)

    landpattern = MA50V220M10x10_LP()

    symbol = BoxSymbol(
        rows=[Row(left=[PinGroup([ANODE])], right=[PinGroup([CATHODE])])],
    )

    mappings = [
        PadMapping({ANODE: [landpattern.p[1]], CATHODE: [landpattern.p[2]]}),
    ]


Device: type[MA50V220M10x10] = MA50V220M10x10


# --- standalone test design -------------------------------------------------
from jitx.circuit import Circuit  # noqa: E402
from jitx.sample import SampleDesign  # noqa: E402


class _TestCircuit(Circuit):
    c = MA50V220M10x10()


class TestDesign(SampleDesign):
    circuit = _TestCircuit()
