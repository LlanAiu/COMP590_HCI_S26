from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
import json
import time
from io import BytesIO

app = FastAPI()

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Circle Packing Lab</title>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; background: #f0f2f5; }
        #controls { margin: 20px; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        canvas { background: white; border: 1px solid #ccc; cursor: crosshair; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .stats { margin-top: 10px; font-size: 0.9em; color: #666; }
        button { cursor: pointer; padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h2>Circle Packing Explorer</h2>
    <div id="controls">
        Circles: <input type="number" id="circleLimit" value="23" min="1" style="width: 50px;">
        <label style="margin-left:10px;"><input type="checkbox" id="sqGrid" onclick="toggleGrid('sq')"> Square Grid</label>
        <label style="margin-left:10px; margin-right:10px;"><input type="checkbox" id="hexGrid" onclick="toggleGrid('hex')"> Hex Grid</label>
        <label style="margin-left:10px; margin-right:10px;">Bounding Shape:
            <select id="shapeSelect" onchange="draw()">
                <option value="square">Square</option>
                <option value="circle">Circle</option>
            </select>
        </label>
        <button onclick="submitLayout()">Submit Layout</button>
        <button onclick="resetCanvas()" style="background:#dc3545">Reset</button>
        <div class="stats" id="stats">Placed: 0 | Remaining: 23 | Square Side: 0</div>
    </div>
    <canvas id="canvas" width="800" height="800"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const limitInput = document.getElementById('circleLimit');
        const statsDisplay = document.getElementById('stats');
        const sqGridCb = document.getElementById('sqGrid');
        const hexGridCb = document.getElementById('hexGrid');
        const shapeSelect = document.getElementById('shapeSelect');

        let R = 20; // Visual radius (represents 1 unit)
        let circles = [];
        let draggingCircle = null;
        let offsetX, offsetY;
        let currentMouseX = 0, currentMouseY = 0;

        // Add event listener to update remaining count when limit changes
        limitInput.addEventListener('change', () => {
            updateScale();
            draw();
        });

        function updateScale() {
            const N = parseInt(limitInput.value) || 1;
            // Standard bounding box across is 2*ceil(sqrt(N)) circles.
            const numCirclesAcross = 2 * Math.ceil(Math.sqrt(N));
            
            // To fit this many circles across the width, and since each circle is diameter 2*R
            // The canvas width accommodates `numCirclesAcross` full circles
            const new_R = canvas.width / (numCirclesAcross * 2);
            
            if (R !== new_R && R > 0) {
                const scaleFactor = new_R / R;
                circles.forEach(c => {
                    c.x *= scaleFactor;
                    c.y *= scaleFactor;
                });
                R = new_R;
            } else if (R === 0) {
                R = new_R;
            }
        }
        
        // Initialize scale
        updateScale();

        function toggleGrid(type) {
            if (type === 'sq' && sqGridCb.checked) {
                hexGridCb.checked = false;
            } else if (type === 'hex' && hexGridCb.checked) {
                sqGridCb.checked = false;
            }
            draw();
        }

        function snapToGrid(x, y) {
            if (!sqGridCb.checked && !hexGridCb.checked) return { x, y };
            
            const unit = R;
            let bestPt = { x, y };

            if (sqGridCb.checked) {
                const spacing = 2 * unit;
                bestPt = {
                    x: Math.round(x / spacing) * spacing,
                    y: Math.round(y / spacing) * spacing
                };
            } else if (hexGridCb.checked) {
                const hexS = 2.001; // Slightly larger than 2 to prevent intersection
                const spacingX = hexS * unit;
                const spacingY = (Math.sqrt(3) / 2) * hexS * unit;
                const shiftX = (hexS / 2) * unit;
                
                let bestDist = Infinity;
                
                const rowG = Math.round(y / spacingY);
                for (let r = rowG - 1; r <= rowG + 1; r++) {
                    const y_candidate = r * spacingY;
                    const startX = (Math.abs(r) % 2 === 1) ? shiftX : 0;
                    
                    const k = Math.round((x - startX) / spacingX);
                    const x_candidate = startX + k * spacingX;
                    
                    const dist = Math.sqrt((x - x_candidate)**2 + (y - y_candidate)**2);
                    if (dist < bestDist) {
                        bestDist = dist;
                        bestPt = { x: x_candidate, y: y_candidate };
                    }
                }
            }
            return bestPt;
        }

        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // Check if clicking an existing circle (for dragging)
            draggingCircle = circles.find(c => {
                const dist = Math.sqrt((c.x - mouseX)**2 + (c.y - mouseY)**2);
                return dist < R;
            });

            if (draggingCircle) {
                offsetX = mouseX - draggingCircle.x;
                offsetY = mouseY - draggingCircle.y;
            } else if (circles.length < parseInt(limitInput.value)) {
                // Place new circle
                const pt = snapToGrid(mouseX, mouseY);
                circles.push({ x: pt.x, y: pt.y, id: Date.now() });
            }
            draw();
        });

        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            currentMouseX = e.clientX - rect.left;
            currentMouseY = e.clientY - rect.top;

            if (draggingCircle) {
                draggingCircle.x = currentMouseX - offsetX;
                draggingCircle.y = currentMouseY - offsetY;
                draw();
            }
        });

        window.addEventListener('keydown', (e) => {
            if (e.key === 'd' || e.key === 'D') {
                const initialCount = circles.length;
                circles = circles.filter(c => {
                    const dist = Math.sqrt((c.x - currentMouseX)**2 + (c.y - currentMouseY)**2);
                    return dist >= R; // Keep circles that do NOT overlap with the pointer
                });
                
                if (circles.length !== initialCount) {
                    draw();
                }
            }
        });

        window.addEventListener('mouseup', () => { 
            if (draggingCircle) {
                const pt = snapToGrid(draggingCircle.x, draggingCircle.y);
                draggingCircle.x = pt.x;
                draggingCircle.y = pt.y;
                draggingCircle = null; 
                draw();
            } else {
                draggingCircle = null;
            }
        });

        function checkCollision(c1) {
            return circles.some(c2 => {
                if (c1.id === c2.id) return false;
                const dist = Math.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2);
                return dist < (R * 1.9999);
            });
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw grid dots
            if (sqGridCb.checked || hexGridCb.checked) {
                ctx.fillStyle = '#e6b800'; // Dark yellow for visibility
                const unit = R;
                const r_dot = 4;
                
                if (sqGridCb.checked) {
                    const spacing = 2 * unit;
                    for (let x = 0; x <= canvas.width; x += spacing) {
                        for (let y = 0; y <= canvas.height; y += spacing) {
                            ctx.beginPath();
                            ctx.arc(x, y, r_dot, 0, Math.PI * 2);
                            ctx.fill();
                        }
                    }
                } else if (hexGridCb.checked) {
                    const hexS = 2.001; // Slightly larger than 2 to prevent intersection
                    const spacingX = hexS * unit;
                    const spacingY = (Math.sqrt(3) / 2) * hexS * unit;
                    const shiftX = (hexS / 2) * unit;
                    
                    let row = 0;
                    for (let y = 0; y <= canvas.height + spacingY; y += spacingY) {
                        const startX = (row % 2 !== 0) ? shiftX : 0;
                        for (let x = startX; x <= canvas.width + spacingX; x += spacingX) {
                            ctx.beginPath();
                            ctx.arc(x, y, r_dot, 0, Math.PI * 2);
                            ctx.fill();
                        }
                        row++;
                    }
                }
            }

            // Update stats
            const limit = parseInt(limitInput.value) || 0;
            const remaining = Math.max(0, limit - circles.length);
            const shape = shapeSelect.value;

            if (circles.length === 0) {
                statsDisplay.innerText = `Placed: 0 | Remaining: ${remaining} | ${shape === 'square' ? 'Square Side' : 'Radius'}: 0.00 units`;
                return;
            }

            // compute bounding shape based on selection
            function computeBoundingShape() {
                if (shape === 'square') {
                    // 1. Calculate Bounding Box (existing behavior)
                    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                    circles.forEach(c => {
                        if (c.x - R < minX) minX = c.x - R;
                        if (c.x + R > maxX) maxX = c.x + R;
                        if (c.y - R < minY) minY = c.y - R;
                        if (c.y + R > maxY) maxY = c.y + R;
                    });

                    const width = maxX - minX;
                    const height = maxY - minY;
                    const side = Math.max(width, height);
                    const centerX = minX + width / 2;
                    const centerY = minY + height / 2;
                    const sqX = centerX - side / 2;
                    const sqY = centerY - side / 2;
                    return { type: 'square', x: sqX, y: sqY, side: side };
                } else if (shape === 'circle') {
                    // Minimum Enclosing Circle (for circle centers) using Welzl-like algorithm
                    const pts = circles.map(c => ({ x: c.x, y: c.y }));
                    function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
                    function shuffle(array) {
                        for (let i = array.length - 1; i > 0; i--) {
                            const j = Math.floor(Math.random() * (i + 1));
                            [array[i], array[j]] = [array[j], array[i]];
                        }
                    }
                    function circleFromTwo(a, b) {
                        const cx = (a.x + b.x) / 2;
                        const cy = (a.y + b.y) / 2;
                        return { x: cx, y: cy, r: dist(a, b) / 2 };
                    }
                    function circleFromThree(a, b, c) {
                        const A = b.x - a.x, B = b.y - a.y;
                        const C = c.x - a.x, D = c.y - a.y;
                        const E = A * (a.x + b.x) + B * (a.y + b.y);
                        const F = C * (a.x + c.x) + D * (a.y + c.y);
                        const G = 2 * (A * (c.y - b.y) - B * (c.x - b.x));
                        if (Math.abs(G) < 1e-12) return null;
                        const cx = (D * E - B * F) / G;
                        const cy = (A * F - C * E) / G;
                        return { x: cx, y: cy, r: dist({ x: cx, y: cy }, a) };
                    }
                    function isInCircle(p, c) { return c && dist(p, { x: c.x, y: c.y }) <= c.r + 1e-8; }

                    if (pts.length === 0) return { type: 'circle', x: canvas.width/2, y: canvas.height/2, r: 0 };

                    shuffle(pts);
                    let c = { x: pts[0].x, y: pts[0].y, r: 0 };
                    for (let i = 1; i < pts.length; i++) {
                        const p = pts[i];
                        if (isInCircle(p, c)) continue;
                        c = { x: p.x, y: p.y, r: 0 };
                        for (let j = 0; j < i; j++) {
                            const q = pts[j];
                            if (isInCircle(q, c)) continue;
                            c = circleFromTwo(p, q);
                            for (let k = 0; k < j; k++) {
                                const rP = pts[k];
                                if (isInCircle(rP, c)) continue;
                                const circ = circleFromThree(p, q, rP);
                                if (circ) c = circ;
                            }
                        }
                    }
                    // Add visual radius R to fully enclose circles (centers + circle radius)
                    return { type: 'circle', x: c.x, y: c.y, r: c.r + R };
                }
                return null;
            }

            const bounding = computeBoundingShape();

            // 1. Calculate Bounding Box
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            circles.forEach(c => {
                if (c.x - R < minX) minX = c.x - R;
                if (c.x + R > maxX) maxX = c.x + R;
                if (c.y - R < minY) minY = c.y - R;
                if (c.y + R > maxY) maxY = c.y + R;
            });

            const width = maxX - minX;
            const height = maxY - minY;
            const side = Math.max(width, height);
            
            // Center the square relative to the circles
            const centerX = minX + width / 2;
            const centerY = minY + height / 2;
            const sqX = centerX - side / 2;
            const sqY = centerY - side / 2;

            // 2. Draw selected bounding shape
            ctx.strokeStyle = '#333';
            ctx.setLineDash([5, 5]);
            if (bounding) {
                if (bounding.type === 'square') {
                    ctx.strokeRect(bounding.x, bounding.y, bounding.side, bounding.side);
                } else if (bounding.type === 'circle') {
                    ctx.beginPath();
                    ctx.arc(bounding.x, bounding.y, bounding.r, 0, Math.PI * 2);
                    ctx.stroke();
                }
            }
            ctx.setLineDash([]);

            // 3. Draw Circles
            circles.forEach(c => {
                ctx.beginPath();
                ctx.arc(c.x, c.y, R, 0, Math.PI * 2);
                ctx.fillStyle = checkCollision(c) ? '#ff4d4d' : '#007bff';
                ctx.fill();
                ctx.strokeStyle = '#003d80';
                ctx.stroke();
            });

            if (bounding) {
                if (bounding.type === 'square') {
                    statsDisplay.innerText = `Placed: ${circles.length} | Remaining: ${remaining} | Square Side: ${(bounding.side / R).toFixed(2)} units`;
                } else if (bounding.type === 'circle') {
                    statsDisplay.innerText = `Placed: ${circles.length} | Remaining: ${remaining} | Radius: ${(bounding.r / R).toFixed(2)} units`;
                }
            } else {
                statsDisplay.innerText = `Placed: ${circles.length} | Remaining: ${remaining}`;
            }
        }

        function resetCanvas() {
            circles = [];
            updateScale();
            draw();
        }

        async function submitLayout() {
            const response = await fetch('/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ circles: circles })
            });
            if (!response.ok) {
                alert('Submit failed');
                return;
            }
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const disposition = response.headers.get('Content-Disposition') || '';
            let filename = 'layout.json';
            const m = /filename="?([^";]+)"?/.exec(disposition);
            if (m && m[1]) filename = m[1];
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            alert('Layout download started.');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT

@app.post("/submit")
async def submit(request: Request):
    data = await request.json()
    circles = data.get("circles", [])
    filename = f"layout_{int(time.time())}.json"
    content = json.dumps({"circles": circles}, indent=2)
    buf = BytesIO(content.encode("utf-8"))
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    print(f"Prepared download for layout with {len(circles)} circles as {filename}.")
    return StreamingResponse(buf, media_type="application/json", headers=headers)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

