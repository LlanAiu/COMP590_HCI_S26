import uvicorn
from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import datetime
from pathlib import Path

app = FastAPI()

class SaveRequest(BaseModel):
    moves: str

CSS = """
:root {
    --bg-color: #C0C0C0;
    --text-color: #0f172a;
    --primary-color: #3b82f6; /* Blue */
    --secondary-color: #ef4444; /* Red */
    --accent-color: #8b5cf6;
    --glass-bg: rgba(255, 255, 255, 0.7);
    --glass-border: rgba(0, 0, 0, 0.1);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    height: 100vh;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
}

#app {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    position: relative;
}

header {
    padding: 0.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(10px);
    z-index: 10;
    border-bottom: 1px solid var(--glass-border);
    height: 60px;
}

.header-left, .header-right {
    flex: 1;
    display: flex;
    align-items: center;
}

.header-right {
    justify-content: flex-end;
}

.header-center {
    flex: 2;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
}

h1 {
    font-weight: 600;
    letter-spacing: 2px;
    background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

#game-controls {
    display: flex;
    gap: 0.5rem;
}

#game-message {
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--text-color);
}

#game-message.winner-red { color: var(--secondary-color); }
#game-message.winner-blue { color: var(--primary-color); }

.btn {
    padding: 0.4rem 0.8rem;
    border: none;
    border-radius: 6px;
    font-family: inherit;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    transition: transform 0.2s, filter 0.2s;
}

.hidden {
    display: none !important;
}

.button-group {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

.btn {
    padding: 0.8rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-family: inherit;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, filter 0.2s;
}

.btn:hover {
    transform: translateY(-2px);
    filter: brightness(1.1);
}

.btn.primary {
    background: var(--primary-color);
    color: white;
}

.btn.secondary {
    background: var(--secondary-color);
    color: white;
}

main {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: stretch;
    overflow: hidden;
}

#canvas-container {
    flex: 1;
    position: relative;
    overflow: hidden;
    min-width: 0; /* Allow shrinking if needed */
}

#sidebar {
    width: 250px;
    background: var(--glass-bg);
    border-right: 1px solid var(--glass-border);
    padding: 1rem;
    overflow-y: auto;
    backdrop-filter: blur(12px);
    display: flex;
    flex-direction: column;
}

.move-history {
    width: 100%;
}

.move-history table {
    width: 100%;
    border-collapse: collapse;
    color: var(--text-color);
}

.move-history th {
    position: sticky;
    top: 0;
    background: rgba(15, 23, 42, 0.9);
    padding: 0.5rem;
    z-index: 1;
}

.move-history th.red { color: var(--secondary-color); }
.move-history th.blue { color: var(--primary-color); }

.move-history td {
    padding: 0.4rem;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 0.9rem;
}
"""

