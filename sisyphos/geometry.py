"""Diamond board geometry and LED lattice for the Sisyphos panel.

The board perimeter is an elongated hexagon ("flattened diamond"), 163.51 mm wide x
109.51 mm tall, apex angle 116.6 deg. The 8x8 LED lattice is rhombic: its basis
vectors lie along the two lower diamond edges (31.7 deg off horizontal) with a
13.02 mm pitch, so the grid renders as a diamond (rows of 1,2,...,8,...,2,1) and each
LED is rotated 45 deg. The chain order is serpentine, so every hop between
consecutive LEDs spans exactly one 13.02 mm basis step (minimal wire length).
"""

import math

from jitx.shapes.primitive import Polygon
from jitx.transform import Transform

# Perimeter vertices, clockwise from the top point.
PERIMETER: list[tuple[float, float]] = [
    (0.000, 54.755),
    (81.755, 4.262),
    (81.755, -4.262),
    (0.000, -54.755),
    (-81.755, -4.262),
    (-81.755, 4.262),
]

# Default LED grid parameters (from the mechanical drawing).
GRID_N = 8
GRID_PITCH = 13.02  # mm, center-to-center along the diamond edges
LED_BASE_ROT = 45.0  # deg, each LED rotated 45 deg


def diamond_shape() -> Polygon:
    """Board outline polygon (the flattened-diamond hexagon)."""
    return Polygon(PERIMETER)


# WS2815 footprint (local frame): two pad columns at x = +/-2.45, each 3 pins
# spanning y = +/-1.6. The top/bottom edges (y = +/-2.5) carry no pads. VCC/BIN
# are the bottom (-y) pads. See components/leds/worldsemi_WS2815.py.
# Cap sits on the no-pad bottom edge (local -y), centered between the two columns
# (x=0), just outside the 5050 body (half-height 2.5 mm). Its long axis is
# PERPENDICULAR to the edge (cap rotated 90 deg), so its near pad tucks up against
# the LED toward VCC. Sits right at the 5050 body edge (~0 gap, no body overlap).
CAP_EDGE_OFFSET = 3.35


def _rotate(px: float, py: float, deg: float) -> tuple[float, float]:
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    return (px * c - py * s, px * s + py * c)


