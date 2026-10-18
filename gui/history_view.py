"""
D-RTOS: History View
Displays simulation session history records retrieved from MongoDB.
Allows comparing historical metrics across sessions.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from gui.theme import Colors, Fonts, Styles

class HistoryView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="📜 HISTORICAL SIMULATION RECORD ARCHIVE", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Table container
        self.table_frame = tk.Frame(self, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        lbl_h = tk.Label(self.table_frame, text="Persistent DB Simulation Sessions History", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_h.pack(anchor="w", padx=10, pady=5)
        
        self.tree_hist = ttk.Treeview(self.table_frame, columns=("sid", "start", "end", "radar", "processes", "status"), 
                                      show="headings", style="Custom.Treeview")
        self.tree_hist.heading("sid", text="Session ID")
        self.tree_hist.heading("start", text="Start Time")
        self.tree_hist.heading("end", text="End Time")
        self.tree_hist.heading("radar", text="Radar Events")
        self.tree_hist.heading("processes", text="Processes Run")
        self.tree_hist.heading("status", text="Session Status")
        
        for col in ("sid", "start", "end", "radar", "processes", "status"):
            self.tree_hist.column(col, width=150, anchor="center")
            
        scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree_hist.yview)
        xscroll = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree_hist.xview)
        self.tree_hist.configure(yscrollcommand=scroll.set, xscrollcommand=xscroll.set)
        
        self.tree_hist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0,10))
        xscroll.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 8))
        self.empty_table = Styles.empty_state(
            self.table_frame,
            "No saved sessions found.\nRun a simulation, then refresh the history."
        )
        Styles.prepare_tree(self.tree_hist)
        
        # Compare selection action buttons
        self.btn_refresh = tk.Button(self, text="🔄 Refresh Database Log", 
                                     **Styles.button(), command=self.update_view)
        self.btn_refresh.pack(side=tk.LEFT, padx=15, pady=15)
        
        self.btn_load_hist = tk.Button(self, text="📂 Load Selected Session Data", 
                                       **Styles.success_button(), command=self._load_session_data)
        self.btn_load_hist.pack(side=tk.LEFT, padx=5, pady=15)
        
    def _load_session_data(self):
        sel = self.tree_hist.selection()
        if not sel:
            messagebox.showwarning("Session Browser", "Select a historical session row from the tree view table.")
            return
            
        vals = self.tree_hist.item(sel[0], "values")
        session_id = vals[0]
        
        # Load historical processes list
        procs = self.main_window.db_service.get_processes(session_id)
        metrics = self.main_window.db_service.get_system_metrics(session_id)
        
        msg = (
            f"HISTORICAL METRICS: {session_id}\n"
            f"---------------------------------\n"
            f"Total Processes Tracked: {len(procs)}\n"
            f"Total Status Log Snaps : {len(metrics)}\n\n"
        )
        if metrics:
            last = metrics[-1]
            msg += (
                f"Peak CPU Load Util   : {last.get('cpu_utilization', 0.0):.1f}%\n"
                f"Memory Utilized      : {last.get('memory_utilization', 0.0):.1f}%\n"
                f"Deadline Success Rate: {last.get('deadline_success_rate', 100.0):.1f}%\n"
                f"Context Switches     : {last.get('context_switches', 0)}\n"
                f"Page Faults          : {last.get('page_faults', 0)}\n"
            )
        messagebox.showinfo("Session Stats Summary", msg)
        self.main_window.show_feedback(f"Loaded summary for session {session_id}", "info")
        
    def update_view(self):
        self.tree_hist.delete(*self.tree_hist.get_children())
        history = self.main_window.db_service.get_session_history()
        for index, h in enumerate(history):
            status = h.get("status", "ACTIVE").upper()
            tags = [status]
            if index % 2:
                tags.insert(0, "alternate")
            self.tree_hist.insert("", "end", values=(
                h.get("session_id", "?"),
                h.get("start_datetime", "?")[:19].replace("T", " "),
                h.get("end_datetime", "Active Session")[:19].replace("T", " "),
                h.get("radar_events", 0),
                h.get("processes", 0),
                status
            ), tags=tuple(tags))
        Styles.update_empty_state(self.tree_hist, self.empty_table)
