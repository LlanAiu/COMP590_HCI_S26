# builtin
import datetime

# external
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

# internal


download_moves_router = APIRouter()

@download_moves_router.get("/download-moves")
async def download_moves(gameId: str, request: Request):
    games = request.app.state.games
    state = games.get(gameId)
    
    if not state:
        return JSONResponse({"error": "Invalid gameId"}, status_code=400)

    moves = state.get("moves", [])
    text = ",".join(m["move"] for m in moves)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"hex_moves_{gameId}_{ts}.txt"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=text, headers=headers, media_type="text/plain")