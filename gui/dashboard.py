"""
D-RTOS: Dashboard View
Command center overview displaying real-time gauges, active process tracking,
system utilization logs, and live threat counts.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk

from gui.theme import Colors, Fonts, Styles

class DashboardView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        # Title
        lbl_title = tk.Label(self, text="📊 SYSTEM CONTROL DASHBOARD", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Upper Cards Panel (Threat Levels & Core metrics)
        self.upper_panel = tk.Frame(self, bg=Colors.BG_DEEP)
        self.upper_panel.pack(fill=tk.X, padx=15, pady=5)
        
        # Threat Gauge Card
        self.card_threat = tk.Frame(self.upper_panel, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.card_threat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        lbl_th_title = tk.Label(self.card_threat, text="SYSTEM DEFENSE THREAT LEVEL", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_th_title.pack(anchor="w", padx=10, pady=5)
        
        self.lbl_threat_val = tk.Label(self.card_threat, text="LOW", fg=Colors.RADAR_GREEN, bg=Colors.BG_PANEL, font=("Courier New", 28, "bold"))
        self.lbl_threat_val.pack(pady=10)
        
        # Object stats (Friendly, Unknown, Threats)
        self.lbl_obj_counts = tk.Label(self.card_threat, text="Friendly: 0  |  Unknown: 0  |  Threats: 0", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.LABEL_SM))
        self.lbl_obj_counts.pack(pady=5)
        
        # CPU Cores Card
        self.card_cpu = tk.Frame(self.upper_panel, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.card_cpu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        lbl_cpu_title = tk.Label(self.card_cpu, text="CPU CORE UTILIZATION", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_cpu_title.pack(anchor="w", padx=10, pady=5)
        
        self.cpu_bars = []
        for i in range(4):
            f = tk.Frame(self.card_cpu, bg=Colors.BG_PANEL)
            f.pack(fill=tk.X, padx=10, pady=2)
            lbl = tk.Label(f, text=f"CPU {i}:", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.LABEL_SM))
            lbl.pack(side=tk.LEFT)
            bar = ttk.Progressbar(f, length=120, mode='determinate')
            bar.pack(side=tk.LEFT, padx=10)
            val = tk.Label(f, text="0%", **Styles.label(fg=Colors.TEXT_PRIMARY, font=Fonts.MONO_SM))
            val.pack(side=tk.LEFT)
            self.cpu_bars.append((bar, val))
            
        # Memory & Process Counts Card
        self.card_mem = tk.Frame(self.upper_panel, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.card_mem.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        lbl_mem_title = tk.Label(self.card_mem, text="RAM & PROCESS LOAD", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_mem_title.pack(anchor="w", padx=10, pady=5)
        
        # Memory progress
        f_mem = tk.Frame(self.card_mem, bg=Colors.BG_PANEL)
        f_mem.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f_mem, text="RAM:", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.LABEL_MD)).pack(side=tk.LEFT)
        self.mem_bar = ttk.Progressbar(f_mem, length=120, mode='determinate')
        self.mem_bar.pack(side=tk.LEFT, padx=10)
        self.lbl_mem_val = tk.Label(f_mem, text="0%", **Styles.label(fg=Colors.TEXT_PRIMARY, font=Fonts.MONO_SM))
        self.lbl_mem_val.pack(side=tk.LEFT)
        
        # Process state metrics labels
        self.lbl_proc_states = tk.Label(self.card_mem, text="Active: 0 | Ready: 0 | Waiting: 0 | Running: 0",
                                        **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.LABEL_SM))
        self.lbl_proc_states.pack(pady=10)
        
        # Lower Section: critical process status and frequently used destinations
        self.lower_panel = tk.Frame(self, bg=Colors.BG_DEEP)
        self.lower_panel.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.card_active_proc = tk.Frame(self.lower_panel, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.card_active_proc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 8), pady=5)
        
        lbl_ap_title = tk.Label(self.card_active_proc, text="CURRENTLY EXECUTING CRITICAL PROCESS", **Styles.label(fg=Colors.ALERT_RED, font=Fonts.SUBHEADER))
        lbl_ap_title.pack(anchor="w", padx=15, pady=10)
        
        self.lbl_ap_details = tk.Label(self.card_active_proc, text="NO ACTIVE CRITICAL THREATS IN FLIGHT",
                                       **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_LG))
        self.lbl_ap_details.pack(pady=20)

        self.card_quick = tk.Frame(self.lower_panel, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER, width=250)
        self.card_quick.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 5), pady=5)
        self.card_quick.pack_propagate(False)
        tk.Label(self.card_quick, text="QUICK ACCESS", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.SUBHEADER)).pack(anchor="w", padx=14, pady=(14, 4))
        tk.Label(self.card_quick, text="Jump to a common workflow", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.LABEL_SM)).pack(anchor="w", padx=14, pady=(0, 10))

        shortcuts = [
            ("📡  Open Radar Scope", "Radar Simulation"),
            ("🎮  Run a Scenario", "Scenario Runner"),
            ("🎛️  Compare Schedulers", "CPU Scheduler"),
            ("📈  View Performance", "Performance"),
        ]
        for label, destination in shortcuts:
            tk.Button(
                self.card_quick, text=label, anchor="w",
                command=lambda name=destination: self.main_window.show_view(name),
                **Styles.button(bg=Colors.BG_INPUT, fg=Colors.TEXT_PRIMARY)
            ).pack(fill=tk.X, padx=12, pady=4)

        tk.Frame(self.card_quick, bg=Colors.BORDER, height=1).pack(fill=tk.X, padx=12, pady=(12, 8))
        tk.Label(self.card_quick, text="SIMULATION CLOCK", **Styles.label(fg=Colors.TEXT_DIM, font=Fonts.LABEL_SM)).pack(anchor="w", padx=14, pady=(0, 5))
        self.lbl_sim_time = tk.Label(self.card_quick, text="0.0 s", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.VALUE_LG))
        self.lbl_sim_time.pack(anchor="w", padx=14)
        self.lbl_tick = tk.Label(self.card_quick, text="TICK 0000", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_SM))
        self.lbl_tick.pack(anchor="w", padx=14, pady=(3, 10))
        
    def update_view(self):
        sim_time = self.main_window.multicore_mgr.simulation_time
        self.lbl_sim_time.configure(text=f"{sim_time:.1f} s")
        self.lbl_tick.configure(text=f"TICK {self.main_window.tick_counter:04d}")

        # 1. Update Threat Gauges
        counts = self.main_window.simulator.counts_by_threat()
        friendly = sum(1 for o in self.main_window.simulator.detected_objects if "Friendly" in o.object_type or "Weather" in o.object_type)
        unknown = sum(1 for o in self.main_window.simulator.detected_objects if "Unknown" in o.object_type or "Unidentified" in o.object_type)
        threats = counts.get("HIGH", 0) + counts.get("CRITICAL", 0)
        
        self.lbl_obj_counts.configure(text=f"Friendly: {friendly}  |  Unknown: {unknown}  |  Threats: {threats}")
        
        # Determine overall threat status
        if counts.get("CRITICAL", 0) > 0:
            self.lbl_threat_val.configure(text="CRITICAL", fg=Colors.ALERT_RED)
        elif counts.get("HIGH", 0) > 0:
            self.lbl_threat_val.configure(text="HIGH", fg=Colors.HIGH)
        elif counts.get("MEDIUM", 0) > 0:
            self.lbl_threat_val.configure(text="MEDIUM", fg=Colors.AMBER_WARN)
        else:
            self.lbl_threat_val.configure(text="LOW", fg=Colors.RADAR_GREEN)
            
        # 2. Update CPU Core utilization bars
        for idx, core in enumerate(self.main_window.multicore_mgr.cores):
            bar, val_lbl = self.cpu_bars[idx]
            util = core.utilization
            bar['value'] = util
            val_lbl.configure(text=f"{util:.1f}%")
            
        # 3. Update Memory Utilization bar
        mem_util = self.main_window.memory_mgr.utilization
        self.mem_bar['value'] = mem_util
        self.lbl_mem_val.configure(text=f"{mem_util:.1f}%")
        
        # 4. Update Process counters
        counts_proc = self.main_window.process_manager.counts()
        self.lbl_proc_states.configure(
            text=f"Active: {counts_proc.get('total', 0) - counts_proc.get('terminated', 0)} | "
                 f"Ready: {counts_proc.get('ready', 0)} | "
                 f"Waiting: {counts_proc.get('waiting', 0)} | "
                 f"Running: {counts_proc.get('running', 0)}"
        )
        
        # 5. Display high-priority active critical process details
        critical_procs = [p for p in self.main_window.process_manager.get_all_active() if p.priority == 1]
        if critical_procs:
            p = critical_procs[0]
            self.lbl_ap_details.configure(
                text=f"PID: {p.pid}  |  NAME: {p.process_name}  |  STATUS: {p.state.value}\n"
                     f"DEADLINE: {p.deadline:.1f}s  |  REMAINING: {p.remaining_burst:.1f}s  |  CORE: CPU-{p.assigned_cpu if p.assigned_cpu is not None else 'N/A'}",
                fg=Colors.ALERT_RED
            )
        else:
            self.lbl_ap_details.configure(
                text="NO ACTIVE CRITICAL THREATS IN FLIGHT",
                fg=Colors.TEXT_SECONDARY
            )
