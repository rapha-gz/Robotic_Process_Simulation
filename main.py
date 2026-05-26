import asyncio
import random
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Literal

# --- 1. DYNAMIC SHARED MEMORY ---
sim_state = {
    "grid": {"rows": 6, "cols": 10},
    "obstacles": [],
    "treasures": [],
    "robots": {}
}

def generate_random_environment(num_obs=6, num_treasures=5, num_robots=3):
    """Generates a random map ensuring no entities overlap."""
    rows = sim_state["grid"]["rows"]
    cols = sim_state["grid"]["cols"]
    
    all_coords = [[r, c] for r in range(rows) for c in range(cols)]
    random.shuffle(all_coords) 
    
    sim_state["obstacles"] = [all_coords.pop() for _ in range(num_obs)]
    sim_state["treasures"] = [all_coords.pop() for _ in range(num_treasures)]
    
    sim_state["robots"] = {}
    for i in range(1, num_robots + 1):
        sim_state["robots"][str(i)] = {
            "pos": all_coords.pop(),
            "battery": 100,
            "status": "active"
        }

# --- 2. BACKGROUND LOOP (Battery Drain) ---
async def battery_drain_loop():
    while True:
        await asyncio.sleep(1)
        for r_id, robot in sim_state["robots"].items():
            if robot["status"] == "active" and robot["battery"] > 0:
                robot["battery"] -= 1
                if robot["battery"] <= 0:
                    robot["battery"] = 0
                    robot["status"] = "dead"

@asynccontextmanager
async def lifespan(app: FastAPI):
    generate_random_environment() 
    drain_task = asyncio.create_task(battery_drain_loop())
    yield
    drain_task.cancel()

# --- 3. API INITIALIZATION ---
app = FastAPI(title="Dynamic Fleet API", lifespan=lifespan)

class MoveCommand(BaseModel):
    direction: Literal["up", "down", "left", "right"]

# --- 4. CORE LOGIC ---
def attempt_move(robot_id: str, direction: str) -> tuple[bool, str]:
    robot = sim_state["robots"][robot_id]
    
    if robot["status"] == "suspended": return False, "Robot suspended."
    if robot["status"] == "dead" or robot["battery"] < 5: return False, "Battery too low."

    r, c = robot["pos"]
    if direction == "up": r -= 1
    elif direction == "down": r += 1
    elif direction == "left": c -= 1
    elif direction == "right": c += 1
    target = [r, c]

    if not (0 <= r < sim_state["grid"]["rows"] and 0 <= c < sim_state["grid"]["cols"]):
        return False, "Wall collision."
    if target in sim_state["obstacles"]:
        return False, "Obstacle collision."
    for other_id, other_robot in sim_state["robots"].items():
        if other_id != robot_id and other_robot["pos"] == target:
            return False, f"Collision with Robot {other_id}."

    robot["pos"] = target
    robot["battery"] -= 5 

    if target in sim_state["treasures"]:
        sim_state["treasures"].remove(target)
        robot["battery"] = min(100, robot["battery"] + 50)
        return True, f"Moved {direction}. Collected Treasure! (+50 Bat)"

    return True, f"Moved {direction} successfully."

# --- 5. ENDPOINTS & DASHBOARD ---

