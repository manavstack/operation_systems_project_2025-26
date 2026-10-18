"""
D-RTOS: Scenario Runner View
Guides the evaluator through Scenarios A to K and the main 8-Phase Demonstration sequence.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import time

from gui.theme import Colors, Fonts, Styles

class ScenarioView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self.current_phase = 1
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="🎮 ACADEMIC DEMONSTRATION & SCENARIO STEPPER", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Grid frame split into Scenario Stepper and Scenarios A-K list
        self.split_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left Panel: Main 8-Phase Demonstration Scenario
        self.phase_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.phase_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_p = tk.Label(self.phase_panel, text="Phase-by-Phase Interactive OS Walkthrough", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_p.pack(anchor="w", padx=10, pady=5)
        
        self.txt_phase_desc = tk.Text(self.phase_panel, **Styles.text_widget(), wrap=tk.WORD, height=12)
        self.txt_phase_desc.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        frm_step_btns = tk.Frame(self.phase_panel, bg=Colors.BG_PANEL)
        frm_step_btns.pack(fill=tk.X, padx=15, pady=10)
        
        self.btn_prev_phase = tk.Button(frm_step_btns, text="◀ Prev Phase", **Styles.button(), command=self._prev_phase)
        self.btn_prev_phase.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.btn_trigger_phase = tk.Button(frm_step_btns, text="🚀 Trigger Phase Actions", **Styles.success_button(), command=self._trigger_phase_action)
        self.btn_trigger_phase.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.btn_next_phase = tk.Button(frm_step_btns, text="Next Phase ▶", **Styles.button(), command=self._next_phase)
        self.btn_next_phase.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # Right Panel: Scenario A-K Batch Injector
        self.scen_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, width=440, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.scen_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.scen_panel.pack_propagate(False)
        
        lbl_s = tk.Label(self.scen_panel, text="Evaluator Test Scenarios (A - K)", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_s.pack(anchor="w", padx=10, pady=5)
        
        self.cb_scen = ttk.Combobox(self.scen_panel, values=[
            "Scenario A — Normal Traffic",
            "Scenario B — Multiple Threats",
            "Scenario C — CPU Overload",
            "Scenario D — Deadline Pressure",
            "Scenario E — Memory Shortage",
            "Scenario F — Resource Contention",
            "Scenario G — Circular Deadlock Cycle",
            "Scenario H — Safe Bankers Request",
            "Scenario I — Unsafe Bankers Request",
            "Scenario J — Competitor Buffer Sync",
            "Scenario K — CPU Core Imbalance"
        ], state="readonly")
        self.cb_scen.current(0)
        self.cb_scen.pack(fill=tk.X, padx=15, pady=15)
        
        btn_run_scen = tk.Button(self.scen_panel, text="⚡ Load & Inject Scenario", 
                                  **Styles.success_button(), command=self._run_scen_injection)
        btn_run_scen.pack(fill=tk.X, padx=20, pady=10)
        
        self.txt_scen_desc = tk.Text(self.scen_panel, **Styles.text_widget(), wrap=tk.WORD, height=10)
        self.txt_scen_desc.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.cb_scen.bind("<<ComboboxSelected>>", lambda e: self._update_scen_desc())
        
        self._update_phase_desc()
        self._update_scen_desc()
        
    def _update_phase_desc(self):
        phase_texts = {
            1: (
                "PHASE 1: Normal Flight Environment (Friendly target)\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "Generates a friendly radar sweep aircraft. The system classifies the target as LOW priority (priority 4), allocates memory using First/Best/Worst Fit, maps logical pages to frames, and starts simulation ticks.\n\n"
                "What to observe:\n"
                "1. Click 'Trigger Phase Actions'.\n"
                "2. Navigate to Dashboard -> Core HUD and RAM block allocations update.\n"
                "3. Navigate to Process Manager to view the LOW threat priority PCB."
            ),
            2: (
                "PHASE 2: Unknown Object detection (Medium priority)\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "An unknown aircraft target enters the airspace. System classifies the object as MEDIUM threat (priority 3) with a deadline parameters of 6.0 seconds.\n\n"
                "What to observe:\n"
                "1. Object enters READY state.\n"
                "2. The scheduler prepares CPU execution blocks."
            ),
            3: (
                "PHASE 3: Critical Threat Injection (Preemption Demonstration)\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "A Hostile Target is identified. It escalates to CRITICAL threat (Priority 1) with an urgent 3.0 second execution deadline.\n\n"
                "What to observe:\n"
                "1. Preemption occurs immediately.\n"
                "2. Check Preemption Log inside Process Manager. Preempted details with Context Switch logs are recorded."
            ),
            4: (
                "PHASE 4: Multi-Core execution load balancing\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "Multiple radar tracks appear concurrently, causing a load imbalance across the 4 CPU cores.\n\n"
                "What to observe:\n"
                "1. Navigate to Multi-Core view to check core utilization indicators.\n"
                "2. Click 'Trigger OS Load Balancer' to redistribute process allocations."
            ),
            5: (
                "PHASE 5: Shared Resource Buffer Race Condition demo\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "Multiple target processes write tracking parameters into the shared RADAR DATA BUFFER concurrently.\n\n"
                "What to observe:\n"
                "1. Switch to Synchronization view.\n"
                "2. Disable Sync to verify race condition buffer data corruptions.\n"
                "3. Enable Mutex/Semaphore to verify protected access."
            ),
            6: (
                "PHASE 6: Bankers Resource Safety Check\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "Resource manager requests allocations for running processes.\n\n"
                "What to observe:\n"
                "1. Navigate to Deadlock / Banker tab.\n"
                "2. Run Safety Sequence Check to verify deadlock-free execution paths."
            ),
            7: (
                "PHASE 7: Task Completion & Resource Reclamation\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "Process completes burst cycle execution, and terminates. OS reclaims RAM, page frame, and allocated system resource instances.\n\n"
                "What to observe:\n"
                "1. Process transitions to TERMINATED.\n"
                "2. Allocated block visualizers in Memory Manager revert to FREE."
            ),
            8: (
                "PHASE 8: Performance Analytics summary\n"
                "-----------------------------------------------------\n"
                "Description:\n"
                "Compile and store all scheduling logs into MongoDB database collections.\n\n"
                "What to observe:\n"
                "1. Switch to Performance tab to view comparative metrics horizontal/vertical bar charts."
            )
        }
        self.txt_phase_desc.config(state=tk.NORMAL)
        self.txt_phase_desc.delete("1.0", tk.END)
        self.txt_phase_desc.insert("1.0", phase_texts.get(self.current_phase, ""))
        self.txt_phase_desc.config(state=tk.DISABLED)
        
    def _update_scen_desc(self):
        scen_descs = {
            "A": "SCENARIO A: Normal traffic scan. Few friendly targets are detected. Low CPU Core utilization and memory load.",
            "B": "SCENARIO B: Multi-threat environment. Classifies several targets as HIGH or CRITICAL. Triggers deadline warning counts.",
            "C": "SCENARIO C: System load overload. Triggers processes queue overflow scenarios. Tests CPU scheduling policies metrics.",
            "D": "SCENARIO D: Tight deadline pressure. Targets trigger EDF nearest deadline scheduling priorities.",
            "E": "SCENARIO E: Physical memory shortage. Allocates several large memory segments to trigger First/Best/Worst allocation failures.",
            "F": "SCENARIO F: High resource contention. Multiple processes request shared GPU and Radar Processor hardware instances.",
            "G": "SCENARIO G: circular Resource Graph. Circular wait injected explicitly: P1 holds CPU requests GPU; P2 holds GPU requests Comm; P3 holds Comm requests CPU.",
            "H": "SCENARIO H: Safe Bankers request. Submits resource request vector. Evaluator runs safety check to see safe sequence path.",
            "I": "SCENARIO I: Unsafe Bankers request. Submits resource request exceeding bounds. Request is denied to avoid circular deadlock.",
            "J": "SCENARIO J: Concurrent lock competition. Simulates Mutex locking queuing and race condition data corruption on shared buffer.",
            "K": "SCENARIO K: Core load imbalance. Creates uneven workloads on CPU-0 and CPU-1. Demonstrates load migration balancer."
        }
        char = self.cb_scen.get().split()[1] # Gets 'A', 'B' etc
        self.txt_scen_desc.config(state=tk.NORMAL)
        self.txt_scen_desc.delete("1.0", tk.END)
        self.txt_scen_desc.insert("1.0", scen_descs.get(char, ""))
        self.txt_scen_desc.config(state=tk.DISABLED)
        
    def _prev_phase(self):
        if self.current_phase > 1:
            self.current_phase -= 1
            self._update_phase_desc()
            
    def _next_phase(self):
        if self.current_phase < 8:
            self.current_phase += 1
            self._update_phase_desc()
            
    def _trigger_phase_action(self):
        # Trigger object injections corresponding to phase
        objs = self.main_window.simulator.generate_phase(self.current_phase)
        
        # Sync with OS scheduler ready/running queue
        for obj in objs:
            pcb = self.main_window.process_manager.create_process(
                object_id=obj.object_id,
                threat_level=obj.threat_level,
                event_id=obj.event_id
            )
            # Log to DB
            self.main_window.db_service.save_radar_event(obj.to_dict())
            self.main_window.db_service.save_process(pcb.to_dict())
            
        self.main_window.process_manager.admit_all_new()
        self.main_window.show_feedback(f"Phase {self.current_phase} actions executed", "success")
        
        # Trigger custom actions per phase
        if self.current_phase == 3:
            # Preemption action: assign core 0 to high priority
            active = self.main_window.process_manager.get_all_active()
            critical = [p for p in active if p.priority == 1]
            running = self.main_window.multicore_mgr.cores[0].current_process
            if critical and running and running.priority > 1:
                self.main_window.process_manager.preempt_process(
                    running_pcb=running,
                    new_pcb=critical[0],
                    reason="Critical threat RAG check preemption",
                    cpu_id=0
                )
                self.main_window.multicore_mgr.cores[0].current_process = critical[0]
                
        elif self.current_phase == 5:
            # Load sync screen
            self.main_window.show_feedback("Synchronization walkthrough ready", "info")
            self.main_window.show_view("Synchronization")
            return
            
        elif self.current_phase == 6:
            # Setup Bankers demo state
            self.main_window.banker_algo.build_demo_state("drtos")
            self.main_window.show_feedback("Banker's safety demo loaded", "success")
            self.main_window.show_view("Deadlock / Banker")
            return
            
        elif self.current_phase == 8:
            # Run comparison of all algorithms and load performance page
            procs = self.main_window.process_manager.terminated
            if not procs:
                procs = list(self.main_window.process_manager.get_all_active())
            if procs:
                res = self.main_window.scheduler.run_all(procs)
                self.main_window.perf_mgr.record_all(res)
            self.main_window.show_feedback("Performance walkthrough ready", "success")
            self.main_window.show_view("Performance")
            return
            
        self.main_window.views["Dashboard"].update_view()
        messagebox.showinfo("Phase Stepper", f"Phase {self.current_phase} actions successfully executed.")
        
    def _run_scen_injection(self):
        char = self.cb_scen.get().split()[1] # Gets 'A', 'B' etc
        self.main_window.reset_simulation()
        
        # Generate scenario-specific blip objects
        objs = self.main_window.simulator.generate_scenario(char)
        
        # Admit to OS scheduler queues
        for obj in objs:
            pcb = self.main_window.process_manager.create_process(
                object_id=obj.object_id,
                threat_level=obj.threat_level,
                event_id=obj.event_id
            )
            self.main_window.db_service.save_radar_event(obj.to_dict())
            self.main_window.db_service.save_process(pcb.to_dict())
            
        self.main_window.process_manager.admit_all_new()
        
        # Navigate to appropriate view depending on Scenario character
        view_map = {
            "A": "Dashboard",
            "B": "Real-Time Scheduler",
            "C": "CPU Scheduler",
            "D": "Real-Time Scheduler",
            "E": "Memory Manager",
            "F": "Resource Manager",
            "G": "Deadlock / Banker",
            "H": "Deadlock / Banker",
            "I": "Deadlock / Banker",
            "J": "Synchronization",
            "K": "Multi-Core"
        }
        target_view = view_map.get(char, "Dashboard")
        
        if char == "G":
            self.main_window.deadlock_det.build_scenario("classic")
        elif char in ("H", "I"):
            self.main_window.banker_algo.build_demo_state("drtos" if char == "H" else "unsafe")
            
        self.main_window.show_view(target_view)
        self.main_window.show_feedback(f"Scenario {char} loaded · opened {target_view}", "success")
        messagebox.showinfo("Scenario Stepper", f"Scenario {char} injected. Navigating to {target_view} view.")
        
    def update_view(self):
        self._update_phase_desc()
        self._update_scen_desc()
