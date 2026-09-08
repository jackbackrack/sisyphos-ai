"""Top-level assembly for the Sisyphos diamond LED panel.

A passive 8x8 WS2815 panel on a flattened-diamond hexagon board. Four 2-circuit Molex
Micro-Fit 3.0 connectors on the back side, one near each vertex (power-in=right,
data-in=bottom, power-out=top, data-out=left), daisy-chain boards: 12V/GND pass through
both power connectors; DATA enters J_DAT_IN and leaves J_DAT_OUT. A bulk cap sits across
12V/GND by J_PWR_IN, and each connector has a bottom-silk function label. 4-layer JLCPCB
stackup with pours:
    layer 0 (top)   = GND
    layer 1 (inner) = 12V
    layer 2 (inner) = GND
    layer 3 (bottom)= GND
"""

from jitx.board import Board
from jitx.circuit import Circuit
from jitx import KeepOut
from jitx.anchor import Anchor
from jitx.constraints import Tag, design_constraint
from jitx.copper import Pour
from jitx.design import Design
from jitx.feature import Silkscreen
from jitx.layerindex import LayerSet, Side
from jitx.net import Net
from jitx.shapes import Shape
from jitx.shapes.primitive import Circle, Text
from jitx.transform import Transform
from jitxlib.parts import CapacitorQuery, Resistor, ResistorQuery
from jitxlib.symbols.net_symbols.ground import GroundSymbol
from jitxlib.symbols.net_symbols.power import PowerSymbol

from ..circuits.led_panel import LedDiamond
from ..components.connectors.molex_430450218 import MicroFit3_43045_0218
from ..components.diodes.smcja12a import SMCJA12A
from ..components.mechanical.mounting_hole import MountingHole
from ..components.passives.electrolytic_MA50V220M10x10 import MA50V220M10x10
from ..geometry import MOUNTING_HOLE_DIAMETER, diamond_shape, mounting_hole_positions
from ..substrate import JlcPcb4LayerSubstrate


class PowerTag(Tag):
    """Tag for power/ground nets that get wider traces."""

    pass


