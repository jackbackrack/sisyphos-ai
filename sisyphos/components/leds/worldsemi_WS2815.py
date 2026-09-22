"""Worldsemi WS2815 - Intelligent control 12V addressable RGB LED (5050).

Dual-signal-wire version with signal break-point continuous transmission: each
pixel has a main data input (DIN) and a backup data input (BIN). A pixel's single
data output (DO) drives the NEXT pixel's DIN and the pixel-after-that's BIN
(skip-one redundancy), so a single dead pixel does not break the chain.

Source: Worldsemi/Normand "WS2815 Intelligent control LED integrated light source"
datasheet (datasheets/WS2815.pdf):
  - Pin configuration + PIN Function table, page 2.
  - Mechanical Dimensions + recommended PCB Solder Pad layout, page 2.

Pin function (page 2):
  1 VCC  - IC power supply; suspended or connected with a filter capacitor to GND
  2 VDD  - LED power supply, connect to +12V
  3 DO   - control data signal output
  4 DIN  - control data signal input
  5 GND  - data & power ground
  6 BIN  - backup control data signal input

Recommended PCB land pattern (LCSC C5446699 EasyEDA footprint, cross-checked against
datasheet page 2): six pads, 1.5 mm (X) x 1.1 mm (Y); two columns 4.9 mm apart
(x = +/-2.45); three rows on a 1.6 mm pitch (y = +1.6, 0, -1.6).
"""

from dataclasses import dataclass

from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.feature import Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.property import Property
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Text
from jitx.si import Toleranced
from jitxlib.jlcpcb.part import LCSCPart
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


class RectSMDPad(Pad):
    rect = rectangle(1.5, 1.1)  # PCB solder pad: 1.5 mm (X) x 1.1 mm (Y)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class WS2815_5050(Landpattern):
    """5050 six-pad land pattern from the datasheet recommended PCB layout."""

    _X = 2.45  # column center: 4.9 mm / 2  (LCSC C5446699 footprint)
    _Y = 1.6  # row pitch

    p = {
        1: RectSMDPad().at(_X, -_Y, on=Side.Top),  # VCC  (right, bottom)
        2: RectSMDPad().at(_X, 0.0, on=Side.Top),  # VDD  (right, middle)
        3: RectSMDPad().at(_X, _Y, on=Side.Top),  # DO   (right, top)
        4: RectSMDPad().at(-_X, _Y, on=Side.Top),  # DIN  (left, top)
        5: RectSMDPad().at(-_X, 0.0, on=Side.Top),  # GND  (left, middle)
        6: RectSMDPad().at(-_X, -_Y, on=Side.Top),  # BIN  (left, bottom)
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 3.2))
    # pin-1 (VCC) indicator near the bottom-right pad (outside pad edge at 2.45+0.75=3.2)
    pin1_marker = Silkscreen(Circle(radius=0.15).at(3.7, -1.6))


class WS2815(Component):
    """Worldsemi WS2815 12V dual-signal addressable RGB LED (5050)."""

    manufacturer = "Worldsemi"
    mpn = "WS2815"
    reference_designator_prefix = "D"
    datasheet = "https://www.normandled.com/upload/201808/WS2815%20LED%20Datasheet.pdf"

    # WS2815B-V1, 12V, SMD5050-6P (LCSC C5446699) -- the same LCSC/EasyEDA part
    # the recommended land pattern above was cross-checked against.
    lcsc = LCSCPart("C5446699")

    VCC = Port()  # IC supply (filter cap to GND)
    VDD = Port()  # LED supply, +12V
    DO = Port()  # data output
    DIN = Port()  # data input
    GND = Port()
    BIN = Port()  # backup data input

    landpattern = WS2815_5050()

    symbol = BoxSymbol(
        rows=[
            Row(left=[PinGroup([DIN, BIN])], right=[PinGroup([DO])]),
        ],
        columns=[
            Column(up=[PinGroup([VDD, VCC])], down=[PinGroup([GND])]),
        ],
    )

    mappings = [
        PadMapping(
            {
                VCC: [landpattern.p[1]],
                VDD: [landpattern.p[2]],
                DO: [landpattern.p[3]],
                DIN: [landpattern.p[4]],
                GND: [landpattern.p[5]],
                BIN: [landpattern.p[6]],
            }
        ),
    ]

    @dataclass
    class PowerPin(Property):
        voltage_range: Toleranced

    # Absolute-max VDD 9.5-13.5 V; operating "+12V" (datasheet page 2).
    VDD_power_pin = PowerPin(voltage_range=Toleranced.min_max(9.5, 13.5))


Device: type[WS2815] = WS2815


# --- standalone test design -------------------------------------------------
from jitx.circuit import Circuit  # noqa: E402
from jitx.sample import SampleDesign  # noqa: E402


class _TestCircuit(Circuit):
    dut = WS2815()


class TestDesign(SampleDesign):
    circuit = _TestCircuit()
