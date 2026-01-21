# builtin
from contextlib import asynccontextmanager
import random, datetime
from collections import deque

# external
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# internal
from app.modules import HexGame

@asynccontextmanager
def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- In-memory game storage ---
games = {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/create-game")
async def create_game():
    game_id = f"g{random.randint(1000,9999)}"
    games[game_id] = HexGame(game_id=game_id)
    return games[game_id]

@app.post("/submit-move")
async def submit_move(request: Request):
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

@app.get("/download-moves")
async def download_moves(gameId: str):
    state = games.get(gameId)
    if not state:
        return JSONResponse({"error": "Invalid gameId"}, status_code=400)

    moves = state.get("moves", [])
    text = ",".join(moves)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"hex_moves_{gameId}_{ts}.txt"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=text, headers=headers, media_type="text/plain")

