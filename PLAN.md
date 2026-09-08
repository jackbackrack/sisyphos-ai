# Project Plan: Sisyphos Diamond LED Panel

## Architecture Summary

Passive 8×8 (64-LED) WS2816C_2121 diamond panel. **No MCU, no on-board level shifting —
everything on this board is at 12V** (level shifting is handled off-board). 12V power and a
single 12V data wire come in over connectors; the panel is chainable via a 12V data-out connector.

### Power Tree
| Rail | Voltage | Source | Regulator | Load | Current |
|------|---------|--------|-----------|------|---------|
| 12V  | 12V | Power connector (2 doubled contacts) | none | 64× WS2816C VDD | ~2.3A max |
| GND  | 0V  | Power connector (2 doubled contacts) | none | all | — |

### Interface Map
| Interface | From | To | Protocol | SI Constrained | Level |
|-----------|------|----|----------|----------------|-------|
| DATA_IN | data-in connector | LED[0].DIN/BIN + LED[1].BIN | WS2815 1-wire | No | 12V |
| LED chain (main) | LED[i].DO | LED[i+1].DIN | WS2815 1-wire | No | 12V |
| LED chain (backup) | LED[i].DO | LED[i+2].BIN | WS2815 skip-one | No | 12V |
| DATA_OUT | LED[63].DO | data-out connector | WS2815 1-wire | No | 12V |

### Board
- Dimensions: 163.51 × 109.51 mm elongated hexagon ("flattened diamond"), apex 116.6°.
- Layers: 4 (top GND / inner 12V / inner GND / bottom GND pours).
- Material: FR-4 (JLCPCB).
- LED lattice: 8×8 rhombic, pitch 13.02 mm along edges, LEDs rotated 45°, serpentine chain (every hop = 13.02 mm).

## Data Sources

| Component | MPN | Package | Source | Footprint Method |
|-----------|-----|---------|--------|------------------|
| WS2815 LED | WS2815 | 5050 6-pad | Worldsemi/Normand datasheet (`datasheets/WS2815.pdf`) | explicit Landpattern from datasheet recommended PCB pad layout (pg 2) |
| Resistor/Capacitor | (query) | 0402 | jitxlib.parts | jitxlib generators |
| Connector (×4: 2 power + 2 data) | Molex 430450218 Micro-Fit 3.0 | 2-ckt vertical SMT | LCSC C476811 | **parts2jitx KiCad footprint (EasyEDA, user-approved)** |
| Bulk cap | MA50V220M10x10 (220µF 50V alu electrolytic) | 10×10 SMD | LCSC C46550473 | custom polarized component (own symbol/silk) — parts2jitx footprint |

---

## Phase 1: Substrate + Components

### [sub-01] Substrate (JLCPCB 4-layer)
- **Type:** substrate
- **Description:** Port `JlcPcb4LayerSubstrate` (+ `JlcPcb4Layer` stackup, `RegularVia`/`SmallVia`, `JlcPcbBasicRules`, dielectric/conductor classes) from `py_social_badge/helpers.py` into `sisyphos/substrate.py`.
- **Verification:** imports cleanly; exercised by main build.
- **Status:** pending

### [comp-01] Power connector — Molex Mini-Fit Jr (4-circuit, locking) stand-in
- **Type:** component
- **Skill:** jitx-component-modeler / jitxlib Header generator
- **Description:** 4-contact connector via Header generator (2×2, 4.2 mm pitch). Wire as 2×12V + 2×GND (doubled). Ports `V12` (list[2]) and `GND` (list[2]).
- **Verification:** `python -m jitx build sisyphos.components.connectors.power_minifit.TestDesign`
- **Status:** pending

### [comp-02] Data connector — 2-pin locking header stand-in
- **Type:** component
- **Skill:** jitxlib Header generator
- **Description:** 2-contact connector via Header generator (1×2, 2.54 mm pitch). Ports `DAT`, `GND`. One class reused for DATA_IN and DATA_OUT.
- **Verification:** `python -m jitx build sisyphos.components.connectors.data_conn.TestDesign`
- **Status:** done

### [comp-04] Mounting hole (NPTH) — mechanical drawing
- **Type:** component (mechanical)
- **Description:** `components/mechanical/mounting_hole.py`. `NPTHPad(Circle(Ø3.8 mm))`, art-only symbol, prefix `MH`. Nine placed in top-level on a 3×3 grid at 3× LED pitch (`mounting_hole_positions()` in geometry.py); each gets an all-layer KeepOut (pour/via/route) ringing the drill. Positions extracted from the mechanical drawing PNG (green circles) via LED-lattice-fit image analysis.
- **Verification:** `python -m jitx build sisyphos.components.mechanical.mounting_hole.TestDesign`
- **Status:** done

---

## Phase 2: Geometry + LED Panel Circuit

### [comp-03] WS2815 LED component
- **Type:** component
- **Skill:** jitx-component-modeler
- **Data source:** Worldsemi/Normand datasheet `datasheets/WS2815.pdf` (pinout + recommended PCB pad layout, pg 2)
- **Description:** `components/leds/worldsemi_WS2815.py`. 5050 6-pad: VCC, VDD(+12V), DO, DIN, GND, BIN. Explicit Landpattern (1.5×1.0 mm pads, columns ±1.7, rows ±1.6 from datasheet recommended layout). BoxSymbol + PadMapping.
- **Verification:** `python -m jitx build sisyphos.components.leds.worldsemi_WS2815.TestDesign`
- **Status:** done

