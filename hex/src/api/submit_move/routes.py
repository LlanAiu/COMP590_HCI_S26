# builtin

# external
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# internal
from src.modules import HexGame
from .io import MoveInput

submit_move_router = APIRouter()

@submit_move_router.post("/submit-move")
async def submit_move(request: Request, input: MoveInput):
    games = request.app.state.games
    
    game: HexGame = games.get(input.gameId)
    
    if not game: 
        return JSONResponse({"error": "Invalid gameId"}, status_code=400)
    
    game.process_move(input)
    
    return game.to_json()