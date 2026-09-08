"""SMCJ12A — Unidirectional 12V TVS diode, DO-214AB (SMC) package.

LCSC C33269, Ruilon SMCJ12A. Clamps transient overvoltages on the 12V supply rail.
Footprint from EasyEDA/LCSC (C33269, ingestion approved for this project).

Pad layout (from EasyEDA footprint SMC_L7.1-W6.2-LS8.1):
  Pad 1 (left,  x=-3.44 mm): Cathode (K) — bar-marked end; tie to 12V.
  Pad 2 (right, x=+3.44 mm): Anode   (A) — tie to GND.
Both pads are 3.03 × 3.82 mm.
"""

import jitx
from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polyline, Text
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row


class _SMCPad(Pad):
    """DO-214AB (SMC) SMD pad: 3.03 × 3.82 mm."""

    shape = rectangle(3.03, 3.82)
    soldermask = Soldermask(rectangle(3.03, 3.82))
    paste = Paste(rectangle(3.03, 3.82))


class SMCJA12A_LP(Landpattern):
    """DO-214AB footprint derived from EasyEDA C33269 (SMC_L7.1-W6.2-LS8.1)."""

    name = "SMC_L7.1-W6.2-LS8.1"
    p = {
        1: _SMCPad().at(-3.44, 0.0),  # Cathode (K) — left pad
        2: _SMCPad().at(3.44, 0.0),   # Anode   (A) — right pad
    }
    silkscreen = [
        # Cathode bar (vertical line near left pad)
        Silkscreen(Polyline(0.25, [(-1.19, 3.11), (-1.19, -3.11)])),
        # Body outline (top/bottom rails + corner stubs)
        Silkscreen(Polyline(0.25, [(-3.6, -3.11), (3.6, -3.11)])),
        Silkscreen(Polyline(0.25, [(-3.6, 3.11), (3.6, 3.11)])),
        Silkscreen(Polyline(0.25, [(-3.6, -2.14), (-3.6, -3.11)])),
        Silkscreen(Polyline(0.25, [(-3.6, 3.11), (-3.6, 2.14)])),
        Silkscreen(Polyline(0.25, [(3.6, -2.14), (3.6, -3.11)])),
        Silkscreen(Polyline(0.25, [(3.6, 3.11), (3.6, 2.14)])),
        # Diode symbol: triangle pointing left (cathode left), bar at x=0
        Silkscreen(Polyline(0.25, [(0.0, 0.0), (1.02, -0.51)])),
        Silkscreen(Polyline(0.25, [(1.02, -0.51), (1.02, 0.51)])),
        Silkscreen(Polyline(0.25, [(1.02, 0.51), (0.0, 0.0)])),
        Silkscreen(Polyline(0.25, [(0.0, -0.51), (0.0, 0.51)])),
        Silkscreen(Polyline(0.25, [(1.52, 0.0), (-0.51, 0.0)])),
    ]
    # Polarity labels outside the courtyard (top edge at y=3.25), readable in 3D/real life
    polarity_k = Silkscreen(Text("K", 0.8, Anchor.C).at(-2.5, 4.0))
    polarity_a = Silkscreen(Text("A", 0.8, Anchor.C).at(1.8, 4.0))
    reference_designator = Silkscreen(Text(">REF", 1, Anchor.C).at(0.0, 5.5))
    value_label = Custom(Text(">VALUE", 1, Anchor.C).at(0.0, -4.5), name="Fab")
    # Courtyard covers full pad extent (±4.955 mm) plus margin
    courtyard = Courtyard(rectangle(10.5, 6.5))


class SMCJA12A(jitx.Component):
    """Ruilon SMCJ12A — 12V unidirectional TVS diode, DO-214AB (SMC). LCSC C33269."""

    mpn = "SMCJ12A"
    manufacturer = "Ruilon"
    reference_designator_prefix = "D"
    datasheet = "https://datasheet.lcsc.com/datasheet/pdf/029721aecff14d6ea9216d2d3a0e82e0.pdf?productCode=C33269"

    CATHODE = Port()  # K — pad 1, x=-3.44 mm; connect to 12V
    ANODE = Port()    # A — pad 2, x=+3.44 mm; connect to GND

    landpattern = SMCJA12A_LP()

    symbol = BoxSymbol(
        rows=[Row(left=[PinGroup([ANODE])], right=[PinGroup([CATHODE])])],
    )

    mappings = [
        PadMapping({
            CATHODE: [landpattern.p[1]],
            ANODE:   [landpattern.p[2]],
        }),
    ]


Device: type[SMCJA12A] = SMCJA12A


# --- standalone test design -------------------------------------------------
from jitx.circuit import Circuit  # noqa: E402
from jitx.sample import SampleDesign  # noqa: E402


class _TestCircuit(Circuit):
    tvs = SMCJA12A()


class TestDesign(SampleDesign):
    circuit = _TestCircuit()
