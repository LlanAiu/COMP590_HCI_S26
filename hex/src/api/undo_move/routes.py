# builtin

# external
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# internal
from src.modules import HexGame

# Generated from PS1-Q2
undo_router = APIRouter()


@undo_router.post("/undo-move")
async def undo_move(request: Request):
	data = await request.json()
	game_id = data.get("gameId")
	games = request.app.state.games

	game: HexGame = games.get(game_id)

	if not game:
		return JSONResponse({"error": "Invalid gameId"}, status_code=400)

	ok = game.undo()

	if not ok:
		return JSONResponse({"error": "Cannot undo"}, status_code=400)

	return game.to_json()

