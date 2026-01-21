# builtin

# external
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# internal

submit_move_router = APIRouter()

@submit_move_router.post("/submit-move")
async def submit_move(request: Request):
    games = request.app.state.games
    
    data = await request.json()
    game_id = data.get("gameId")
    move = data.get("move")
    player = data.get("player")
    
    state = games.get(game_id)
    
    if not state:
        return JSONResponse({"error": "Invalid gameId"}, status_code=400)
    try:
        r, c = coord_to_index(move)
    except Exception:
        state["status"] = "invalid"
        return state

    if not (0 <= r < len(state["board"]) and 0 <= c < len(state["board"])):
        state["status"] = "invalid"
        return state

    if state["board"][r][c] != "0" or state["player"] != player or state["status"] == "win":
        state["status"] = "invalid"
        return state

    # ensure moves list exists
    if "moves" not in state:
        state["moves"] = []

    # apply human move
    row = list(state["board"][r])
    row[c] = "R" if player == "red" else "B"
    state["board"][r] = "".join(row)
    state["lastMove"] = move
    state["moveNumber"] += 1
    state["moves"].append(move)

    if check_win(state["board"], player):
        state["status"] = "win"
        state["winner"] = player
        return state

    # alternate turn
    state["player"] = "blue" if player == "red" else "red"

    # AI move if it's blue's turn
    if state["player"] == "blue":
        ai = ai_move(state["board"], "red")
        r_ai, c_ai = coord_to_index(ai)
        row = list(state["board"][r_ai])
        row[c_ai] = "B"
        state["board"][r_ai] = "".join(row)
        state["lastMove"] = ai
        state["moveNumber"] += 1
        state["moves"].append(ai)
        if check_win(state["board"], "blue"):
            state["status"] = "win"
            state["winner"] = "blue"
        else:
            state["player"] = "red"

    return state