class Sisyphos(Circuit):
    P12V = Net()
    GND = Net()

    def __init__(self, board_shape: Shape):
        self.board_shape = board_shape
        self.nets: list = []

        # LED panel
        self.panel = LedDiamond()
        self.place(self.panel, Transform((0.0, 0.0)))

        # Four 2-pin Molex Micro-Fit 3.0 connectors near the diamond's four vertices,
        # all on the BACK (bottom) side. Each is moved INWARD, past its neighboring
        # mounting hole, leaving a >=2 mm buffer to the outer edge of that hole's
        # keepout ring (ring radius 2.9 mm -> connector edge >= 4.9 mm from center):
        #   power-in = right, data-in = bottom, power-out = top, data-out = left.
        # Top/bottom are rotated 90 deg to fit the narrowing tips.
        self.j_pwr_in = MicroFit3_43045_0218()
        self.j_dat_in = MicroFit3_43045_0218()
        self.j_pwr_out = MicroFit3_43045_0218()
        self.j_dat_out = MicroFit3_43045_0218()
        self.place(self.j_pwr_in, Transform((57.0, 0.0)), on=Side.Bottom)
        self.place(self.j_dat_in, Transform((0.0, -31.5), 90.0), on=Side.Bottom)
        self.place(self.j_pwr_out, Transform((0.0, 31.5), 90.0), on=Side.Bottom)
        self.place(self.j_dat_out, Transform((-57.0, 0.0)), on=Side.Bottom)

        # Bottom-silk function labels next to each connector. Mirrored in x
        # (scale -1) so they read correctly when viewed from the bottom.
        def _btm_label(text, x, y):
            return Silkscreen(
                Text(text, 1.5, Anchor.C).at(Transform((x, y), 0.0, (-1.0, 1.0))),
                side=Side.Bottom,
            )

        self.labels = [
            _btm_label("PWR IN", 57.0, 8.0),
            _btm_label("DATA OUT", -57.0, 8.0),
            _btm_label("DATA IN", 0.0, -25.0),
            _btm_label("PWR OUT", 0.0, 25.0),
        ]

        # Mounting / drill holes (mechanical drawing): nine NPTH on a 3x3 grid.
        # Each gets an all-layer keepout (pour/via/route) ringing the drill so
        # copper clears the hole.
        hole_pts = mounting_hole_positions()
        self.mounting_holes = [MountingHole() for _ in hole_pts]
        keepout_r = MOUNTING_HOLE_DIAMETER / 2.0 + 1.0
        self.hole_keepouts = []
        for mh, (hx, hy) in zip(self.mounting_holes, hole_pts):
            self.place(mh, Transform((hx, hy)))
            self.hole_keepouts.append(
                KeepOut(
                    Circle(radius=keepout_r).at(hx, hy),
                    LayerSet(0, 1, 2, 3),
                    pour=True,
                    via=True,
                    route=True,
                )
            )

        # 12V passes through both power connectors (P1) for the daisy chain.
        self.nets.append(
            self.P12V + self.j_pwr_in.P1 + self.j_pwr_out.P1 + self.panel.PWR_HI
        )
        # GND: every connector's P2 + both solder tabs, plus the panel.
        self.nets.append(
            self.GND
            + self.j_pwr_in.P2
            + self.j_pwr_in.TAB_L
            + self.j_pwr_in.TAB_R
            + self.j_pwr_out.P2
            + self.j_pwr_out.TAB_L
            + self.j_pwr_out.TAB_R
            + self.j_dat_in.P2
            + self.j_dat_in.TAB_L
            + self.j_dat_in.TAB_R
            + self.j_dat_out.P2
            + self.j_dat_out.TAB_L
            + self.j_dat_out.TAB_R
            + self.panel.GND
        )

        # Data (12V): J_DAT_IN.P1 -> chain head, chain tail -> [series R] -> J_DAT_OUT.
        self.nets.append(self.j_dat_in.P1 + self.panel.DAT_IN)
        # 0603 0-ohm in series on the outgoing data (chain tail -> data-out connector).
        # Swap for ~20-30 ohm series termination later if the cabled signal needs it.
        self.r_dat_out = Resistor(ResistorQuery(case=["0603"]), resistance=0.0)
        self.r_dat_out.insert(self.panel.DAT_OUT, self.j_dat_out.P1)
        # Orbited 90 deg around J_DAT_OUT to sit by its data pin (P1, below the
        # connector), flipped 180 deg so the input pad faces the incoming data.
        self.place(self.r_dat_out, Transform((-57.0, -8.0), 180.0), on=Side.Bottom)

        # Bulk electrolytic across 12V/GND on the BACK side: MA50V220M10x10, 220 uF
        # 50 V, 10x10 mm. Custom component (own polarized symbol + +/- silk),
        # bypassing the broken parts-DB polarized-cap path. ANODE(+) -> 12V.
        # The bottom side is uncrowded (LEDs/pads/caps are all on top), so this big
        # part fits near power-in, clear of the connector and mounting holes.
        self.bulk_cap = MA50V220M10x10()
        self.nets.append(self.P12V + self.bulk_cap.ANODE)
        self.nets.append(self.GND + self.bulk_cap.CATHODE)
        # Rotated -90 deg (bottom side) so anode(12V)/cathode(GND) stack vertically,
        # lined up with J_PWR_IN's 12V / GND pads. Shifted left (x=38.25) from its
        # former x=44.5 to open a gap for the TVS diode between the can and the
        # connector (the 10 mm can courtyard otherwise leaves no room).
        self.place(self.bulk_cap, Transform((38.25, 0.0), -90.0), on=Side.Bottom)

        # TVS diode: transient overvoltage protection at the 12V rail entry point.
        # Placed IN-LINE between the bulk cap (x=38.25) and J_PWR_IN (x=57), in the
        # gap at (47.75, 2.0) — nudged +2 mm in y to clear an LED stitching via
        # below it. Rotated -90 deg on the bottom side — the SAME
        # transform as the bulk cap — so its pads stack vertically and, because the
        # diode's CATHODE(12V) sits at local -x just like the cap's ANODE(12V), the
        # 12V and GND pads of the two parts land on the same board sides as each
        # other and line up with J_PWR_IN's 12V/GND. Physical P12V trace order:
        # connector → TVS → cap. Under normal operation reverse-biased (invisible);
        # clamps spikes to ~20V.
        self.tvs_pwr_in = SMCJA12A()
        self.nets.append(self.P12V + self.tvs_pwr_in.CATHODE)
        self.nets.append(self.GND + self.tvs_pwr_in.ANODE)
        self.place(self.tvs_pwr_in, Transform((47.75, 2.0), -90.0), on=Side.Bottom)

        # Net symbols
        self.P12V.symbol = PowerSymbol()
        self.GND.symbol = GroundSymbol()

        # Copper pours: top GND, inner 12V, inner GND, bottom GND
        outline = self.board_shape.to_shapely().buffer(-1.0)
        self.gnd_pour_top = Pour(outline, 0, isolate=0.15, rank=1)
        self.p12v_pour = Pour(outline, 1, isolate=0.15, rank=1)
        self.gnd_pour_inner = Pour(outline, 2, isolate=0.15, rank=1)
        self.gnd_pour_bot = Pour(outline, 3, isolate=0.15, rank=1)
        self.nets.append(self.P12V + self.p12v_pour)
        self.nets.append(
            self.GND + self.gnd_pour_top + self.gnd_pour_inner + self.gnd_pour_bot
        )

        # Wider traces for power/ground
        PowerTag().assign(self.P12V)
        PowerTag().assign(self.GND)
        self.rules = [design_constraint(PowerTag()).trace_width(0.5)]


class SisyphosBoard(Board):
    def __init__(self, board_shape: Shape):
        super().__init__()
        self.shape = board_shape


_board_shape = diamond_shape()


class sisyphos(Design):
    resistor_defaults = ResistorQuery(case=["0402", "0603"])
    capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    board_shape = _board_shape
    substrate = JlcPcb4LayerSubstrate()
    board = SisyphosBoard(_board_shape)
    circuit = Sisyphos(_board_shape)
