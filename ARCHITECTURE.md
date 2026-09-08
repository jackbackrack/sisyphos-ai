# Architecture: Sisyphos Diamond LED Panel

A passive 8×8 (64-LED) WS2815 panel laid out as a diamond/hexagon. No MCU and
**no on-board level shifting — everything is at 12V** (level shifting handled off-board).
Four Molex Micro-Fit 3.0 **2-circuit** connectors on the **back (bottom) side**, one at each
diamond vertex, daisy-chain boards: two power (12V/GND) and two data (DATA/GND), each pair an
in/out. power-in=right, data-in=bottom, power-out=top, data-out=left (data connectors sit by the
chain ends — LED[0] at the bottom tip, LED[63] at the top). 12V and GND pass straight
through both power connectors; DATA enters J_DAT_IN and leaves J_DAT_OUT. A bulk cap across
12V/GND sits next to J_PWR_IN. All four connectors are positioned clear of the mounting holes.

## Module Hierarchy

```
sisyphos/
├── substrate.py            # JLCPCB 4-layer substrate (adapted from py_social_badge/helpers.py)
├── geometry.py             # diamond perimeter shape + diamond_grid_poses() (45°-rotated rhombic lattice)
├── components/
│   ├── leds/
│   │   └── worldsemi_WS2815.py  # WS2815 12V dual-signal RGB LED (5050), modeled from datasheet
│   ├── mechanical/
│   │   └── mounting_hole.py     # NPTH drill hole (Ø3.8 mm) — 9 placed per mechanical drawing
│   ├── passives/
│   │   └── electrolytic_MA50V220M10x10.py  # 220µF 50V 10×10 SMD alu electrolytic (custom polarized component)
│   └── connectors/
│       └── molex_430450218.py # Molex Micro-Fit 3.0, 2-ckt vertical SMT (P1/P2 + 2 tabs); footprint from LCSC C476811; used x4
├── circuits/
│   └── led_panel.py        # LedDiamond: 64× WS2815 + 64× 100nF VCC caps, serpentine skip-one chain
└── designs/
    └── diamond_panel.py    # top-level assembly + Design
```

## Power Tree

No on-board regulation (no MCU, no 5V rail generated). 5V data is handled by a
12V-only level shifter, so the only board rails are 12V and GND.

| Rail | Voltage | Source | Regulator | Type | Load | Current | Noise Req | Sequence |
|------|---------|--------|-----------|------|------|---------|-----------|----------|
| 12V  | 12V | Power connector (Mini-Fit, ×2 doubled contacts) | — | Input | 64× WS2815 VDD | ~2.3A max (≈12mA/ch × 3 × 64) | bulk + per-LED 100nF on VCC | — |
| GND  | 0V | Power connector (×2 doubled contacts) | — | Input | all | — | — | — |

### Thermal Notes
- No regulators; LED self-heating is distributed. Internal 12V plane + GND planes carry bulk current.

## Interface Map

| Interface | From | To | Protocol | Speed | SI Constrained | Level | Notes |
|-----------|------|----|----------|-------|----------------|-------|-------|
| DATA_IN | data-in connector | LED[0].DIN, LED[0].BIN, LED[1].BIN | WS2815 single-wire | ~0.8 Mbps | No (slow) | 12V | one wire + GND; seeds main + first two backups |
| LED chain (main) | LED[i].DO | LED[i+1].DIN | WS2815 single-wire | — | No | 12V | serpentine, hop = 13.02 mm |
| LED chain (backup) | LED[i].DO | LED[i+2].BIN | WS2815 skip-one | — | No | 12V | redundancy; ~2 hops (~26 mm) |
| DATA_OUT | LED[63].DO | data-out connector | WS2815 single-wire | — | No | 12V | regenerated chain output |

## Board

- **Dimensions:** 163.51 mm (W) × 109.51 mm (H), elongated hexagon ("flattened diamond").
- **Perimeter (clockwise from top):** (0, 54.755), (81.755, 4.262), (81.755, −4.262), (0, −54.755), (−81.755, −4.262), (−81.755, 4.262). Apex angle 116.6°.
- **Layers:** 4.
- **Stackup (pours):** layer 0 (top) = GND, layer 1 (inner) = 12V, layer 2 (inner) = GND, layer 3 (bottom) = GND.
- **Material:** FR-4.
- **Fab house:** JLCPCB.
- **Substrate:** JlcPcb4LayerSubstrate (adapted from reference).

### Mounting Holes
- Nine non-plated drill holes from the mechanical drawing, **Ø ≈ 3.8 mm** (drawn circle measured ~3.87 mm; no dimension callout — confirm intended size/screw before fab).
- Positioned on a **3×3 grid** at 3× the LED lattice step (basis 3·u, 3·v), centered at the origin: (0,0), (0,±41.05), (±66.47,0), (±33.23,±20.53). All inside the perimeter; ≥6.84 mm to any LED center.
- Each has an all-layer copper/via/route **keepout** (Ø drill + 2 mm) so pours clear the hole.

### LED Lattice
- 8×8 rhombic lattice, basis vectors along the two diamond edges (31.7° off horizontal), pitch **13.02 mm** (half-pitch 6.51 mm).
  - u = (11.078, 6.842), v = (−11.078, 6.842), |u| = |v| = 13.02 mm.
  - P(i,j) = (i−3.5)·u + (j−3.5)·v, i,j ∈ 0..7.