JS = """
// --- HexUtils.js ---
class Hex {
    constructor(q, r) {
        this.q = q;
        this.r = r;
        this.s = -q - r;
    }

    toString() {
        return `${this.q},${this.r}`;
    }

    equals(other) {
        return this.q === other.q && this.r === other.r;
    }

    add(other) {
        return new Hex(this.q + other.q, this.r + other.r);
    }
}

const DIRECTIONS = [
    new Hex(1, 0), new Hex(1, -1), new Hex(0, -1),
    new Hex(-1, 0), new Hex(-1, 1), new Hex(0, 1)
];

class HexLayout {
    constructor(size, origin) {
        this.size = size;     // pixel size
        this.origin = origin; // center point {x, y}
    }

    // Convert Hex to Pixel center
    toPixel(hex) {
        const x = this.size * (Math.sqrt(3) * hex.q + Math.sqrt(3)/2 * hex.r);
        const y = this.size * (3./2 * hex.r);
        return {
            x: x + this.origin.x,
            y: y + this.origin.y
        };
    }

    // Convert Pixel to Hex (Rounding required)
    pixelToHex(p) {
        const pt = {
            x: (p.x - this.origin.x) / this.size,
            y: (p.y - this.origin.y) / this.size
        };
        const q = (Math.sqrt(3)/3 * pt.x - 1/3 * pt.y);
        const r = (2/3 * pt.y);
        return this.hexRound({ q, r, s: -q-r });
    }

    hexRound(h) {
        let q = Math.round(h.q);
        let r = Math.round(h.r);
        let s = Math.round(h.s);
        
        const q_diff = Math.abs(q - h.q);
        const r_diff = Math.abs(r - h.r);
        const s_diff = Math.abs(s - h.s);

        if (q_diff > r_diff && q_diff > s_diff) {
            q = -r - s;
        } else if (r_diff > s_diff) {
            r = -q - s;
        } else {
            s = -q - r;
        }
        return new Hex(q, r);
    }
}

// --- Game.js ---
class UnionFind {
    constructor() {
        this.parent = new Map();
    }

    find(i) {
        if (!this.parent.has(i)) {
            this.parent.set(i, i);
        }
        if (this.parent.get(i) === i) {
            return i;
        }
        const root = this.find(this.parent.get(i));
        this.parent.set(i, root);
        return root;
    }

    union(i, j) {
        const rootI = this.find(i);
        const rootJ = this.find(j);
        if (rootI !== rootJ) {
            this.parent.set(rootI, rootJ);
        }
    }
    
    connected(i, j) {
        return this.find(i) === this.find(j);
    }
}

class Game {
    constructor(size = 11) {
        this.size = size;
        this.board = new Map(); // "q,r" -> "red" | "blue"
        this.turn = 'red'; // 'red' starts
        this.winner = null;
        this.gameOver = false;
        
        // Win detection
        this.ufRed = new UnionFind();
        this.ufBlue = new UnionFind();
        
        this.RED_TOP = "RED_TOP";
        this.RED_BOTTOM = "RED_BOTTOM";
        this.BLUE_LEFT = "BLUE_LEFT";
        this.BLUE_RIGHT = "BLUE_RIGHT";
        
        this.moves = []; // List of moves
        this.winningPath = []; // Array of Hex objects representing the winning path
        this.winningPathSet = new Set(); // Set of "q,r" strings for fast lookup
    }

    reset() {
        this.board.clear();
        this.turn = 'red';
        this.winner = null;
        this.gameOver = false;
        this.ufRed = new UnionFind();
        this.ufBlue = new UnionFind();
        this.moves = [];
        this.winningPath = [];
        this.winningPathSet = new Set();
    }

    isValidMove(hex) {
        if (this.gameOver) return false;
        if (this.board.has(hex.toString())) return false;
        
        // Check bounds for Lozenge shape (Rhombus)
        // In axial coords/rhombus map: 0 <= q < size, 0 <= r < size
        return hex.q >= 0 && hex.q < this.size &&
               hex.r >= 0 && hex.r < this.size;
    }

    makeMove(hex) {
        if (!this.isValidMove(hex)) return false;

        const player = this.turn;
        this.board.set(hex.toString(), player);
        this.moves.push({ player, hex });
        this.updateWinStatus(hex, player);

        if (!this.winner) {
            this.turn = this.turn === 'red' ? 'blue' : 'red';
        } else {
            this.gameOver = true;
        }
        return true;
    }

    updateWinStatus(hex, player) {
        const key = hex.toString();
        
        if (player === 'red') {
            // Connect to neighbors
            for (let dir of DIRECTIONS) {
                const neighbor = hex.add(dir);
                if (this.board.get(neighbor.toString()) === 'red') {
                    this.ufRed.union(key, neighbor.toString());
                }
            }
            
            if (hex.r === 0) this.ufRed.union(key, this.RED_TOP);
            if (hex.r === this.size - 1) this.ufRed.union(key, this.RED_BOTTOM);
            
            if (this.ufRed.connected(this.RED_TOP, this.RED_BOTTOM)) {
                this.winner = 'red';
                this.computeWinningPath('red');
            }
        } else {
            // Blue
            for (let dir of DIRECTIONS) {
                const neighbor = hex.add(dir);
                if (this.board.get(neighbor.toString()) === 'blue') {
                    this.ufBlue.union(key, neighbor.toString());
                }
            }
            if (hex.q === 0) this.ufBlue.union(key, this.BLUE_LEFT);
            if (hex.q === this.size - 1) this.ufBlue.union(key, this.BLUE_RIGHT);
            
            if (this.ufBlue.connected(this.BLUE_LEFT, this.BLUE_RIGHT)) {
                this.winner = 'blue';
                this.computeWinningPath('blue');
            }
        }
    }

    // Build the winning path (list of hexes) for the given player
    computeWinningPath(player) {
        this.winningPath = [];
        this.winningPathSet = new Set();

        let uf = player === 'red' ? this.ufRed : this.ufBlue;
        let start = player === 'red' ? this.RED_TOP : this.BLUE_LEFT;

        // Determine the canonical root representing the connected component
        const root = uf.find(start);

        // Iterate keys in the union-find parent map and collect those in the root
        for (let k of uf.parent.keys()) {
            // only include real hex keys that look like "q,r"
            if (typeof k === 'string' && k.indexOf(',') !== -1) {
                if (uf.find(k) === root) {
                    const parts = k.split(',').map(Number);
                    const h = new Hex(parts[0], parts[1]);
                    this.winningPath.push(h);
                    this.winningPathSet.add(k);
                }
            }
        }
    }
    
    getBoard() {
        return this.board;
    }
}

// --- Renderer.js ---
class Renderer {
    constructor(canvas, game) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.game = game;
        this.layout = new HexLayout(25, { x: 0, y: 0 }); // Default size, updated in resize
        
        this.hoverHex = null;
        // Colors
        this.colors = {
            board: '#1e293b',
            grid: '#334155',
            red: '#ef4444',
            blue: '#3b82f6',
            hover: 'rgba(255, 255, 255, 0.2)',
            highlight: 'rgba(255, 255, 255, 0.1)'
        };
    }

    resize() {
        this.canvas.width = this.canvas.parentElement.offsetWidth;
        this.canvas.height = this.canvas.parentElement.offsetHeight;
        
        const boardSize = this.game.size;
        const minDim = Math.min(this.canvas.width, this.canvas.height);
        const hexSize = (minDim / (boardSize * 3)) * 1.5; // optimized for margin
        
        this.layout.size = hexSize;
        
        const centerHex = new Hex((boardSize-1)/2, (boardSize-1)/2);
        this.layout.origin = { x: 0, y: 0 };
        const pCenter = this.layout.toPixel(centerHex);
        
        this.layout.origin = {
            x: this.canvas.width / 2 - pCenter.x,
            y: this.canvas.height / 2 - pCenter.y
        };
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw Board Background / Grid
        for (let r = 0; r < this.game.size; r++) {
            for (let q = 0; q < this.game.size; q++) {
                const hex = new Hex(q, r);
                // Fill with board background or highlight winning path
                const key = hex.toString();
                const bg = (this.game.winningPathSet && this.game.winningPathSet.has(key)) ? this.colors.highlight : 'black';
                this.drawHexPoly(hex, bg, 'fill');
                // Outline with white
                this.drawHexPoly(hex, 'white', 'stroke');
            }
        }
        
        // Draw Borders
        this.drawBorders();
        
        // Draw Labels
        this.drawLabels();
        
        // Draw Pieces
        this.game.board.forEach((color, key) => {
            const [q, r] = key.split(',').map(Number);
            this.drawPiece(new Hex(q, r), this.colors[color]);
        });
        
        // Draw Hover
        if (this.hoverHex && this.game.isValidMove(this.hoverHex)) {
            this.drawHexPoly(this.hoverHex, this.colors.hover, 'fill');
            this.drawPiece(this.hoverHex, this.colors[this.game.turn], 0.5);
        }
    }

    drawBorders() {
        const size = this.game.size;
        const red = this.colors.red;
        const blue = this.colors.blue;

        // Top Red Border
        for (let q = 0; q < size; q++) {
            const hex = new Hex(q, 0);
            this.drawEdge(hex, 3, red); // NW
            this.drawEdge(hex, 4, red); // NE
        }

        // Bottom Red Border
        for (let q = 0; q < size; q++) {
            const hex = new Hex(q, size - 1);
            this.drawEdge(hex, 0, red); // SE
            this.drawEdge(hex, 1, red); // SW
        }

        // Left Blue Border
        for (let r = 0; r < size; r++) {
            const hex = new Hex(0, r);
            this.drawEdge(hex, 2, blue); // W
            // Skip SW edge for bottom-left corner (handled by Red Bottom)
            if (r < size - 1) {
                this.drawEdge(hex, 1, blue); // SW
            }
        }

        // Right Blue Border
        for (let r = 0; r < size; r++) {
            const hex = new Hex(size - 1, r);
            this.drawEdge(hex, 5, blue); // E
            // Skip NE edge for top-right corner (handled by Red Top)
            if (r > 0) {
                this.drawEdge(hex, 4, blue); // NE
            }
        }
    }

    drawLabels() {
        const size = this.game.size;
        const hexSize = this.layout.size;

        this.ctx.font = "bold 16px Outfit, sans-serif";
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";
        this.ctx.fillStyle = "black";

        // Row Labels (A-K) - Left Side
        for (let r = 0; r < size; r++) {
            const hex = new Hex(0, r);
            const center = this.layout.toPixel(hex);
            
            // Shift left from the first cell of the row
            // The magic number 1.5 ensures enough padding
            const x = center.x - hexSize * 1.5;
            const y = center.y;
            
            const label = String.fromCharCode(65 + r); // A, B, C...
            this.ctx.fillText(label, x, y);
        }

        // Column Labels (1-11) - Top Side
        for (let q = 0; q < size; q++) {
            // (q, 0) is the top-most cell in the column q
            const hex = new Hex(q, 0);
            const center = this.layout.toPixel(hex);
            
            // Shift up from the first cell of the column
            // Need to account for the skew.
            // Actually, for (q,0), the top direction is roughly -y.
            const x = center.x;
            const y = center.y - hexSize * 1.5;
            
            const label = (q + 1).toString();
            this.ctx.fillText(label, x, y);
        }
    }

    drawEdge(hex, edgeIndex, color) {
        const center = this.layout.toPixel(hex);
        const size = this.layout.size;
        
        const angle1_deg = 60 * edgeIndex + 30;
        const angle2_deg = 60 * (edgeIndex + 1) + 30;
        
        const a1 = Math.PI / 180 * angle1_deg;
        const a2 = Math.PI / 180 * angle2_deg;
        
        const x1 = center.x + size * Math.cos(a1);
        const y1 = center.y + size * Math.sin(a1);
        
        const x2 = center.x + size * Math.cos(a2);
        const y2 = center.y + size * Math.sin(a2);
        
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 5;
        this.ctx.lineCap = 'round';
        this.ctx.stroke();
    }

    drawHexPoly(hex, color, mode = 'stroke') {
        const center = this.layout.toPixel(hex);
        const size = this.layout.size;
        
        this.ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const angle_deg = 60 * i + 30; // Pointy topped for standard Hex
            const angle_rad = Math.PI / 180 * angle_deg;
            const px = center.x + size * Math.cos(angle_rad);
            const py = center.y + size * Math.sin(angle_rad);
            if (i === 0) this.ctx.moveTo(px, py);
            else this.ctx.lineTo(px, py);
        }
        this.ctx.closePath();
        
        this.ctx.lineWidth = 2;
        if (mode === 'stroke') {
            this.ctx.strokeStyle = color;
            this.ctx.stroke();
        } else {
            this.ctx.fillStyle = color;
            this.ctx.fill();
        }
    }

    drawPiece(hex, color, alpha = 1.0) {
        const center = this.layout.toPixel(hex);
        const radius = this.layout.size * 0.7; // Piece is smaller than cell
        
        this.ctx.beginPath();
        this.ctx.arc(center.x, center.y, radius, 0, 2 * Math.PI);
        this.ctx.fillStyle = color;
        this.ctx.globalAlpha = alpha;
        this.ctx.fill();
        this.ctx.globalAlpha = 1.0;
        
        this.ctx.strokeStyle = 'rgba(0,0,0,0.3)';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }
}

// --- Input.js ---
class InputHandler {
    constructor(canvas, game) {
        this.canvas = canvas;
        this.game = game;
        this.mouse = { x: 0, y: 0 };
        this.setupListeners();
    }

    setupListeners() {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = e.clientX - rect.left;
            this.mouse.y = e.clientY - rect.top;
            this.game.onMouseMove(this.mouse.x, this.mouse.y);
        });

        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // Left click
                this.game.onClick();
            }
        });
        
        window.addEventListener('keydown', (e) => {
             this.game.onKeyDown(e.key);
        });
    }
}

// --- AI.js ---
class AI {
    constructor(game) {
        this.game = game;
    }

    getMove() {
        const available = [];
        for (let r = 0; r < this.game.size; r++) {
            for (let q = 0; q < this.game.size; q++) {
                const h = new Hex(q, r);
                if (this.game.isValidMove(h)) {
                    available.push(h);
                }
            }
        }
        
        if (available.length === 0) return null;
        
        // Random pick
        const idx = Math.floor(Math.random() * available.length);
        return available[idx];
    }
}

// --- app.js (Application Logic) ---
const game = new Game();
const canvas = document.getElementById('game-canvas');
const renderer = new Renderer(canvas, game);
const input = new InputHandler(canvas, game);
const ai = new AI(game);

// UI Elements
const statusDisplay = document.getElementById('status-display');
const btnPvP = document.getElementById('btn-pvp');
const btnPvAI = document.getElementById('btn-pvai');
const btnAIAI = document.getElementById('btn-aiai');
const gameMessage = document.getElementById('game-message');
const gameControls = document.getElementById('game-controls');

let gameMode = 'pvp'; // 'pvp' or 'pvai'
let isAiTurn = false;

// Attach input hooks to Game
game.onMouseMove = (x, y) => {
    // Convert pixel to hex
    const p = { x, y };
    const h = renderer.layout.pixelToHex(p);
    renderer.hoverHex = h;
};

game.onClick = () => {
    if (game.gameOver) return;
    
    if (renderer.hoverHex) {
        attemptMove(renderer.hoverHex);
    }
};

game.onKeyDown = (key) => {
    if (game.gameOver) return;

    if (!renderer.hoverHex) {
        const mid = Math.floor(game.size / 2);
        renderer.hoverHex = new Hex(mid, mid);
        return;
    }

    let nextHex = null;
    let dir = null;

    switch(key) {
        case 'ArrowUp': 
        case 'w': dir = 2; break; // (0, -1) Top
        case 'ArrowDown': 
        case 's': dir = 5; break; // (0, 1) Bottom
        case 'ArrowLeft': 
        case 'a': dir = 3; break; // (-1, 0) Left-Top
        case 'ArrowRight': 
        case 'd': dir = 0; break; // (1, 0) Right
    }

    if (dir !== null) {
        nextHex = renderer.hoverHex.add(DIRECTIONS[dir]);
    } else {
        if (key === 'q') nextHex = renderer.hoverHex.add(DIRECTIONS[3]); 
        if (key === 'e') nextHex = renderer.hoverHex.add(DIRECTIONS[1]); 
        if (key === 'z') nextHex = renderer.hoverHex.add(DIRECTIONS[4]); 
        if (key === 'x') nextHex = renderer.hoverHex.add(DIRECTIONS[5]); 
    }
    
    if (nextHex) {
        renderer.hoverHex = nextHex;
    }
    
    if (key === 'Enter' || key === ' ') {
        attemptMove(renderer.hoverHex);
    }
};

function attemptMove(hex) {
    if (isAiTurn) return;

    const currentPlayer = game.turn;
    const success = game.makeMove(hex);
    if (success) {
        // Update Move List UI
        // Use the captured currentPlayer instead of inferring from game.turn
        updateMoveList(hex, currentPlayer);
        
        checkGameState();
        if (!game.gameOver && gameMode === 'pvai' && game.turn === 'blue') {
            isAiTurn = true;
            setTimeout(() => {
                const aiMove = ai.getMove();
                if (aiMove) {
                    game.makeMove(aiMove);
                    // Update Move List UI for AI (Blue)
                    updateMoveList(aiMove, 'blue');
                    checkGameState();
                }
                isAiTurn = false;
            }, 500);
        }
    }
}

function checkGameState() {
    if (game.gameOver) {
        const winnerName = game.winner.toUpperCase();
        gameMessage.textContent = `${winnerName} WINS!`;
        gameMessage.className = game.winner === 'red' ? 'winner-red' : 'winner-blue';
        gameMessage.classList.remove('hidden');
        gameControls.classList.remove('hidden'); // Ensure controls remain visible for restart
        statusDisplay.textContent = "Game Over";
    } else {
        gameMessage.classList.add('hidden');
        gameControls.classList.remove('hidden');
        const pName = game.turn.toUpperCase();
        statusDisplay.textContent = `${pName}'s Turn`;
        statusDisplay.style.color = pName === 'RED' ? 'var(--secondary-color)' : 'var(--primary-color)';
    }
}

function startGame(mode) {
    gameMode = mode;
    game.reset();
    isAiTurn = false;
    isAiTurn = false; // Duplicate initialization removed in cleanup
    
    gameMessage.classList.add('hidden');
    
    // Clear move list
    document.getElementById('move-list').innerHTML = '';
    
    checkGameState();
}

window.addEventListener('resize', () => renderer.resize());
renderer.resize();

btnPvP.addEventListener('click', () => startGame('pvp'));
btnPvAI.addEventListener('click', () => startGame('pvai'));
btnAIAI.addEventListener('click', () => startAIVsAI());

function updateMoveList(hex, player) {
    const moveList = document.getElementById('move-list');
    
    // Notation: Row (A-K) + Col (1-11)
    const rowChar = String.fromCharCode(65 + hex.r);
    const colNum = hex.q + 1;
    const notation = `${rowChar}${colNum}`;
    
    if (player === 'red') {
        const tr = document.createElement('tr');
        const tdRed = document.createElement('td');
        tdRed.textContent = notation;
        tr.appendChild(tdRed);
        moveList.appendChild(tr);
    } else {
        // Blue move: append to last row
        const rows = moveList.getElementsByTagName('tr');
        if (rows.length > 0) {
            const lastRow = rows[rows.length - 1];
            const tdBlue = document.createElement('td');
            tdBlue.textContent = notation;
            lastRow.appendChild(tdBlue);
        } else {
            // Should not happen if Red starts, but handle gracefully
            const tr = document.createElement('tr');
            const tdRed = document.createElement('td'); // Empty red
            const tdBlue = document.createElement('td');
            tdBlue.textContent = notation;
            tr.appendChild(tdRed);
            tr.appendChild(tdBlue);
            moveList.appendChild(tr);
        }
    }
    
    // Scroll to bottom
    const sidebar = document.getElementById('sidebar');
    sidebar.scrollTop = sidebar.scrollHeight;
}

// --- Save Feature ---
function saveGame() {
    const moveList = document.getElementById('move-list');
    const rows = moveList.getElementsByTagName('tr');
    const moves = [];
    
    // We need to reconstruct the linear list of moves from the table
    // The table has rows with Red (col 0) and Blue (col 1)
    for (let row of rows) {
        const cells = row.getElementsByTagName('td');
        if (cells.length > 0) moves.push(cells[0].textContent); // Red
        if (cells.length > 1) moves.push(cells[1].textContent); // Blue
    }
    
    const movesStr = moves.join(',');
    
    fetch('/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ moves: movesStr }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        alert('Game saved to ' + data.filename);
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('Failed to save game');
    });
}

document.getElementById('btn-save').addEventListener('click', saveGame);

// --- AI vs AI Runner ---
function startAIVsAI() {
    gameMode = 'aivai';
    game.reset();
    // Clear move list UI
    document.getElementById('move-list').innerHTML = '';
    gameMessage.classList.add('hidden');

    // Run AI moves until game over, then auto-save
    function runAIMove() {
        if (game.gameOver) {
            // Save after the game finishes
            saveGame();
            return;
        }

        const currentPlayer = game.turn;
        const aiMove = ai.getMove();
        if (aiMove) {
            game.makeMove(aiMove);
            updateMoveList(aiMove, currentPlayer);
            checkGameState();
            // Small delay to allow UI update and to avoid blocking
            setTimeout(runAIMove, 50);
        } else {
            // No moves available -> save and stop
            saveGame();
        }
    }

    // Kick off the AI vs AI loop
    setTimeout(runAIMove, 150);
}

function loop() {
    renderer.draw();
    requestAnimationFrame(loop);
}

loop();
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hex Game</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
    {css_content}
    </style>
</head>
<body>
    <div id="app">
        <header>
            <div class="header-left">
                <h1>HEX</h1>
            </div>
            <div class="header-center">
                <div id="game-controls">
                    <button id="btn-pvp" class="btn secondary">Player vs Player</button>
                    <button id="btn-pvai" class="btn primary">Player vs AI</button>
                    <button id="btn-aiai" class="btn secondary">AI vs AI</button>
                    <button id="btn-save" class="btn secondary">Save</button>
                </div>
                <div id="game-message" class="hidden"></div>
            </div>
            <div class="header-right">
                <div id="status-display">Player's Turn</div>
            </div>
        </header>
        
        <main>
            <aside id="sidebar">
                <div class="move-history">
                    <table>
                        <thead>
                            <tr>
                                <th class="red">Red</th>
                                <th class="blue">Blue</th>
                            </tr>
                        </thead>
                        <tbody id="move-list">
                            <!-- Moves will appear here -->
                        </tbody>
                    </table>
                </div>
            </aside>
            <div id="canvas-container">
                <canvas id="game-canvas"></canvas>
            </div>
        </main>
    </div>

    <script>
    {js_content}
    </script>
</body>
</html>
"""


@app.post("/save")
async def save_game(request: SaveRequest):
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
    filename = f"HEX{timestamp}.txt"
    downloads_dir = Path.home() / "Downloads"
    try:
        downloads_dir.mkdir(parents=True, exist_ok=True)
        filepath = downloads_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(request.moves)
        return {"status": "success", "filename": str(filepath)}
    except Exception as e:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(request.moves)
        return {"status": "success", "filename": filename, "warning": str(e)}

@app.get("/", response_class=HTMLResponse)
async def get_game():
    return HTML_TEMPLATE.format(css_content=CSS, js_content=JS)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
