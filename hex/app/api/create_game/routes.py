# builtin
import random

# external
from fastapi import APIRouter, Request

# internal
from app.modules import HexGame


create_game_router = APIRouter()

@create_game_router.post("/create-game")
async def create_game(request: Request):
    game_id = f"g{random.randint(1000,9999)}"
    game = HexGame(game_id=game_id)
    
    app = request.app
    games = app.state.games
    games[game_id] = game
    
    return game.to_json()