- Renders as a diamond (rows of 1,2,…,8,…,2,1). All 64 centers inside perimeter; min center-to-edge = 4.21 mm.
- Each LED rotated **45°** (+180° on reversed serpentine rows so DIN/DO follow the chain).
- One 100 nF 0402 filter cap (VCC↔GND, per datasheet) per LED, placed on the LED's **no-pad bottom edge** (local −y, the VCC/BIN end), **centered between the two pad columns** (x=0), 3.25 mm from the LED center just outside the 5050 body, **rotated 90° so its long axis is perpendicular to the edge** and its near pad tucks against the LED toward VCC (cap rotation = LED rotation − 90°). All 64 fit, including the diamond tips (0/64 flipped; near-pad-to-body gap 0.25 mm; min edge clearance 1.91 mm).

### Chain Ordering (minimal wire)
- Serpentine over lattice indices: row j traversed +i (j even) / −i (j odd).
- Every chain hop spans exactly one basis step = **13.02 mm** (in-row = u, row-to-row = v).

### Vias & Routing (JITX route requests — not hand-drawn copper)
- Per LED: a **VDD (12 V) stitching via** just outside the +x pad column and a **GND via** just outside the −x pad column (**`RegularVia`** — the preferred/larger substrate via, Ø0.9 mm pad / 0.4 mm drill — 3.0 mm from LED center). Each via is on its own net (so it only ties to its matching plane; antipads auto-clear it from the others) and ≥2.09 mm from the board edge. **128 vias total** (64 VDD + 64 GND).
- Note: vias are on **VDD**, not the WS2815 VCC pin — VCC is an internal filter-cap-only node with no plane, so a via there would dead-end.
- **`jitx.circuit.Route` requests** (the router realizes them; no `Copper(...)` drawn by us), all on layer 0: VDD pad→via and GND pad→via (128); the data daisy-chain `DO[i]→DIN[i+1]` (63) and skip-one `DO[i]→BIN[i+2]` (62); and each LED's VCC pad→its cap VCC terminal `cap.p1` (64, replacing the former `short_trace` directive). **317 route requests total.**

## Voltage Domains

| Domain | Voltage | Components/Pins |
|--------|---------|-----------------|
| 12V | 12V | all LED VDD, all data (DIN/DO/BIN), 12V plane |
| VCC (internal) | ~regulated by LED | each LED VCC pin + its 100 nF filter cap to GND (not externally driven) |
| GND | 0V | all |

## Design Notes
- **WS2815 is a genuine 12V part** (datasheet: VDD "+12V", abs-max 9.5–13.5 V). This replaced the
  earlier WS2816C_2121 (a library part declared 3.7–5.5 V) and resolves the prior voltage concern.
- **All 12V on-board.** Per user decision, this board does no level shifting; incoming data is already
  at 12V (shifted off-board). WS2815 logic-high VIH = VDD−0.5…VCC+0.5, so external 12V data drives
  DIN/BIN directly. DATA_OUT is the chain's regenerated 12V output.
- **Skip-one redundancy:** WS2815 has one data output (DO) and a backup input (BIN). DO[i] drives
  DIN[i+1] (main) and BIN[i+2] (backup); if pixel i+1 dies, pixel i+2 still receives data via BIN.
  The head net seeds DIN[0], BIN[0], and BIN[1] (no upstream DO for those backups).
- **VCC filter cap:** WS2815 VCC is an internal logic rail ("suspended or connected with a filter
  capacitor to GROUND"). The per-LED 100 nF sits VCC↔GND; VCC is never tied to 12V.
- **Connectors:** four **Molex Micro-Fit 3.0, 2-circuit vertical SMT** (MPN 430450218), footprint
  from LCSC/EasyEDA **C476811** via parts2jitx. Generic P1/P2 + 2 solder tabs. Power connectors:
  P1=12V, P2=GND; data connectors: P1=DATA, P2=GND; all solder tabs → GND. Placed on the **back
  (bottom) side** at the four vertices, clear of the mounting holes (top/bottom rotated 90° to fit
  the tips). Each is moved **inward past its neighboring hole** with a ≥2 mm buffer to that hole's
  keepout ring (ring r = 2.9 mm; actual buffer ≈3.2 mm): J_PWR_IN (57, 0),
  J_DAT_IN (0, −31.5, 90°), J_PWR_OUT (0, 31.5, 90°), J_DAT_OUT (−57, 0); bulk electrolytic near J_PWR_IN at (44, 0).
- **Bulk cap:** **MA50V220M10x10** — 220 µF 50 V 10×10 mm SMD aluminum electrolytic (LCSC C46550473),
  across 12V/GND on the back side, ANODE(+)→12V. Modeled as a **custom polarized component**
  (`components/passives/`) with its own symbol and +/- silk, because the parts-DB polarized-cap path
  is broken in this JITX build (`PolarizedCapacitorSymbol` has no `.p`). The bottom side is uncrowded
  (LEDs/pads/caps are all on top), so the large part sits near power-in clear of the connector/holes.
