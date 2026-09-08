"""The 8x8 diamond LED panel: 64 WS2815 LEDs in a serpentine chain.

Each LED is placed on the rhombic diamond lattice (see geometry.py), rotated 45 deg,
with its own 100 nF VCC filter capacitor (per the datasheet) placed adjacent and
explicitly routed VCC pad -> cap terminal.

The WS2815 is a dual-signal-wire part with skip-one backup: each pixel's data output
(DO) drives the NEXT pixel's main input (DIN) and the pixel-after-that's backup input
(BIN). A single dead pixel therefore does not break the chain. All signals are 12V;
incoming data is level-shifted off-board.
"""

import math

from jitx.anchor import Anchor
from jitx.circuit import Circuit, Route
from jitx.feature import Silkscreen
from jitx.net import Port
from jitx.shapes.primitive import Text
from jitx.transform import Transform
from jitxlib.parts import Capacitor, CapacitorQuery

from ..components.leds.worldsemi_WS2815 import WS2815
from ..geometry import (
    GRID_N,
    GRID_PITCH,
    VIA_OFFSET,
    decoupling_cap_layout,
    diamond_grid_layout,
    led_via_positions,
)
from ..substrate import RegularVia

_TOP = 0  # top copper layer (LEDs, caps, vias, data traces)


class LedDiamond(Circuit):
    """Serpentine-chained 8x8 WS2815 diamond array with per-LED VCC decoupling."""

    PWR_HI = Port()  # 12V (LED VDD supply)
    GND = Port()
    DAT_IN = Port()  # 12V data into the head of the chain (main + backup seed)
    DAT_OUT = Port()  # 12V data off the tail of the chain (last DO)

    def __init__(self, n: int = GRID_N, pitch: float = GRID_PITCH):
        layout = diamond_grid_layout(n, pitch)
        cap_layout = decoupling_cap_layout(layout)
        via_layout = led_via_positions(layout)
        count = len(layout)

        self.leds = [WS2815() for _ in range(count)]
        self.caps = [
            Capacitor(
                CapacitorQuery(case=["0603"]), capacitance=100e-9, rated_voltage=50.0
            )
            for _ in range(count)
        ]
        self.vias = []  # power + ground stitching vias (retain so they persist)
        self.routes = []  # JITX routing requests (the router realizes these)
        self.nets = []

        for i, (x, y, rot) in enumerate(layout):
            led = self.leds[i]
            self.place(led, Transform((x, y), rot))

            # power / ground (VDD = +12V)
            self.nets.append(led.VDD + self.PWR_HI)
            self.nets.append(led.GND + self.GND)

            # per-LED VCC filter capacitor to GND (datasheet); placed beside the
            # VCC pad (clear of the body) and rotated to match the LED. cap.p1 is
            # the VCC terminal (insert maps pin_a->p1), cap.p2 the GND terminal.
            cap = self.caps[i]
            cap.insert(led.VCC, self.GND)
            cx, cy, crot = cap_layout[i]
            self.place(cap, Transform((cx, cy), crot))
            # Move the refdes alongside the cap (rotated 90 deg, off the body)
            # instead of the default position on top of it.
            cap.landpattern.pcb_layer_reference = Silkscreen(
                Text(">REF", 0.6, Anchor.C).at(Transform((1.1, 0.0), 90.0, (1.0, 1.0)))
            )
            # explicit programmatic route: LED VCC pad -> cap VCC terminal
            # (replaces the former short_trace=True directive)
            self.routes.append(Route(led.VCC, cap.p1, _TOP))

            # GND stitching via right next to the cap's GND pad (cap.p2), on the
            # side opposite VCC. The cap pads run along its local y axis (VCC=+y,
            # GND=-y), so place the via 1.6 mm along local -y from the cap center
            # (just past the GND pad). Tied to GND and routed cap.p2 -> via.
            ang = math.radians(crot)
            cap_gnd_via = RegularVia().at(
                cx + 1.6 * math.sin(ang), cy - 1.6 * math.cos(ang)
            )
            self.vias.append(cap_gnd_via)
            self.nets.append(self.GND + cap_gnd_via)
            self.routes.append(Route(cap.p2, cap_gnd_via, _TOP))

            # power + ground stitching vias just outside the VDD/GND pads, on the
            # respective planes; let JITX route the short pad->via connection
            (pvx, pvy), (gvx, gvy) = via_layout[i]
            pwr_via = RegularVia().at(pvx, pvy)
            gnd_via = RegularVia().at(gvx, gvy)
            self.vias += [pwr_via, gnd_via]
            self.nets.append(self.PWR_HI + pwr_via)
            self.nets.append(self.GND + gnd_via)
            self.routes.append(Route(led.VDD, pwr_via, _TOP))
            self.routes.append(Route(led.GND, gnd_via, _TOP))

            # WS2815 skip-one chain: DO[i] -> DIN[i+1] (main) and BIN[i+2] (backup)
            chain = led.DO
            if i + 1 < count:
                chain = chain + self.leds[i + 1].DIN
                self.routes.append(Route(led.DO, self.leds[i + 1].DIN, _TOP))
            if i + 2 < count:
                chain = chain + self.leds[i + 2].BIN
                self.routes.append(
                    Route(self.leds[i + 1].DIN, self.leds[i + 2].BIN, _TOP)
                )
            if i == count - 1:
                chain = chain + self.DAT_OUT  # expose the tail data output
            self.nets.append(chain)

        # Seed the head of the skip-one chain.
        # LED[0].BIN has no predecessor — tie to GND (no valid backup source).
        # LED[0].DIN gets DAT_IN and also routes to LED[1].BIN so that if LED[0]
        # fails, LED[1] still receives data on its backup input.
        head = self.leds[0]
        self.nets.append(self.DAT_IN + head.DIN + self.leds[1].BIN)
        self.routes.append(Route(head.DIN, self.leds[1].BIN, _TOP))
        # BIN GND via: same offset pattern as the LED GND stitching vias but placed
        # at local (-VIA_OFFSET, -1.6) to sit beside the BIN pad row.
        x0, y0, rot0 = layout[0]
        ang0 = math.radians(rot0)
        c0, s0 = math.cos(ang0), math.sin(ang0)
        bin_via_x = x0 + (-VIA_OFFSET) * c0 - (-1.6) * s0
        bin_via_y = y0 + (-VIA_OFFSET) * s0 + (-1.6) * c0
        bin_gnd_via = RegularVia().at(bin_via_x, bin_via_y)
        self.vias.append(bin_gnd_via)
        self.nets.append(self.GND + head.BIN + bin_gnd_via)
        self.routes.append(Route(head.BIN, bin_gnd_via, _TOP))


# --- standalone test design -------------------------------------------------
from jitx.sample import SampleDesign  # noqa: E402


class _TestCircuit(Circuit):
    panel = LedDiamond()


class TestDesign(SampleDesign):
    capacitor_defaults = CapacitorQuery(case=["0603"])
    circuit = _TestCircuit()
