# D-RTOS — Defense Radar Real-Time Operating System Simulator

An educational **40-mark Operating Systems academic project** simulating a real-time defense radar operating system. It implements and visualizes process management, CPU scheduling, preemptive real-time task control, multi-core load balancing, page-replacement virtual memory, multi-instance resource management, deadlock avoidance via Banker's algorithm, and process synchronization primitives.

---

## 🛡️ Project Overview

**D-RTOS** is a simulated real-time Defense Radar Operating System that converts radar events into OS processes and dynamically manages their execution.

```text
Radar Event
     ↓
Threat Classification
     ↓
Process Creation
     ↓
PCB Creation
     ↓
Priority + Deadline Assignment
     ↓
Resource Requirement
     ↓
CPU Scheduling
     ↓
Multi-Core Execution
     ↓
Memory Management
     ↓
Synchronization
     ↓
Deadlock / Banker Safety Check
     ↓
Process Execution
     ↓
Deadline Monitoring
     ↓
Process Completion
     ↓
Performance Analysis
     ↓
MongoDB Storage
```

---

## 🛠️ Key OS Features Implemented

### 1. Process & PCB Manager
- **Process Control Blocks (PCB)** containing detailed metrics: PID, arrival/burst/remaining time, priority, threat level, deadlines, logical page mapping, and resource footprints.
- **Process States** transition flow: `NEW` ➔ `READY` ➔ `RUNNING` ➔ `WAITING` ➔ `TERMINATED`.

### 2. CPU Scheduling Policies
1. **FCFS** (First-Come, First-Served)
2. **SJF** (Shortest Job First - Non-preemptive)
3. **Priority Scheduling** (Non-preemptive)
4. **Round Robin** (Time-sliced execution with customizable quantum)
5. **Preemptive Priority** (Dynamic preemption of lower priority jobs)
6. **SRTF** (Shortest Remaining Time First)
7. **Multilevel Queue (MLQ)** (Critical Priority queue: Preemptive, Interactive: RR, Routine: FCFS)
8. **EDF** (Earliest Deadline First)

### 3. Memory & Virtual Memory (Paging)
- **Contiguous Allocation**: First Fit, Best Fit, and Worst Fit partition selection.
- **Paging Manager**: Maps logical addresses to physical frames (32 MB page blocks).
- **Page Replacement**: Simulates and compares **FIFO** and **LRU** fault rates on page reference strings.

### 4. Multi-Core HUD & Balancer
- Simulates **4 CPU Cores** (`CPU-0` to `CPU-3`) running concurrently.
- Implements an **OS Load Balancer** migrating ready tasks from overloaded cores to underloaded cores.

### 5. Deadlock Detection & Avoidance
- **Resource Allocation Graph (RAG)**: Cycle scanning using DFS detection.
- **Banker's Algorithm**: Safely evaluates multi-instance allocations and returns the `Safe Sequence` chain.

### 6. Process Synchronization (No IPC)
- Simulates a protected **Radar Data Buffer** with **Mutex** and **Counting Semaphore** primitives.
- Demonstrates a controlled **Race Condition** causing buffer corruption when synchronization is deactivated.

### 7. MongoDB Persistence Layer
- Isolates MongoDB queries behind a dedicated `MongoDBService` service layer.
- Implements an **In-Memory fallback database** if MongoDB is offline, guaranteeing 100% crash-free offline execution.

---

## 📁 Directory Structure

```text
D-RTOS/
│
├── main.py                     # Entry point
├── requirements.txt            # Dependency files
├── core/                       # OS Simulation Engine Layer
│   ├── process.py              # Process enums and profile configs
│   ├── pcb.py                  # PCB Class definition
│   ├── process_manager.py      # Transitions and queues manager
│   ├── scheduler.py            # FCFS, SJF, Priority, RR, PP, SRTF, MLQ
│   ├── realtime.py             # EDF and Deadline monitor metrics
│   ├── multicore.py            # CPU 0-3 management and balancing
│   ├── memory.py               # Contiguous Fit allocation block maps
│   ├── paging.py               # Pages translation and FIFO/LRU tests
│   ├── resources.py            # Resource allocation request managers
│   ├── deadlock.py             # RAG graph cycle DFS checks
│   ├── banker.py               # Banker's safety state matrix calculations
│   ├── synchronization.py      # Mutex, Semaphores and Radar Buffers
│   └── performance.py          # Metric snapshots and aggregations
│
├── radar/                      # Fictional Simulation Layer
│   ├── simulator.py            # Object sweep generators
│   └── classifier.py           # Threat level mapping
│
├── database/                   # Database Persistence
│   └── mongodb.py              # Service layer with collections management
│
├── gui/                        # presentation views (Tkinter & Matplotlib)
│   ├── theme.py                # Command center tactical styles
│   ├── main_window.py          # Navigation layout container
│   ├── dashboard.py            # System metrics overview
│   ├── radar_view.py           # PPI sweep and blips canvas
│   ├── process_view.py         # Process lists and PCB inspector
│   ├── scheduler_view.py       # Gantt canvas and metrics comparer
│   ├── realtime_view.py        # Deadline gauge tables
│   ├── multicore_view.py       # Core load progress HUD
│   ├── memory_view.py          # Physical RAM address partition graphs
│   ├── paging_view.py          # Logical translator and replacement stepper
│   ├── resource_view.py        # Allocators list and slider forms
│   ├── deadlock_view.py        # Deadlock cycle paths list and Bankers safety sequence
│   ├── synchronization_view.py # Mutex locks and Race Condition demo
│   ├── analytics_view.py       # Matplotlib bar charts comparing schedules
│   ├── history_view.py         # History sessions browser
│   ├── scenario_view.py        # 8-Phase walkthrough runner
│   └── settings_view.py        # DB Connection URI configuration
│
└── tests/                      # Verification Tests Suite
```

---

## 🚀 Getting Started

### 📋 Prerequisites
- **Python 3.8+**
- **Tkinter** (usually comes default with Python installations. On Linux: `sudo apt-get install python3-tk`)
- **MongoDB Community Server** (Optional: D-RTOS uses an in-memory database mock if MongoDB is not running)

### 📥 Installation & Setup
1. Clone this repository to your computer workspace directory.
2. Install required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the complete test suite:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py" -v
   ```
4. Start the D-RTOS Simulator Dashboard:
   ```bash
   python3 main.py
   ```

---

## 🎮 Walkthrough Scenarios for Academic Evaluation

D-RTOS includes a built-in **Scenario Stepper** panel. Evaluators can load preset test cases:
- **Scenario A**: Normal traffic logs (few tasks, low core utilization).
- **Scenario G**: circular Resource Graph. Circular wait injected explicitly: P1 holds CPU requests GPU; P2 holds GPU requests Comm; P3 holds Comm requests CPU.
- **Scenario J**: Concurrent lock competition. Simulates Mutex locking queuing and race condition data corruption on shared buffer.
- **8-Phase Interactive OS Walkthrough**: Step through the core loop of Process Creation, Scheduling, Preemption, Load Balancing, and Analytics step-by-step.