def _point_in_polygon(px: float, py: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


def _edge_distance(px: float, py: float, poly: list[tuple[float, float]]) -> float:
    best = float("inf")
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        qx, qy = x1 + t * dx, y1 + t * dy
        best = min(best, math.hypot(px - qx, py - qy))
    return best


# Power/ground stitching vias: VDD (12V) pad is at local +x, GND pad at local -x.
# Place each via just outside its pad. Pad outer edge at 2.45+0.75=3.2mm; offset
# must clear 3.2 + via radius 0.45 + clearance 0.2 = 3.85 → use 4.0.
VIA_OFFSET = 4.0


def led_via_positions(
    led_layout: list[tuple[float, float, float]], offset: float = VIA_OFFSET
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """For each LED return ((vdd_via_x, vdd_via_y), (gnd_via_x, gnd_via_y)).

    VDD via sits just outside the +x (VDD/12V) pad column; GND via just outside
    the -x (GND) pad column. Both clear the body and the neighboring pads.
    """
    out: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for x, y, rot in led_layout:
        pdx, pdy = _rotate(offset, 0.0, rot)
        gdx, gdy = _rotate(-offset, 0.0, rot)
        out.append(((x + pdx, y + pdy), (x + gdx, y + gdy)))
    return out


def top_layer_obstacles(
    n: int = GRID_N, pitch: float = GRID_PITCH
) -> list[tuple[float, float, float]]:
    """Top-layer features a back-side connector via must avoid, as (x, y, radius):
    the 6 pads of every LED, the 128 LED stitching vias, the 64 LED filter caps,
    and the 9 mounting-hole keepout rings.
    """
    layout = diamond_grid_layout(n, pitch)
    obs: list[tuple[float, float, float]] = []
    led_pads = [
        (2.45, -1.6),
        (2.45, 0.0),
        (2.45, 1.6),
        (-2.45, 1.6),
        (-2.45, 0.0),
        (-2.45, -1.6),
    ]
    for x, y, rot in layout:
        for lx, ly in led_pads:
            px, py = _rotate(lx, ly, rot)
            obs.append((x + px, y + py, 0.95))  # 1.5x1.1 pad ~ r0.93
    for pwr, gnd in led_via_positions(layout):
        obs.append((pwr[0], pwr[1], 0.33))
        obs.append((gnd[0], gnd[1], 0.33))
    for cx, cy, _ in decoupling_cap_layout(layout):
        obs.append((cx, cy, 0.6))  # 0402 cap ~ r0.6
    for hx, hy in mounting_hole_positions(pitch):
        obs.append((hx, hy, MOUNTING_HOLE_DIAMETER / 2.0 + 1.0))
    return obs


def find_clear_via(
    tx: float,
    ty: float,
    obstacles: list[tuple[float, float, float]],
    prefer: tuple[float, float] = (0.0, 0.0),
    via_radius: float = 0.33,
    clearance: float = 0.2,
    max_search: float = 5.0,
) -> tuple[float, float] | None:
    """Nearest position to (tx, ty), inside the perimeter, whose via copper clears
    every obstacle. Searches the target then rings outward, biased toward ``prefer``.
    """

    def ok(x: float, y: float) -> bool:
        if not _point_in_polygon(x, y, PERIMETER):
            return False
        for ox, oy, orad in obstacles:
            if math.hypot(x - ox, y - oy) < via_radius + orad + clearance:
                return False
        return True

    if ok(tx, ty):
        return (tx, ty)
    steps = 36
    r = 0.25
    while r <= max_search:
        cands = [
            (
                tx + r * math.cos(2 * math.pi * k / steps),
                ty + r * math.sin(2 * math.pi * k / steps),
            )
            for k in range(steps)
        ]
        cands = [(x, y) for x, y in cands if ok(x, y)]
        if cands:
            if prefer != (0.0, 0.0):
                cands.sort(
                    key=lambda p: -((p[0] - tx) * prefer[0] + (p[1] - ty) * prefer[1])
                )
            return cands[0]
        r += 0.25
    return None


def decoupling_cap_layout(
    led_layout: list[tuple[float, float, float]],
    offset: float = CAP_EDGE_OFFSET,
    edge_margin: float = 1.0,
) -> list[tuple[float, float, float]]:
    """Cap (x, y, rot) for each LED: placed on the no-pad bottom edge (local -y,
    the VCC/BIN end), centered between the two pad columns, just outside the body,
    rotated 90 deg so its long axis is perpendicular to the edge and its near pad
    tucks against the LED toward VCC. Stays on the bottom edge unless that would
    leave the perimeter or sit within ``edge_margin`` of the board edge, in which
    case it flips to the top edge.
    """
    out: list[tuple[float, float, float]] = []
    for x, y, rot in led_layout:
        # local offset (0, -offset): no-pad bottom edge, centered between columns
        dx, dy = _rotate(0.0, -offset, rot)
        bottom = (x + dx, y + dy)
        if (
            _point_in_polygon(*bottom, PERIMETER)
            and _edge_distance(*bottom, PERIMETER) >= edge_margin
        ):
            cx, cy = bottom
        else:
            cx, cy = (x - dx, y - dy)  # flip to the top edge only when it won't fit
        out.append((cx, cy, rot - 90.0))  # 90 deg CW: long axis perpendicular to edge
    return out


def _edge_basis(pitch: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Lattice basis vectors u, v of length ``pitch`` along the two lower edges.

    u runs from the bottom vertex toward the lower-right vertex; v is its mirror
    across the vertical axis (toward the lower-left vertex).
    """
    bx, by = 0.000, -54.755  # bottom vertex
    rx, ry = 81.755, -4.262  # lower-right vertex
    length = math.hypot(rx - bx, ry - by)
    ux, uy = (rx - bx) / length * pitch, (ry - by) / length * pitch
    return (ux, uy), (-ux, uy)


def diamond_grid_layout(
    n: int = GRID_N, pitch: float = GRID_PITCH, base_rot: float = LED_BASE_ROT
) -> list[tuple[float, float, float]]:
    """Return ``n*n`` (x, y, rotation_deg) tuples in serpentine chain order.

    Reversed rows are rotated an extra 180 deg so each LED's data ports (DI/DO)
    follow the chain direction.
    """
    (ux, uy), (vx, vy) = _edge_basis(pitch)
    center = (n - 1) / 2.0
    layout: list[tuple[float, float, float]] = []
    for j in range(n):
        reverse = j % 2 == 1
        rot = base_rot + (180.0 if reverse else 0.0)
        cols = range(n - 1, -1, -1) if reverse else range(n)
        for i in cols:
            x = (i - center) * ux + (j - center) * vx
            y = (i - center) * uy + (j - center) * vy
            layout.append((x, y, rot))
    return layout


def diamond_grid_poses(
    n: int = GRID_N, pitch: float = GRID_PITCH, base_rot: float = LED_BASE_ROT
) -> list[Transform]:
    """Return the LED placement Transforms in serpentine chain order."""
    return [
        Transform((x, y), rot)
        for (x, y, rot) in diamond_grid_layout(n, pitch, base_rot)
    ]


# Mounting/drill holes from the mechanical drawing: nine holes on a 3x3 grid
# whose basis is 3x the LED lattice step (3*u, 3*v), centered at the origin.
# Measured from the drawing (drawn circle outer diameter).
MOUNTING_HOLE_DIAMETER = 3.8  # mm (measured ~3.87; see PLAN open item)


def mounting_hole_positions(pitch: float = GRID_PITCH) -> list[tuple[float, float]]:
    """Nine (x, y) mounting-hole centers: 3x3 grid spaced 3 LED-pitches apart."""
    (ux, uy), (vx, vy) = _edge_basis(pitch)
    pts: list[tuple[float, float]] = []
    for m in (-1, 0, 1):
        for n in (-1, 0, 1):
            x = 3 * (m * ux + n * vx)
            y = 3 * (m * uy + n * vy)
            pts.append((x, y))
    return pts
