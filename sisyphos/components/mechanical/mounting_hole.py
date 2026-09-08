"""Non-plated mounting / drill hole for the Sisyphos diamond panel.

A mechanical NPTH (non-plated through hole) with a circular cutout. Used for the
nine drill holes from the mechanical drawing. No electrical connection.
"""

from jitx.anchor import Anchor
from jitx.component import Component
from jitx.container import inline
from jitx.landpattern import Landpattern
from jitx.shapes.primitive import Circle, Text
from jitx.symbol import Symbol
from jitxlib.landpatterns.pads import NPTHPad

from ...geometry import MOUNTING_HOLE_DIAMETER


class MountingHoleLandpattern(Landpattern):
    hole = NPTHPad(Circle(diameter=MOUNTING_HOLE_DIAMETER))


class MountingHole(Component):
    """Non-plated through-hole drill (mechanical only)."""

    reference_designator_prefix = "MH"
    landpattern = MountingHoleLandpattern()

    @inline
    class symbol(Symbol):
        art = [
            Circle(radius=MOUNTING_HOLE_DIAMETER / 2.0),
            Text(">REF", 0.8, Anchor.C),
        ]


# --- standalone test design -------------------------------------------------
from jitx.circuit import Circuit  # noqa: E402
from jitx.sample import SampleDesign  # noqa: E402


class _TestCircuit(Circuit):
    mh = MountingHole()


class TestDesign(SampleDesign):
    circuit = _TestCircuit()
