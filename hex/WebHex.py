from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
import uvicorn, random, datetime
from collections import deque

app = FastAPI()

# --- Embedded HTML/JS ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Hex Game</title>
  <style>
    body { font-family: sans-serif; }
    canvas { border: 1px solid #000; display:block; margin: 10px 0; }
    #controls { margin-bottom: 8px; }
  </style>
</head>
<body>
  <h1>Hex Game</h1>
  <div id="controls">
    <button id="downloadMovesBtn">Download moves</button>
    <span id="status"></span>
  </div>
  <canvas id="board" width="1200" height="700"></canvas>

  <script>
    const size = 11;
    const R = 30;
    let state = null;
    let myRole = "red";
    let locked = false;

    // Lozenge hex geometry: p(i,j) = i*u + j*v
    function hexToPixel(row, col) {
      const x = col * (Math.sqrt(3) * R) + row * (Math.sqrt(3)/2 * R) + 50;
      const y = row * (1.5 * R) + 50;
      return [x, y];
    }

    // build a hex path (does not stroke/fill)
    function drawHexPath(ctx, x, y, radius, scale = 1.0) {
      ctx.beginPath();
      const r = radius * scale;
      for (let i = 0; i < 6; i++) {
        const angle = Math.PI/6 + i * Math.PI/3; // rotated 30° flat-top
        const px = x + r * Math.cos(angle);
        const py = y + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
    }

    // normal hex draw (uses drawHexPath)
    function drawHex(ctx, x, y, fillStyle, highlight = false) {
      drawHexPath(ctx, x, y, R, 1.0);
      ctx.fillStyle = fillStyle;
      ctx.fill();
      ctx.strokeStyle = highlight ? "yellow" : "black";
      ctx.lineWidth = highlight ? 3 : 1;
      ctx.stroke();
    }

    // draw subtle base highlights behind the board pieces
    function drawBases(ctx) {
      ctx.save();
      ctx.globalAlpha = 0.22;

      // Red bases (first and last rows)
      ctx.fillStyle = "red";
      for (let c = 0; c < size; c++) {
        let [xTop, yTop] = hexToPixel(0, c);
        drawHexPath(ctx, xTop, yTop, R, 1.25);
        ctx.fill();
        let [xBot, yBot] = hexToPixel(size - 1, c);
        drawHexPath(ctx, xBot, yBot, R, 1.25);
        ctx.fill();
      }

      // Blue bases (first and last columns)
      ctx.fillStyle = "blue";
      for (let r = 0; r < size; r++) {
        let [xLeft, yLeft] = hexToPixel(r, 0);
        drawHexPath(ctx, xLeft, yLeft, R, 1.25);
        ctx.fill();
        let [xRight, yRight] = hexToPixel(r, size - 1);
        drawHexPath(ctx, xRight, yRight, R, 1.25);
        ctx.fill();
      }

      ctx.restore();
    }

    function drawBoard(ctx) {
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      drawBases(ctx);
      for (let r = 0; r < size; r++) {
        for (let c = 0; c < size; c++) {
          const [x, y] = hexToPixel(r, c);
          let cell = state.board[r][c];
          let fill = cell === "R" ? "red" : cell === "B" ? "blue" : "white";
          let highlight = (state.lastMove && state.lastMove === String.fromCharCode(65 + c) + (r + 1));
          drawHex(ctx, x, y, fill, highlight);
        }
      }
    }

    async function startGame() {
      const res = await fetch('/create-game', { method: 'POST' });
      state = await res.json();
      document.getElementById("status").innerText = " Game started. Red goes first.";
      drawBoard(document.getElementById("board").getContext("2d"));
    }

    document.getElementById("board").addEventListener("click", async (e) => {
      if (locked || !state || state.status === "win" || state.player !== myRole) return;
      locked = true;
      const rect = e.target.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      let best = null, bestDist = 1e9;
      for (let r = 0; r < size; r++) {
        for (let c = 0; c < size; c++) {
          const [hx, hy] = hexToPixel(r, c);
          const d = (hx - x) ** 2 + (hy - y) ** 2;
          if (d < bestDist) { bestDist = d; best = [r, c]; }
        }
      }
      const move = String.fromCharCode(65 + best[1]) + (best[0] + 1);
      const res = await fetch('/submit-move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gameId: state.gameId, move: move, player: state.player })
      });
      state = await res.json();
      locked = false;
      document.getElementById("status").innerText = " Turn: " + state.player + " | Move: " + state.lastMove + " | Status: " + state.status;
      drawBoard(document.getElementById("board").getContext("2d"));
    });

    // Download moves button
    document.getElementById("downloadMovesBtn").addEventListener("click", async () => {
      if (!state || !state.gameId) return;
      const res = await fetch(`/download-moves?gameId=${encodeURIComponent(state.gameId)}`);
      if (!res.ok) {
        const err = await res.json().catch(()=>({error:"download failed"}));
        alert("Download failed: " + (err.error || res.statusText));
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `hex_moves_${state.gameId}.txt`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });

    startGame();
  </script>
</body>
</html>
"""

# --- In-memory game storage ---
games = {}

def empty_board(n=11):
    return ["0" * n for _ in range(n)]

def coord_to_index(coord):
    col = ord(coord[0]) - 65
    row = int(coord[1:]) - 1
    return row, col

def check_win(board, player):
    n = len(board)
    visited = set()
    q = deque()
    if player == "red":
        for c in range(n):
            if board[0][c] == "R":
                q.append((0, c))
                visited.add((0, c))
        while q:
            r, c = q.popleft()
            if r == n - 1:
                return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == "R" and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
    else:
        for r in range(n):
            if board[r][0] == "B":
                q.append((r, 0))
                visited.add((r, 0))
        while q:
            r, c = q.popleft()
            if c == n - 1:
                return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == "B" and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
    return False

def ai_move(board, opponent):
    n = len(board)
    opp = "R" if opponent == "blue" else "B"
    empties = []
    adj = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == "0":
                empties.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == opp:
                        adj.append((r, c))
                        break
    choice = random.choice(adj if adj else empties)
    return chr(65 + choice[1]) + str(choice[0] + 1)

@app.get("/", response_class=HTMLResponse)
async def root():
    return INDEX_HTML

@app.post("/create-game")
async def create_game():
    game_id = f"g{random.randint(1000,9999)}"
    games[game_id] = {
        "gameId": game_id,
        "board": empty_board(),
        "player": "red",
        "lastMove": "",
        "moveNumber": 0,
        "status": "ok",
        "moves": []  # chronological move list
    }
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

