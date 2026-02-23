// Minimal client for interacting with the circle-packing API and canvas.
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const gridSelect = document.getElementById('gridSelect');
const numCirclesInput = document.getElementById('numCircles');
const generateBtn = document.getElementById('generateBtn');
const showGrid = document.getElementById('showGrid');
const forceTangent = document.getElementById('forceTangent');
const areaDisplay = document.getElementById('areaDisplay');

let centers = [];
let bbox = null;
let pixelsPerUnit = 40;
let hoverSnap = null; // world coords where a new circle would be placed

function resizeCanvas() {
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
    draw();
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();

generateBtn.addEventListener('click', async () => {
    const num = parseInt(numCirclesInput.value) || 1;
    const grid = gridSelect.value === 'none' ? 'square' : gridSelect.value;
    const res = await fetch('/api/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ num_circles: num, grid }) });
    const j = await res.json();
    centers = j.centers;
    bbox = j.bbox;
    // compute pixelsPerUnit to fit
    const margin = 0.9;
    const canvasW = canvas.width;
    const canvasH = canvas.height;
    pixelsPerUnit = Math.max(1, Math.min(canvasW / (j.width_units), canvasH / (j.height_units)) * margin);
    areaDisplay.textContent = `BBox area (units^2): ${j.area_units.toFixed(3)}`;
    draw();
});

function worldToCanvas(x, y) {
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    return [cx + x * pixelsPerUnit, cy + y * pixelsPerUnit];
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (showGrid.checked && centers.length > 0) {
        drawGrid();
    }
    // draw circles
    ctx.strokeStyle = '#2b2b2b';
    ctx.fillStyle = 'rgba(79, 144, 255, 0.85)';
    ctx.lineWidth = 1;
    ctx.shadowColor = 'rgba(0,0,0,0.15)';
    ctx.shadowBlur = 8;
    for (const c of centers) {
        const [cx, cy] = worldToCanvas(c[0], c[1]);
        const r = pixelsPerUnit * 1.0;
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    }
    ctx.shadowBlur = 0;
    if (bbox) {
        // draw bbox expanded by radius
        const minx = bbox.minx - 1, maxx = bbox.maxx + 1, miny = bbox.miny - 1, maxy = bbox.maxy + 1;
        const [x1, y1] = worldToCanvas(minx, miny);
        const [x2, y2] = worldToCanvas(maxx, maxy);
        ctx.strokeStyle = 'red'; ctx.lineWidth = 2; ctx.strokeRect(x1, y2, x2 - x1, y1 - y2);
    }

    // draw hover outline if present
    if (hoverSnap) {
        const [hx, hy] = worldToCanvas(hoverSnap.x, hoverSnap.y);
        const hr = pixelsPerUnit * 1.0;
        ctx.save();
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(0,0,0,0.85)';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(hx, hy, hr, 0, Math.PI * 2); ctx.stroke();
        ctx.restore();
    }
}

function drawGrid() {
    ctx.save();
    ctx.strokeStyle = '#ddd'; ctx.lineWidth = 1;
    const grid = gridSelect.value;
    if (grid === 'square') {
        // draw lines at integer multiples of 2 units
        const step = 2;
        const w = canvas.width, h = canvas.height; const cx = canvas.width / 2, cy = canvas.height / 2;
        const unitsW = Math.ceil(w / pixelsPerUnit / step) * step;
        for (let x = -unitsW; x <= unitsW; x += step) {
            const [sx,] = worldToCanvas(x, 0);
            ctx.beginPath(); ctx.moveTo(sx, 0); ctx.lineTo(sx, h); ctx.stroke();
        }
        const unitsH = Math.ceil(h / pixelsPerUnit / step) * step;
        for (let y = -unitsH; y <= unitsH; y += step) {
            const [, sy] = worldToCanvas(0, y);
            ctx.beginPath(); ctx.moveTo(0, sy); ctx.lineTo(w, sy); ctx.stroke();
        }
    } else if (grid === 'hex') {
        // draw hex grid points (approx)
        const v = Math.sqrt(3);
        const step = 2;
        const range = 30;
        for (let r = -range; r <= range; r++) {
            for (let c = -range; c <= range; c++) {
                const x = c * 2 + (r % 2) * 1;
                const y = r * v;
                const [sx, sy] = worldToCanvas(x, y);
                ctx.beginPath(); ctx.arc(sx, sy, 1, 0, Math.PI * 2); ctx.fillStyle = '#eee'; ctx.fill();
            }
        }
    }
    ctx.restore();
}

// simple placement snapping: click to place a circle tangent to nearest existing circle or snap to grid
canvas.addEventListener('click', (ev) => {
    const rect = canvas.getBoundingClientRect();
    const px = ev.clientX - rect.left;
    const py = ev.clientY - rect.top;
    // convert to world coords
    const wx = (px - canvas.width / 2) / pixelsPerUnit;
    const wy = (py - canvas.height / 2) / pixelsPerUnit;

    const snap = computeSnap(wx, wy);
    centers.push([snap.x, snap.y]);
    // update bbox
    const xs = centers.map(c => c[0]); const ys = centers.map(c => c[1]);
    bbox = { minx: Math.min(...xs), maxx: Math.max(...xs), miny: Math.min(...ys), maxy: Math.max(...ys) };
    const width_units = (bbox.maxx - bbox.minx) + 2.0;
    const height_units = (bbox.maxy - bbox.miny) + 2.0;
    areaDisplay.textContent = `BBox area (units^2): ${(width_units * height_units).toFixed(3)}`;
    draw();
});

// compute snapping logic in one place so hover and click use same behavior
function computeSnap(wx, wy) {
    let snap = { x: wx, y: wy };

    if (showGrid.checked) {
        const grid = gridSelect.value;
        if (grid === 'square') {
            snap.x = Math.round(wx / 2) * 2;
            snap.y = Math.round(wy / 2) * 2;
        } else if (grid === 'hex') {
            const v = Math.sqrt(3);
            let r = Math.round(wy / v);
            let c = Math.round((wx - (r % 2) * 1) / 2);
            snap.x = c * 2 + (r % 2) * 1;
            snap.y = r * v;
        }
    }

    // apply tangent snapping only when enabled
    if (forceTangent && forceTangent.checked && centers.length > 0) {
        let bestIdx = -1; let bestDist = Infinity;
        centers.forEach((c, i) => { const d = Math.hypot(c[0] - wx, c[1] - wy); if (d < bestDist) { bestDist = d; bestIdx = i } });
        const base = centers[bestIdx];
        const vx = wx - base[0]; const vy = wy - base[1];
        const mag = Math.hypot(vx, vy) || 1.0;
        snap.x = base[0] + (vx / mag) * 2.0;
        snap.y = base[1] + (vy / mag) * 2.0;
    }

    return snap;
}

canvas.addEventListener('mousemove', (ev) => {
    const rect = canvas.getBoundingClientRect();
    const px = ev.clientX - rect.left;
    const py = ev.clientY - rect.top;
    const wx = (px - canvas.width / 2) / pixelsPerUnit;
    const wy = (py - canvas.height / 2) / pixelsPerUnit;
    hoverSnap = computeSnap(wx, wy);
    draw();
});

canvas.addEventListener('mouseleave', () => { hoverSnap = null; draw(); });

