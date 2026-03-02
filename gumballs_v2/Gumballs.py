from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Global list to store submitted layouts (in memory for this example)
submitted_layouts = []

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
            
            if (circles.length === 0) {
                statsDisplay.innerText = `Placed: 0 | Remaining: ${remaining} | Square Side: 0.00 units`;
                return;
            }

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

            // 2. Draw Enclosing Square
            ctx.strokeStyle = '#333';
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(sqX, sqY, side, side);
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

            statsDisplay.innerText = `Placed: ${circles.length} | Remaining: ${remaining} | Square Side: ${(side/R).toFixed(2)} units`;
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
            const result = await response.json();
            alert("Layout submitted successfully!");
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT

@app.post("/submit")
async def submit(data: dict):
    # Here you can process or save the circle coordinates
    submitted_layouts.append(data["circles"])
    print(f"Received layout with {len(data['circles'])} circles.")
    return {"status": "success", "count": len(data["circles"])}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