### [cir-01] LED diamond panel
- **Type:** circuit
- **Skill:** jitx-circuit-builder
- **Dependencies:** [comp-03]
- **Description:**
  - `geometry.py`: diamond perimeter `Shape` (the 6-point hexagon) + `diamond_grid_poses(n=8, pitch=13.02, base_rot=45)` → 64 serpentine 45°-rotated `Transform`s. Basis u along lower-right edge, v along lower-left edge.
  - `led_panel.py` `LedDiamond(Circuit)`: 64× WS2815 placed at those transforms; **skip-one** chain `DO[i]→DIN[i+1]` (main) and `DO[i]→BIN[i+2]` (backup); `VDD→PWR_HI`, `GND→GND`; 64× 100 nF 0402 caps inserted `VCC↔GND` (short_trace, datasheet filter cap) placed adjacent. Ports: `PWR_HI`, `GND`, `DAT_IN` (→LED[0].DIN+BIN + LED[1].BIN), `DAT_OUT` (←LED[63].DO).
- **Verification:** `python -m jitx build sisyphos.circuits.led_panel.TestDesign`
- **Status:** done

---

## Phase 3: Top-Level Assembly

### [asm-01] Top-level design
- **Type:** assembly
- **Skill:** jitx-circuit-builder
- **Dependencies:** [sub-01, comp-01, comp-02, cir-01]
- **Description:** `main.py`: `board_shape` = diamond hexagon polygon (exact 6 points). Instantiate `LedDiamond` + power connector + 2 data connectors. Nets: 12V (power conn V12 → panel PWR_HI), GND (power conn GND + data conn GND + panel GND + all pours), data-in conn DAT → panel DAT_IN, panel DAT_OUT → data-out conn DAT. Pours: layer0 GND, layer1 12V, layer2 GND, layer3 GND (buffer −1.0, isolate 0.15). PowerTag → wider traces; PowerSymbol/GroundSymbol on rails. Design class: substrate, board_shape, resistor/capacitor defaults (0402/0603), self.rules.
- **Verification:** `python -m jitx build sisyphos.main.<Design>`
- **Status:** pending

---

## Phase 4: Build + Verify + Iterate

### [ver-01] Final verification
- **Type:** verify
- **Dependencies:** [asm-01]
- **Description:** Full build, confirm 64 LEDs + 64 caps + 3 connectors placed; all 64 LED centers inside perimeter; DRC; chain continuity (single net path DAT_IN→…→DAT_OUT). Iterate on failures.
- **Verification:** `python -m jitx build sisyphos.main.<Design>`
- **Status:** pending

---

## Resolved Decisions
1. **All 12V on-board.** No level shifter; DATA_IN/OUT both 12V. Off-board level shifting is the user's concern.
2. **Connectors:** modeled by me via JITX Header generators as stand-ins; can be swapped for exact Molex footprints later.

## Status: COMPLETE (all phases built `status: ok`)
- sub-01, comp-01, comp-02, cir-01, asm-01, ver-01 — all built and verified.
- Top-level design: `sisyphos.designs.diamond_panel.sisyphos` → **status: ok**.
- Verification (netlist): 64 **WS2815** + 64 caps + 3 connectors; main chain `DO[i]→DIN[i+1]` (63)
  continuous leds[0]→leds[63], backup `DO[i]→BIN[i+2]` (62) skip-one; head seeds DIN[0]+BIN[0]+BIN[1];
  VCC never tied to 12V; all 64 LED and 64 cap centers inside the perimeter (≥4.21 mm edge clearance).
- Vias + routing (stable.design): **128 vias** (64 VDD + 64 GND, `SmallVia` just outside the
  respective pads, ≥2.09 mm to edge) and **317 `Route` requests** (128 pad→via + 63 `DO→DIN` +
  62 `DO→BIN` + 64 VCC pad→cap terminal `cap.p1`), all layer 0. JITX route requests — router
  realizes them; no hand-drawn copper. Power vias are on VDD (12 V), not the WS2815 VCC
  filter-cap pin (no plane). The VCC→cap route replaced the former `short_trace=True` directive.
- Grep gate: PASS (0 hard-fail). Review-required dispositions:
  - `Pour(isolate=0.15)` ×4 — `isolate` is the current Pour clearance kwarg (verified in
    `jitx.copper.Pour` signature); 0.15 mm inter-pour clearance is intentional.

## Open items for the user (non-blocking)
- **Electrolytic bulk cap — resolved via custom component.** The parts-DB polarized-cap path is
  broken in this build (`PolarizedCapacitorSymbol` has no attribute `p` — electrolytic/tantalum/
  polymer all fail to instantiate). Worked around by modeling **MA50V220M10x10** (220 µF 50 V,
  LCSC C46550473) as a custom polarized component with its own symbol + +/- silk. (The underlying
  JITX bug is still worth a report.)
- **Connectors:** four Molex 430450218 (Micro-Fit 3.0 2-circuit) on the back side at the four
  vertices (power in=right/out=top, data in=bottom/out=left — data conns by the chain ends),
  footprint from LCSC C476811; all
  clear of mounting holes. Power P1=12V/P2=GND, data P1=DATA/P2=GND, tabs→GND. Verify pin-1 vs the
  Molex drawing before fab.
- **Mounting-hole diameter:** drawn circle measured ~3.87 mm outer; used **Ø3.8 mm** NPTH
  (`MOUNTING_HOLE_DIAMETER` in geometry.py). No dimension callout in the drawing — confirm the
  intended nominal / screw size (e.g. M3 → 3.2 mm) and plated-vs-NPTH before fab.
- **WS2815 LED:** now a genuine 12V part (datasheet VDD "+12V", abs-max 9.5–13.5V) — prior WS2816C
  voltage concern resolved. Landpattern is built from the datasheet's recommended PCB pad layout;
  verify against your exact WS2815 variant/supplier footprint before fab.
- **Connector footprints** are Header-generator stand-ins (placeholder MPNs). Swap for exact Molex
  Mini-Fit Jr (power) and locking data headers when chosen.
