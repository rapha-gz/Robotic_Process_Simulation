# Multi-Process Robot Simulation & Fleet API

A two-phase concurrent systems project that takes the **same robot fleet domain** and implements it twice, first against the bare metal of the Operating System using Unix IPC, then modernized into a cross-platform Cloud API with a live dashboard. The point isn't the simulation; it's the architectural translation between two paradigms.

**Technical surface:** `os.fork` · `os.execv` · anonymous pipes · `SIGINT` / `SIGQUIT` / `SIGTSTP` / `SIGALRM` · `FastAPI` · `asyncio` · `uvicorn` · procedural map generation · interactive HTML/JS dashboard.

This project is divided into two major architectural phases, demonstrating both low-level Operating System mechanics and high-level Cloud/Web deployment:

1. **Phase 1: Local System Simulation**: A Master–Slave architecture using low-level **Unix Pipes** and **Signals**.
2. **Phase 2: Cloud API Expansion**: A modernized, highly-concurrent web interface using **FastAPI** and an interactive HTML/JS Dashboard.

---

## PHASE 1: Local OS-Level Simulation

The foundation of the project. A central controller (`master.py`) manages multiple independent robot processes (`robots.py`) using strictly local Inter-Process Communication (IPC).

### Key Features

* **Inter-Process Communication (IPC):** Anonymous pipes for real-time communication between the Master (Control Center) and the Robots.
* **Signal Handling:** Custom handlers for `SIGINT`, `SIGQUIT`, `SIGTSTP`, and `SIGALRM` to manage robot states (suspend, resume, battery reset, periodic drain).
* **Process Management:** Dynamically spawns robot instances using `os.fork()` and `os.execv()`.
* **Resource Management:** Simulates battery consumption and movement logic with collision detection.

### Architecture

* **`master.py`**: *The Orchestrator.* Reads configuration files, spawns child processes, maintains the global map state, and processes user commands.
* **`robots.py`**: *The Agent.* Represents an individual robot. Handles local navigation logic, battery decay, and sensor queries.
* **`sensor.py`**: *The Interface.* A helper class that parses the environment files (obstacles, treasures).

### Requirements

* **OS:** Linux / macOS / WSL (Windows Subsystem for Linux).
  * *This phase relies on Unix-specific primitives (`os.fork`, `signal`) and will not run natively on Windows Command Prompt.*
* **Language:** Python 3.x (no third-party dependencies — Phase 1 is standard library only).

### How to Run

From the project root, providing the room layout and the initial robot positions:

```bash
python3 src/master.py -room config/room.txt -robots config/robots.txt
```

### Supported Commands (Master Console)

Once the simulation is running, the Master process listens for standard input. You can control individual robots by their ID (1, 2, 3...) or the entire fleet using the `all` keyword.

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| **`mv`** | `<id> <direction>` | Moves a specific robot. Directions: `up`, `down`, `left`, `right`. | `mv 1 up` |
| **`mv`** | `all <direction>` | Moves **all** robots simultaneously. Includes collision detection. | `mv all right` |
| **`bat`** | `<id>` | Queries a robot via pipe for its current battery level. | `bat 2` |
| **`bat`** | `all` | Retrieves battery levels for the entire fleet. | `bat all` |
| **`pos`** | `<id>` | Queries a robot via pipe for its current coordinates. | `pos 1` |
| **`pos`** | `all` | Retrieves coordinates for the entire fleet. | `pos all` |
| **`suspend`** | `<id>` | Pauses a robot (sends `SIGINT`). Stops moving and consuming battery. | `suspend 1` |
| **`suspend`** | `all` | Suspends the entire fleet. | `suspend all` |
| **`resume`** | `<id>` | Resumes a suspended robot (sends `SIGQUIT`). | `resume 1` |
| **`resume`** | `all` | Resumes the entire fleet. | `resume all` |
| **`exit`** | N/A | Gracefully terminates the Master and all child processes. | `exit` |

#### Signal Shortcuts

The Master process also handles specific system signals for global actions:

* **`Ctrl + Z`** (`SIGTSTP`): Prints the status (ID, position, battery) of all robots immediately.
* **`Ctrl + \`** (`SIGQUIT`): Replenishes the battery of **all** robots to 100%.

### Configuration Files

The system requires two text files to initialize the environment. Examples are provided in the `config/` folder.

#### 1. Room Layout (`room.txt`)

Defines the grid size, obstacles, and treasures.

* **Line 1:** Grid dimensions (`Rows` `Columns`).
* **Line 2:** Obstacles. Format: `Count (row,col) (row,col)...`
* **Line 3:** Treasures. Format: `Count (row,col) (row,col)...`

**Example:**

```text
6 10
3 (0,0) (1,2) (3,4)
2 (1,1) (2,3)
```

#### 2. Robot Manifest (`robots.txt`)

Defines the initial spawn coordinates for the robot fleet. Each line represents one robot instance.

**Example:**

```text
(2,3)
(1,4)
(1,5)
```

*(Spawns 3 robots. Robot 1 starts at (2,3), Robot 2 at (1,4), Robot 3 at (1,5).)*

---

## PHASE 2: Cloud API & Interactive Dashboard

A modernized Web API (`main.py`) that replaces local Unix Pipes with HTTP requests, making the simulation cross-platform and accessible over a network with an interactive frontend. Same domain logic, completely different architecture.

### API Upgrades

* **Asynchronous Background Tasks:** `asyncio` runs a non-blocking passive battery drain loop (1% per second) parallel to the web server, replacing the `SIGALRM`-based timer from Phase 1.
* **Procedural Environment Generation:** Dynamically spawns unique, non-overlapping layouts of obstacles, single-use treasures, and robots on command.
* **Live Interactive Dashboard:** An embedded HTML/JS frontend that visualizes the factory grid, entity positions, and battery levels in real time.

### API Setup & Execution

Unlike Phase 1, the API is entirely cross-platform and **will run on Windows natively**.

1. Install the required web server libraries:

   ```bash
   pip install fastapi "uvicorn[standard]"
   ```

2. Start the application server:

   ```bash
   python -m uvicorn main:app --reload
   ```

### Accessing the Interfaces

* **🕹️ Live Dashboard:** [http://127.0.0.1:8000/map](http://127.0.0.1:8000/map) — view the factory floor and use the visual control panel.
* **📖 API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — interactive Swagger UI for testing raw JSON endpoints.

### Core API Endpoints

| Endpoint | Method | Description | Equivalent Legacy Command |
| :--- | :--- | :--- | :--- |
| `/map` | `GET` | Returns the interactive HTML Web Dashboard. | `print_room()` |
| `/system/randomize` | `POST` | Wipes the board and generates a new random map. | *N/A (new feature)* |
| `/fleet/move` | `POST` | Moves all active robots simultaneously. | `mv all <dir>` |
| `/robot/{id}/move` | `POST` | Moves a specific robot (`up`, `down`, `left`, `right`). | `mv <id> <dir>` |
| `/robot/{id}/suspend` | `POST` | Pauses a robot, halting battery drain and movement. | `suspend <id>` (`SIGINT`) |
| `/robot/{id}/resume` | `POST` | Reactivates a suspended robot. | `resume <id>` (`SIGQUIT`) |
| `/fleet/recharge` | `POST` | Restores all robots to 100% battery. | `Ctrl + \` |

---

## Project Status

**Status:** Complete (v2.0).

This repository represents the finished two-phase exploration of the same domain across two paradigms — Unix IPC and a modern async web stack. A planned **v3** (industrial data layer: MQTT, time-series storage, observability, cloud deployment) was planned and then forked into a separate project, where the same infrastructure patterns are applied to a domain better aligned with my target roles in industrial digital operations:

 **[ev-csms-platform](#)** , an OCPP 2.0.1 Charging Station Management System with the full digital-operations stack around it.(https://github.com/rapha-gz/ev-csms-platform)

---

*Developed by Raphael García Zapata — Robotics Engineering Student at UC3M.*
