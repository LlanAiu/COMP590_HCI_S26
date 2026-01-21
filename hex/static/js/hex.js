const size = 11;
let R = 20; // Will be set dynamically
let boardOffsetX = 0;
let boardOffsetY = 0;
let state = null;
const myRole = "red";
let locked = false;

// Lozenge hex geometry: p(i,j) = i*u + j*v
function hexToPixel(row, col) {
    const x = col * (Math.sqrt(3) * R) + row * (Math.sqrt(3) / 2 * R) + boardOffsetX;
    const y = row * (1.5 * R) + boardOffsetY;
    return [x, y];
}

// build a hex path (does not stroke/fill)
function drawHexPath(ctx, x, y, radius, scale = 1.0) {
    ctx.beginPath();
    const r = radius * scale;
    for (let i = 0; i < 6; i++) {
        const angle = Math.PI / 6 + i * Math.PI / 3; // rotated 30° flat-top
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
        const [xTop, yTop] = hexToPixel(0, c);
        drawHexPath(ctx, xTop, yTop, R, 1.25);
        ctx.fill();
        const [xBot, yBot] = hexToPixel(size - 1, c);
        drawHexPath(ctx, xBot, yBot, R, 1.25);
        ctx.fill();
    }

    // Blue bases (first and last columns)
    ctx.fillStyle = "blue";
    for (let r = 0; r < size; r++) {
        const [xLeft, yLeft] = hexToPixel(r, 0);
        drawHexPath(ctx, xLeft, yLeft, R, 1.25);
        ctx.fill();
        const [xRight, yRight] = hexToPixel(r, size - 1);
        drawHexPath(ctx, xRight, yRight, R, 1.25);
        ctx.fill();
    }

    ctx.restore();
}

function computeBoardGeometry(canvas) {
    const margin = 20;
    const w = canvas.width, h = canvas.height;
    const maxRwidth = (w - 2 * margin) / ((size - 1) * Math.sqrt(3) + (size - 1) * Math.sqrt(3) / 2 + 2);
    const maxRheight = (h - 2 * margin) / ((size - 1) * 1.5 + 2);
    R = Math.floor(Math.min(maxRwidth, maxRheight));
    const actualBoardWidth = (size - 1) * Math.sqrt(3) * R + (size - 1) * Math.sqrt(3) / 2 * R + 2 * R;
    const actualBoardHeight = (size - 1) * 1.5 * R + 2 * R;
    boardOffsetX = (w - actualBoardWidth) / 2 + R;
    boardOffsetY = (h - actualBoardHeight) / 2 + R;
}

function drawBoard(ctx) {
    computeBoardGeometry(ctx.canvas);
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    drawBases(ctx);
    for (let r = 0; r < size; r++) {
        for (let c = 0; c < size; c++) {
            const [x, y] = hexToPixel(r, c);
            const cell = state.board[r][c];
            const fill = cell === "R" ? "red" : cell === "B" ? "blue" : "white";
            const highlight = (state.lastMove && state.lastMove === String.fromCharCode(65 + c) + (r + 1));
            drawHex(ctx, x, y, fill, highlight);
        }
    }
}


function renderMoveHistory() {
    if (!state || !state.moves) return;
    const tableBody = document.querySelector('#moveHistoryTable tbody');
    tableBody.innerHTML = '';
    // Build two columns: Red and Blue, up to last 10 moves
    const moves = state.moves.slice(-10); // last 10 moves
    const redMoves = [];
    const blueMoves = [];
    for (let i = 0; i < moves.length; i++) {
        if (moves[i].player === 'R') redMoves.push(moves[i].move);
        else if (moves[i].player === 'B') blueMoves.push(moves[i].move);
    }
    // Pad arrays to equal length
    const maxLen = Math.max(redMoves.length, blueMoves.length);
    while (redMoves.length < maxLen) redMoves.push('');
    while (blueMoves.length < maxLen) blueMoves.push('');
    for (let i = 0; i < maxLen; i++) {
        const row = document.createElement('tr');
        const redCell = document.createElement('td');
        redCell.textContent = redMoves[i];
        redCell.style.textAlign = 'center';
        const blueCell = document.createElement('td');
        blueCell.textContent = blueMoves[i];
        blueCell.style.textAlign = 'center';
        row.appendChild(redCell);
        row.appendChild(blueCell);
        tableBody.appendChild(row);
    }
}

async function startGame() {
    const res = await fetch('/create-game', { method: 'POST' });
    state = await res.json();
    document.getElementById("status").innerText = " Game started. Red goes first.";
    drawBoard(document.getElementById("board").getContext("2d"));
    renderMoveHistory();
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
    console.log(state);
    locked = false;
    document.getElementById("status").innerText = " Turn: " + state.player + " | Move: " + state.lastMove + " | Status: " + state.status;
    drawBoard(document.getElementById("board").getContext("2d"));
    renderMoveHistory();
});

// Download moves button
document.getElementById("downloadMovesBtn").addEventListener("click", async () => {
    if (!state || !state.gameId) return;
    const res = await fetch(`/download-moves?gameId=${encodeURIComponent(state.gameId)}`);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "download failed" }));
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