@app.get("/map", tags=["Visual"], response_class=HTMLResponse)
def get_visual_map():
    """Generates a color-coded HTML map with an interactive JavaScript Control Panel."""
    grid_html = "<table>"
    for r in range(sim_state["grid"]["rows"]):
        grid_html += "<tr>"
        for c in range(sim_state["grid"]["cols"]):
            cell_pos = [r, c]
            cell_class = "empty"
            cell_text = ""
            
            if cell_pos in sim_state["obstacles"]:
                cell_class = "obstacle"
                cell_text = "X"
            elif cell_pos in sim_state["treasures"]:
                cell_class = "treasure"
                cell_text = "★"
            else:
                for r_id, robot in sim_state["robots"].items():
                    if robot["pos"] == cell_pos:
                        cell_class = "robot dead" if robot["status"] == "dead" else "robot"
                        cell_text = f"R{r_id}<br><span style='font-size:10px'>🔋{robot['battery']}</span>"
                        break 
                        
            grid_html += f"<td class='{cell_class}'>{cell_text}</td>"
        grid_html += "</tr>"
    grid_html += "</table>"

    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background-color: #1e1e1e; color: white; display: flex; flex-direction: column; align-items: center; }}
                h2 {{ color: #4da6ff; margin-bottom: 5px; }}
                .dashboard {{ display: flex; gap: 40px; margin-top: 20px; align-items: flex-start; }}
                
                table {{ border-collapse: collapse; box-shadow: 0 0 15px rgba(0,0,0,0.8); background-color: #2d2d2d; }}
                td {{ width: 65px; height: 65px; border: 1px solid #444; text-align: center; vertical-align: middle; font-weight: bold; font-size: 16px; transition: 0.2s; }}
                .empty {{ background-color: #2d2d2d; }}
                .obstacle {{ background-color: #ff4a4a; color: white; box-shadow: inset 0 0 10px rgba(0,0,0,0.5); }}
                .treasure {{ background-color: #ffd700; color: black; font-size: 28px; text-shadow: 0 0 5px rgba(255,255,255,0.8); }}
                .robot {{ background-color: #4da6ff; color: white; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }}
                .dead {{ background-color: #555; color: #aaa; text-decoration: line-through; }}
                
                .panel {{ background-color: #2a2a2a; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); min-width: 250px; text-align: center; }}
                select, button {{ width: 100%; padding: 10px; margin: 8px 0; border-radius: 5px; border: none; font-size: 14px; font-weight: bold; cursor: pointer; }}
                select {{ background-color: #444; color: white; }}
                button {{ background-color: #4da6ff; color: #1e1e1e; transition: 0.2s; }}
                button:hover {{ background-color: #79c0ff; }}
                .danger {{ background-color: #ff4a4a; color: white; }}
                .danger:hover {{ background-color: #ff7b7b; }}
                .warning {{ background-color: #ffd700; color: black; }}
                .warning:hover {{ background-color: #ffeb73; }}
                
                .dpad {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin: 15px 0; }}
                .dpad button {{ margin: 0; font-size: 18px; padding: 15px 0; }}
                .up {{ grid-column: 2; }}
                .left {{ grid-column: 1; }}
                .down {{ grid-column: 2; }}
                .right {{ grid-column: 3; }}
            </style>
        </head>
        <body>
            <h2>🏭 Master Control Center</h2>
            <p>Fleet API is Online. Passive battery drain is active.</p>
            
            <div class="dashboard">
                <div>{grid_html}</div>
                
                <div class="panel">
                    <h3>Target Selector</h3>
                    <select id="targetSelect">
                        <option value="fleet">All Robots (Fleet)</option>
                        <option value="1">Robot 1</option>
                        <option value="2">Robot 2</option>
                        <option value="3">Robot 3</option>
                    </select>

                    <div class="dpad">
                        <button class="up" onclick="move('up')">▲</button>
                        <button class="left" onclick="move('left')">◀</button>
                        <button class="down" onclick="move('down')">▼</button>
                        <button class="right" onclick="move('right')">▶</button>
                    </div>

                    <hr style="border-color: #444; margin: 20px 0;">
                    
                    <button class="warning" onclick="sendSignal('suspend')">⏸️ Suspend Target</button>
                    <button class="warning" onclick="sendSignal('resume')">▶️ Resume Target</button>
                    <button onclick="apiCall('/fleet/recharge', 'POST')">⚡ Global Recharge</button>
                    <button class="danger" onclick="apiCall('/system/randomize', 'POST')">🎲 Randomize Factory</button>
                </div>
            </div>

            <script>
                setInterval(() => window.location.reload(), 2000);

                async function apiCall(endpoint, method, body = null) {{
                    try {{
                        const options = {{ method: method, headers: {{'Content-Type': 'application/json'}} }};
                        if (body) options.body = JSON.stringify(body);
                        
                        const response = await fetch(endpoint, options);
                        const data = await response.json();
                        
                        if (!response.ok) {{
                            alert("⚠️ Error: " + data.detail);
                        }} else {{
                            window.location.reload(); 
                        }}
                    }} catch (error) {{
                        console.error("API Error:", error);
                    }}
                }}

                function move(direction) {{
                    const target = document.getElementById("targetSelect").value;
                    const endpoint = target === "fleet" ? "/fleet/move" : `/robot/${{target}}/move`;
                    apiCall(endpoint, "POST", {{ direction: direction }});
                }}

                function sendSignal(action) {{
                    const target = document.getElementById("targetSelect").value;
                    if (target === "fleet") {{
                        alert("For safety, Suspend/Resume must be done per robot in this UI.");
                        return;
                    }}
                    apiCall(`/robot/${{target}}/${{action}}`, "POST");
                }}
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/system/randomize", tags=["Environment"])
def randomize_map():
    generate_random_environment(num_obs=6, num_treasures=5, num_robots=3)
    return {"message": "New random environment generated!", "state": sim_state}

@app.post("/fleet/move", tags=["Movement"])
def move_entire_fleet(command: MoveCommand):
    results = {r_id: attempt_move(r_id, command.direction)[1] for r_id in sim_state["robots"]}
    return {"command": command.direction, "details": results}

@app.post("/robot/{robot_id}/move", tags=["Movement"])
def move_single_robot(robot_id: str, command: MoveCommand):
    if robot_id not in sim_state["robots"]: raise HTTPException(404, "Robot not found.")
    success, msg = attempt_move(robot_id, command.direction)
    if not success: raise HTTPException(400, msg)
    return {"message": msg, "state": sim_state["robots"][robot_id]}

@app.post("/robot/{robot_id}/suspend", tags=["Signals"])
def suspend_robot(robot_id: str):
    if robot_id not in sim_state["robots"]: raise HTTPException(404, "Robot not found.")
    sim_state["robots"][robot_id]["status"] = "suspended"
    return {"message": f"Robot {robot_id} suspended."}

@app.post("/robot/{robot_id}/resume", tags=["Signals"])
def resume_robot(robot_id: str):
    if robot_id not in sim_state["robots"]: raise HTTPException(404, "Robot not found.")
    sim_state["robots"][robot_id]["status"] = "active"
    return {"message": f"Robot {robot_id} resumed."}

@app.post("/fleet/recharge", tags=["Signals"])
def recharge_fleet():
    for robot in sim_state["robots"].values():
        robot["battery"] = 100
        if robot["status"] == "dead": robot["status"] = "active"
    return {"message": "All batteries replenished."}