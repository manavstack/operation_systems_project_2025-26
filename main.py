"""
D-RTOS: Defense Radar Real-Time Operating System Simulator
Primary executable entrypoint initializing core engines and displaying GUI control dashboard.
"""

from __future__ import annotations
import tkinter as tk
import sys

from core.process_manager import ProcessManager
from core.scheduler import Scheduler
from core.realtime import RealTimeScheduler
from core.multicore import MultiCoreManager
from core.memory import MemoryManager
from core.paging import PagingManager
from core.resources import ResourceManager
from core.deadlock import DeadlockDetector
from core.banker import BankersAlgorithm
from core.synchronization import SynchronizationManager
from core.performance import PerformanceManager
from radar.simulator import RadarSimulator
from database.mongodb import MongoDBService
from gui.main_window import MainWindow

def main():
    # 1. Initialize OS Engines Layer (OS Layer 2)
    process_manager = ProcessManager()
    scheduler = Scheduler()
    realtime_sched = RealTimeScheduler()
    multicore_mgr = MultiCoreManager()
    memory_mgr = MemoryManager()
    paging_mgr = PagingManager()
    resource_mgr = ResourceManager()
    deadlock_det = DeadlockDetector()
    banker_algo = BankersAlgorithm()
    sync_mgr = SynchronizationManager()
    perf_mgr = PerformanceManager()
    
    # 2. Initialize Radar Simulation Layer (Layer 1)
    simulator = RadarSimulator()
    
    # 3. Initialize Presentation / Persistence Layer (Layer 3)
    db_service = MongoDBService()
    
    # Start Tkinter Window GUI loop
    root = tk.Tk()
    app = MainWindow(
        root=root,
        simulator=simulator,
        process_manager=process_manager,
        scheduler=scheduler,
        realtime_sched=realtime_sched,
        multicore_mgr=multicore_mgr,
        memory_mgr=memory_mgr,
        paging_mgr=paging_mgr,
        resource_mgr=resource_mgr,
        deadlock_det=deadlock_det,
        banker_algo=banker_algo,
        sync_mgr=sync_mgr,
        perf_mgr=perf_mgr,
        db_service=db_service
    )
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
