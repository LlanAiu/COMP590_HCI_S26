import math
from typing import List, Tuple


def _square_grid_positions(n: int) -> List[Tuple[float, float]]:
    positions = []
    # place in rows and columns with center-to-center distance = 2 (radius=1)
    per_row = math.ceil(math.sqrt(n))
    for i in range(n):
        r = i // per_row
        c = i % per_row
        x = c * 2.0
        y = r * 2.0
        positions.append((x, y))
    return positions


def _hex_grid_positions(n: int) -> List[Tuple[float, float]]:
    positions = []
    per_row = math.ceil(math.sqrt(n))
    v_spacing = math.sqrt(3)  # vertical spacing for unit radius
    for i in range(n):
        r = i // per_row
        c = i % per_row
        x = c * 2.0 + (r % 2) * 1.0
        y = r * v_spacing
        positions.append((x, y))
    return positions


def _bbox(positions: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    return min(xs), max(xs), min(ys), max(ys)


def generate_positions(num_circles: int, grid: str = "square"):
    """Return centers (list of [x,y]) in units where radius=1, and bbox (minx,maxx,miny,maxy).

    The centers are created so adjacent tangent circles have center-to-center distance 2.
    """
    if num_circles <= 0:
        return [], (0.0, 0.0, 0.0, 0.0)

    if grid == "hex":
        pos = _hex_grid_positions(num_circles)
    else:
        pos = _square_grid_positions(num_circles)

    # shift so positions are centered around origin (optional but nicer)
    minx, maxx, miny, maxy = _bbox(pos)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    centered = [ (x - cx, y - cy) for x,y in pos ]

    minx, maxx, miny, maxy = _bbox(centered)

    return centered, (minx, maxx, miny, maxy)
