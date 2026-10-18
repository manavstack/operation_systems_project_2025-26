"""
D-RTOS: Real-Time Scheduler View
Live monitor displaying deadline countdown metrics, warning alerts, and success rates.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk

from gui.theme import Colors, Fonts, Styles

class RealTimeView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="⏰ REAL-TIME MISSION DEADLINE MONITOR", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Summary metrics panel
        self.summary_panel = tk.Frame(self, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.summary_panel.pack(fill=tk.X, padx=15, pady=5)
        
        # Total deadlines
        f_tot = tk.Frame(self.summary_panel, bg=Colors.BG_PANEL)
        f_tot.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(f_tot, text="TOTAL DEADLINES LOGGED", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.TITLE)).pack()
        self.lbl_total_dl = tk.Label(f_tot, text="0", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.VALUE_LG))
        self.lbl_total_dl.pack()
        
        # Deadlines met
        f_met = tk.Frame(self.summary_panel, bg=Colors.BG_PANEL)
        f_met.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(f_met, text="DEADLINES MET", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.TITLE)).pack()
        self.lbl_met_dl = tk.Label(f_met, text="0", **Styles.label(fg=Colors.RADAR_GREEN, font=Fonts.VALUE_LG))
        self.lbl_met_dl.pack()
        
        # Deadlines missed
        f_miss = tk.Frame(self.summary_panel, bg=Colors.BG_PANEL)
        f_miss.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(f_miss, text="DEADLINES MISSED", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.TITLE)).pack()
        self.lbl_miss_dl = tk.Label(f_miss, text="0", **Styles.label(fg=Colors.ALERT_RED, font=Fonts.VALUE_LG))
        self.lbl_miss_dl.pack()
        
        # Success Rate
        f_rate = tk.Frame(self.summary_panel, bg=Colors.BG_PANEL)
        f_rate.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(f_rate, text="DEADLINE SUCCESS RATE", **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.TITLE)).pack()
        self.lbl_success_rate = tk.Label(f_rate, text="100.0%", **Styles.label(fg=Colors.RADAR_GREEN, font=Fonts.VALUE_LG))
        self.lbl_success_rate.pack()
        
        # Real-time process deadline table
        self.table_frame = tk.Frame(self, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        lbl_tbl = tk.Label(self.table_frame, text="Active Task Countdown Monitor (EDF Ordering)", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_tbl.pack(anchor="w", padx=10, pady=5)
        
        self.tree = ttk.Treeview(self.table_frame, columns=("pid", "priority", "deadline", "remaining", "status"), 
                                 show="headings", style="Custom.Treeview")
        self.tree.heading("pid", text="PID")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("deadline", text="Absolute Deadline (s)")
        self.tree.heading("remaining", text="Remaining Time to DL (s)")
        self.tree.heading("status", text="Warning Status")
        
        for col in ("pid", "priority", "deadline", "remaining", "status"):
            self.tree.column(col, width=150, anchor="center")
            
        scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll.set, xscrollcommand=xscroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0,10))
        xscroll.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 8))
        self.empty_table = Styles.empty_state(
            self.table_frame,
            "No active deadline-bound tasks.\nInject a target to start monitoring."
        )
        Styles.prepare_tree(self.tree)
        
    def update_view(self):
        # Update summary counters
        stats = self.main_window.realtime_sched.stats()
        self.lbl_total_dl.configure(text=str(stats.get("total_deadlines", 0)))
        self.lbl_met_dl.configure(text=str(stats.get("deadlines_met", 0)))
        self.lbl_miss_dl.configure(text=str(stats.get("deadlines_missed", 0)))
        self.lbl_success_rate.configure(text=f"{stats.get('success_rate', 100.0):.1f}%")
        
        # Color rating based on success rate
        rate = stats.get('success_rate', 100.0)
        if rate >= 90:
            self.lbl_success_rate.configure(fg=Colors.RADAR_GREEN)
        elif rate >= 75:
            self.lbl_success_rate.configure(fg=Colors.AMBER_WARN)
        else:
            self.lbl_success_rate.configure(fg=Colors.ALERT_RED)
            
        # Update live task list
        self.tree.delete(*self.tree.get_children())
        records = self.main_window.realtime_sched.get_records()
        visible = 0
        for r in records:
            # Only display active ready/running processes
            if r.state in ("READY", "RUNNING"):
                tags = [r.status.upper()]
                if visible % 2:
                    tags.insert(0, "alternate")
                self.tree.insert("", "end", values=(
                    r.pid, r.priority, f"{r.deadline:.1f}",
                    f"{r.time_to_deadline:.1f}s", r.status
                ), tags=tuple(tags))
                visible += 1
        Styles.update_empty_state(self.tree, self.empty_table)
