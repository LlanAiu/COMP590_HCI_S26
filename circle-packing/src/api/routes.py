from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..modules import pack

# follow convention: mount API under /api
router = APIRouter(prefix="/api")


@router.post("/generate")
async def generate(payload: dict):
    """Generate circle centers and bounding box for requested grid.

    payload: { num_circles: int, grid: 'square'|'hex' }
    """
    num = int(payload.get("num_circles", 10))
    grid = payload.get("grid", "square")

    centers, bbox = pack.generate_positions(num, grid=grid)

    # compute bbox area in units assuming radius=1
    minx, maxx, miny, maxy = bbox
    width_units = (maxx - minx) + 2.0
    height_units = (maxy - miny) + 2.0
    area_units = width_units * height_units

    return JSONResponse({
        "centers": centers,
        "bbox": {"minx": minx, "maxx": maxx, "miny": miny, "maxy": maxy},
        "width_units": width_units,
        "height_units": height_units,
        "area_units": area_units,
    })
