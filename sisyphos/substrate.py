"""JLCPCB 4-layer FR-4 substrate for the Sisyphos diamond LED panel.

Ported from py_social_badge/helpers.py. 4-layer stackup with JLCPCB basic
fabrication rules and through-hole vias. Pours on this board:
    layer 0 (top)    = GND
    layer 1 (inner)  = 12V
    layer 2 (inner)  = GND
    layer 3 (bottom) = GND
"""

from jitx.stackup import Conductor, Dielectric, Symmetric
from jitx.substrate import FabricationConstraints, Substrate
from jitx.via import Via, ViaType


class Copper(Conductor):
    pass


class Prepreg2313(Dielectric):
    name = "FR4 Prepreg 2313"
    dielectric_coefficient = 4.05


class SolderMask(Dielectric):
    name = "Taiyo BSN4000"


class Core45(Dielectric):
    name = "4.5 DK FR4 Core"
    dielectric_coefficient = 4.5


# see https://jlcpcb.com/capabilities/pcb-capabilities for PCB design rules
class JlcPcbBasicRules(FabricationConstraints):
    min_copper_width = 0.15
    min_copper_copper_space = 0.15
    min_copper_hole_space = 0.203
    min_copper_edge_space = 0.2
    min_annular_ring = 0.180
    min_drill_diameter = 0.3
    min_silkscreen_width = 0.153
    min_pitch_leaded = 0.3
    min_pitch_bga = 0.377
    max_board_width = 670.0
    max_board_height = 600.0
    min_silk_solder_mask_space = 0.15
    min_silkscreen_text_height = 1.00
    solder_mask_registration = 0.038
    min_th_pad_expand_outer = 0.26
    min_soldermask_opening = 0.10
    min_soldermask_bridge = 0.1
    min_hole_to_hole = 0.2
    min_pth_pin_solder_clearance = 3.0


class RegularVia(Via):
    # Preferred / larger via: 0.9 mm pad, 0.4 mm drill (0.25 mm annular). Bigger
    # than the minimum SmallVia below; better current capacity for power/ground.
    name = "Regular TH"
    start_layer = 0
    stop_layer = -1
    diameter = 0.9
    hole_diameter = 0.4
    type = ViaType.MechanicalDrill


class SmallVia(Via):
    name = "Minimum TH"
    start_layer = 0
    stop_layer = -1
    annular = 0.18
    drill = 0.3
    diameter = drill + annular * 2.0
    hole_diameter = drill
    type = ViaType.MechanicalDrill


class JlcPcb4Layer(Symmetric):
    name = "JLCPCB 4-layer 1.6mm"
    soldermask = SolderMask(thickness=0.019)
    copper1 = Copper(thickness=0.035)
    prepreg = Prepreg2313(thickness=0.1)
    copper2 = Copper(thickness=0.0175)
    core = Core45(thickness=1.2650)


class JlcPcb4LayerSubstrate(Substrate):
    stackup = JlcPcb4Layer()
    constraints = JlcPcbBasicRules()
    vias = [RegularVia, SmallVia]
