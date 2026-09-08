"""Molex 430450218 — Micro-Fit 3.0, 2-circuit vertical SMT header.

Footprint converted from the LCSC/EasyEDA KiCad footprint for C476811 via
parts2jitx. Two 1.27 x 2.54 mm signal pads (y = +/-4.7 mm) plus two 1.65 x 3.43 mm
mechanical solder tabs (x = +/-3.88 mm). 8.5 A rated. Courtyard 6.67 x 8.8 mm.

Generic 2-pin connector used four times per board: P1/P2 carry (12V, GND) on the
power connectors and (DATA, GND) on the data connectors; solder tabs tie to GND.
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


class SignalPad(Pad):
    """SMD signal pad (1.27 x 2.54 mm)."""

    shape = rectangle(1.27, 2.54)
    soldermask = Soldermask(rectangle(1.27, 2.54))
    paste = Paste(rectangle(1.27, 2.54))


class TabPad(Pad):
    """SMD mechanical solder-tab pad (1.65 x 3.43 mm)."""

    shape = rectangle(1.65, 3.43)
    soldermask = Soldermask(rectangle(1.65, 3.43))
    paste = Paste(rectangle(1.65, 3.43))


class MicroFit3_43045_0218_LP(Landpattern):
    name = "Molex_43045_0218"
    p = {
        1: SignalPad().at(0.0, -4.7),
        2: SignalPad().at(0.0, 4.7),
        3: TabPad().at(-3.88, 0.0, rotate=90),
        4: TabPad().at(3.88, 0.0, rotate=90),
    }
    # Refdes well clear of the signal pads (which reach y~+/-6) and tabs; sits below
    # the part, opposite the design-level function label above it.
    reference_designator = Silkscreen(Text(">REF", 1, Anchor.C).at((0, -8.5)))
    value_label = Custom(Text(">VALUE", 1, Anchor.C).at((0, -10.0)), name="Fab")
    courtyard = Courtyard(rectangle(6.67, 8.8))
    # Silkscreen courtyard shown as CORNER BRACKETS only (the center of each edge
    # is omitted) so the silk never crosses the copper pads/tabs. Box is +/-5.2 x
    # +/-6.5; each L-arm is 2.5 mm.
    courtyard_silk = [
        Silkscreen(Polyline(0.2, [(-2.7, -6.5), (-5.2, -6.5), (-5.2, -4.0)])),
        Silkscreen(Polyline(0.2, [(2.7, -6.5), (5.2, -6.5), (5.2, -4.0)])),
        Silkscreen(Polyline(0.2, [(2.7, 6.5), (5.2, 6.5), (5.2, 4.0)])),
        Silkscreen(Polyline(0.2, [(-2.7, 6.5), (-5.2, 6.5), (-5.2, 4.0)])),
    ]
    # Orientation / pin-1 marker: filled dot by pin 1 (signal pad at y=-4.7) so the
    # connector's placement/rotation is unambiguous on the (otherwise symmetric) silk.
    pin1_marker = Silkscreen(Circle(radius=0.5).at(-2.8, -5.8))


class MicroFit3_43045_0218(jitx.Component):
    """Molex Micro-Fit 3.0 2-circuit vertical SMT header (430450218)."""

    mpn = "430450218"
    manufacturer = "Molex"
    reference_designator_prefix = "J"
    datasheet = "https://www.molex.com/en-us/part-detail/430450218"

    P1 = Port()  # pad 1 — signal A (12V on power conns, DATA on data conns)
    P2 = Port()  # pad 2 — signal B (GND)
    TAB_L = Port()  # pad 3 — solder tab (tie to GND)
    TAB_R = Port()  # pad 4 — solder tab (tie to GND)

    landpattern = MicroFit3_43045_0218_LP()

    symbol = BoxSymbol(
        rows=[
            Row(left=[PinGroup([P1])], right=[PinGroup([P2])]),
            Row(left=[PinGroup([TAB_L])], right=[PinGroup([TAB_R])]),
        ],
    )

    mappings = [
        PadMapping(
            {
                P1: [landpattern.p[1]],
                P2: [landpattern.p[2]],
                TAB_L: [landpattern.p[3]],
                TAB_R: [landpattern.p[4]],
            }
        ),
    ]


Device: type[MicroFit3_43045_0218] = MicroFit3_43045_0218


# --- standalone test design -------------------------------------------------
from jitx.circuit import Circuit  # noqa: E402
from jitx.sample import SampleDesign  # noqa: E402


class _TestCircuit(Circuit):
    j = MicroFit3_43045_0218()


class TestDesign(SampleDesign):
    circuit = _TestCircuit()
