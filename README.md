# Multi-Process Robot Simulation 🤖

A concurrent systems programming project that simulates a fleet of autonomous robots navigating a grid environment. The project implements a Master-Slave architecture where a central controller manages multiple robot processes using **Unix Pipes** and **Signals**.

## 🚀 Key Features
* **Inter-Process Communication (IPC):** Uses anonymous pipes for real-time communication between the Master (Control Center) and the Robots.
* **Signal Handling:** Implements custom handlers for `SIGINT`, `SIGQUIT`, `SIGTSTP`, and `SIGALRM` to manage robot states (suspend, resume, battery reset).
* **Process Management:** Dynamically spawns robot instances using `os.fork()` and `os.execv()`.
* **Resource Management:** Simulates battery consumption and movement logic with collision detection.

## 🛠️ Architecture
* **`master.py`**: The Orchestrator. Reads configuration files, spawns child processes, maintains the global map state, and processes user commands.
* **`robots.py`**: The Agent. Represents an individual robot. Handles local navigation logic, battery decay, and sensor queries.
* **`sensor.py`**: The Interface. A helper class that parses the environment files (obstacles/treasures).

## 📋 Requirements
* **OS:** Linux / macOS / WSL (Windows Subsystem for Linux).
    * *Note: This project relies on Unix-specific libraries (`os.fork`, `signal`) and will not run natively on Windows Command Prompt.*
* **Language:** Python 3.x

## 🎮 How to Run

1.  Clone the repository.
2.  Navigate to the project directory.
3.  Run the master script providing the room layout and the initial robot positions:

```bash
python3 src/master.py -room config/room.txt -robots config/robots.txt
