# Multi-Process Robot Simulation

A concurrent systems programming project that simulates a fleet of autonomous robots navigating a grid environment. The project implements a Master-Slave architecture where a central controller manages multiple robot processes using **Unix Pipes** and **Signals**.

## Key Features
* **Inter-Process Communication (IPC):** Uses anonymous pipes for real-time communication between the Master (Control Center) and the Robots.
* **Signal Handling:** Implements custom handlers for `SIGINT`, `SIGQUIT`, `SIGTSTP`, and `SIGALRM` to manage robot states (suspend, resume, battery reset).
* **Process Management:** Dynamically spawns robot instances using `os.fork()` and `os.execv()`.
* **Resource Management:** Simulates battery consumption and movement logic with collision detection.

## Architecture
* **`master.py`**: The Orchestrator. Reads configuration files, spawns child processes, maintains the global map state, and processes user commands.
* **`robots.py`**: The Agent. Represents an individual robot. Handles local navigation logic, battery decay, and sensor queries.
* **`sensor.py`**: The Interface. A helper class that parses the environment files (obstacles/treasures).

## Requirements
* **OS:** Linux / macOS / WSL (Windows Subsystem for Linux).
    * *Note: This project relies on Unix-specific libraries (`os.fork`, `signal`) and will not run natively on Windows Command Prompt.*
* **Language:** Python 3.x

## How to Run

1.  Clone the repository.
2.  Navigate to the project directory.
3.  Run the master script providing the room layout and the initial robot positions:

```bash
python3 src/master.py -room config/room.txt -robots config/robots.txt
```

## Supported Commands (Master Console)

Once the simulation is running, the Master process listens for standard input. You can control individual robots by their ID (1, 2, 3...) or the entire fleet using the `all` keyword.

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| **`mv`** | `<id> <direction>` | Moves a specific robot. Directions: `up`, `down`, `left`, `right`. | `mv 1 up` |
| **`mv`** | `all <direction>` | Moves **all** robots simultaneously in the same direction. Includes collision detection between robots. | `mv all right` |
| **`bat`** | `<id>` | Queries a robot via pipe for its current battery level. | `bat 2` |
| **`bat`** | `all` | Retrieves battery levels for the entire fleet. | `bat all` |
| **`pos`** | `<id>` | Queries a robot via pipe for its current coordinates. | `pos 1` |
| **`pos`** | `all` | Retrieves coordinates for the entire fleet. | `pos all` |
| **`suspend`** | `<id>` | Pauses a robot's execution (Sends `SIGINT`). The robot stops moving and consuming battery. | `suspend 1` |
| **`suspend`** | `all` | Suspends the entire fleet. | `suspend all` |
| **`resume`** | `<id>` | Resumes a suspended robot (Sends `SIGQUIT`). | `resume 1` |
| **`resume`** | `all` | Resumes the entire fleet. | `resume all` |
| **`exit`** | N/A | Gracefully terminates the Master and all Child processes. | `exit` |

### Signal Shortcuts
The Master process also handles specific system signals for global actions:
* **`Ctrl + Z` (SIGTSTP):** Prints the status (ID, Position, Battery) of all robots immediately.
* **`Ctrl + \` (SIGQUIT):** Replenishes the battery of **all** robots to 100%.

---

## Configuration Files

The system requires two text files to initialize the environment. Examples are provided in the `config/` folder.

### 1. Room Layout (`room.txt`)
Defines the grid size, obstacles, and treasures.
* **Line 1:** Grid Dimensions (`Rows` `Columns`).
* **Line 2:** Obstacles. Format: `Count (row,col) (row,col)...`
* **Line 3:** Treasures. Format: `Count (row,col) (row,col)...`

**Example:**
```text
6 10
3 (0,0) (1,2) (3,4)
2 (1,1) (2,3)
```
---
*Developed by Raphael García Zapata - Robotics Engineering Student at UC3M.*
