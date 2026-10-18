"""
D-RTOS: CPU Scheduler View
Algorithm execution controller showing Gantt charts, preemption events, and performance tables.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import Colors, Fonts, Styles

class SchedulerView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="🎛️ CPU SCHEDULING CONTROL STATION", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Main Grid Layout
        self.top_controls = tk.Frame(self, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.top_controls.pack(fill=tk.X, padx=15, pady=5)
        
        # Left controls
        tk.Label(self.top_controls, text="Select Scheduling Policy:", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(side=tk.LEFT, padx=10, pady=10)
        self.cb_algo = ttk.Combobox(self.top_controls, values=[
            "FCFS", "SJF", "Priority", "Round Robin", "Preemptive Priority", "SRTF", "Multilevel Queue", "EDF"
        ], state="readonly")
        self.cb_algo.current(0)
        self.cb_algo.pack(side=tk.LEFT, padx=5, pady=10)
        
        self.lbl_q = tk.Label(self.top_controls, text="Quantum (RR):", **Styles.label(fg=Colors.TEXT_SECONDARY))
        self.lbl_q.pack(side=tk.LEFT, padx=10)
        self.ent_q = tk.Entry(self.top_controls, width=5, **Styles.entry())
        self.ent_q.insert(0, "2.0")
        self.ent_q.pack(side=tk.LEFT, padx=5)
        
        # Action Buttons
        self.btn_run = tk.Button(self.top_controls, text="▶ Run Scheduler", **Styles.success_button(), command=self._run_scheduler)
        self.btn_run.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Gantt Chart Panel
        self.gantt_frame = tk.Frame(self, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.gantt_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        lbl_g = tk.Label(self.gantt_frame, text="Execution Gantt Chart (Simulation Timeline)", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_g.pack(anchor="w", padx=10, pady=5)
        
        self.gantt_canvas = tk.Canvas(self.gantt_frame, bg=Colors.BG_DEEP, height=180, highlightthickness=0)
        self.gantt_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.gantt_canvas.create_text(400, 90, text="Run a scheduler to see the execution timeline.",
                                      fill=Colors.TEXT_SECONDARY, font=Fonts.LABEL_MD,
                                      tags="empty")
        
        # Metrics Table Panel
        self.metrics_frame = tk.Frame(self, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.metrics_frame.pack(fill=tk.X, padx=15, pady=5)
        
        lbl_m = tk.Label(self.metrics_frame, text="Performance Evaluation Summary", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_m.pack(anchor="w", padx=10, pady=5)
        
        self.tree_metrics = ttk.Treeview(self.metrics_frame, columns=("algo", "avg_wait", "avg_turn", "avg_resp", "util", "tp", "cs"), 
                                         show="headings", style="Custom.Treeview", height=6)
        self.tree_metrics.heading("algo", text="Algorithm")
        self.tree_metrics.heading("avg_wait", text="Avg Wait Time (s)")
        self.tree_metrics.heading("avg_turn", text="Avg Turnaround (s)")
        self.tree_metrics.heading("avg_resp", text="Avg Response (s)")
        self.tree_metrics.heading("util", text="CPU Util %")
        self.tree_metrics.heading("tp", text="Throughput")
        self.tree_metrics.heading("cs", text="Context Switches")
        
        for col in ("algo", "avg_wait", "avg_turn", "avg_resp", "util", "tp", "cs"):
            self.tree_metrics.column(col, width=120, anchor="center")
            
        xscroll = ttk.Scrollbar(self.metrics_frame, orient="horizontal", command=self.tree_metrics.xview)
        self.tree_metrics.configure(xscrollcommand=xscroll.set)
        self.tree_metrics.pack(fill=tk.X, padx=10, pady=(10, 0))
        xscroll.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.empty_table = Styles.empty_state(self.metrics_frame, "No scheduling results yet. Run a scheduler comparison.")
        Styles.prepare_tree(self.tree_metrics)
        
    def _run_scheduler(self):
        # We fetch all ready processes and duplicate them for a batch run demo
        processes = list(self.main_window.process_manager.get_all_active())
        if not processes:
            # Generate a few temporary processes if queue is empty for demonstration
            self.main_window.simulator.generate_batch(5)
            self.main_window.process_manager.admit_all_new()
            processes = list(self.main_window.process_manager.get_all_active())
            
        algo = self.cb_algo.get()
        try:
            q = float(self.ent_q.get())
        except ValueError:
            messagebox.showerror("Invalid Quantum", "Time quantum must be a number greater than zero.")
            self.main_window.show_feedback("Invalid time quantum", "error")
            return
        if q <= 0:
            messagebox.showerror("Invalid Quantum", "Time quantum must be greater than zero.")
            self.main_window.show_feedback("Time quantum must be greater than zero", "error")
            return
            
        # Execute selected scheduling policy
        res = self.main_window.scheduler.run(algo, processes, q)
        
        # Save to Performance Manager and DB
        self.main_window.perf_mgr.record_result(res)
        self.main_window.db_service.save_scheduling_result({
            "session_id": self.main_window.current_session_id,
            **res.to_dict()
        })
        
        # Update UI elements
        self._draw_gantt(res)
        self._populate_metrics()
        self.main_window.show_feedback(f"{algo} scheduling run complete", "success")
        
    def _draw_gantt(self, result):
        self.gantt_canvas.delete("all")
        w = self.gantt_canvas.winfo_width()
        h = self.gantt_canvas.winfo_height()
        if w < 10 or h < 10:
            return
            
        gantt = result.gantt
        if not gantt:
            self.gantt_canvas.create_text(
                self.gantt_canvas.winfo_width() / 2,
                self.gantt_canvas.winfo_height() / 2,
                text="No execution timeline was produced.",
                fill=Colors.TEXT_SECONDARY, font=Fonts.LABEL_MD
            )
            return
        self.gantt_canvas.delete("empty")
            
        # Determine total simulation time span
        total_span = result.total_time
        if total_span <= 0:
            return
            
        x_start = 50
        x_end = w - 50
        y_top = 40
        y_bottom = h - 50
        
        # Draw timeline axis
        self.gantt_canvas.create_line(x_start, y_bottom, x_end, y_bottom, fill=Colors.TEXT_SECONDARY, width=2)
        
        scale_x = (x_end - x_start) / total_span
        
        # Draw segments
        colors_map = {}
        color_idx = 0
        
        for idx, seg in enumerate(gantt):
            seg_start = x_start + (seg.start * scale_x)
            seg_end = x_start + (seg.end * scale_x)
            
            # Segment color assignment
            if seg.pid == "IDLE":
                col = Colors.BG_INPUT
            else:
                if seg.pid not in colors_map:
                    colors_map[seg.pid] = Colors.CHART_PALETTE[color_idx % len(Colors.CHART_PALETTE)]
                    color_idx += 1
                col = colors_map[seg.pid]
                
            self.gantt_canvas.create_rectangle(seg_start, y_top, seg_end, y_bottom - 10, fill=col, outline=Colors.BORDER)
            self.gantt_canvas.create_text((seg_start + seg_end)/2, (y_top + y_bottom)/2 - 5, text=seg.pid, 
                                          fill=Colors.BG_DEEP if col != Colors.BG_INPUT else Colors.TEXT_PRIMARY, font=Fonts.TITLE)
            
            # Ticks markings
            self.gantt_canvas.create_line(seg_start, y_bottom, seg_start, y_bottom + 5, fill=Colors.TEXT_SECONDARY)
            self.gantt_canvas.create_text(seg_start, y_bottom + 15, text=f"{seg.start:.1f}", fill=Colors.TEXT_SECONDARY, font=Fonts.MONO_SM)
            
        # Last tick mark
        self.gantt_canvas.create_line(x_end, y_bottom, x_end, y_bottom + 5, fill=Colors.TEXT_SECONDARY)
        self.gantt_canvas.create_text(x_end, y_bottom + 15, text=f"{total_span:.1f}", fill=Colors.TEXT_SECONDARY, font=Fonts.MONO_SM)
        
    def _populate_metrics(self):
        self.tree_metrics.delete(*self.tree_metrics.get_children())
        rows = self.main_window.perf_mgr.summary_table()
        for index, r in enumerate(rows):
            tags = ("alternate",) if index % 2 else ()
            self.tree_metrics.insert("", "end", values=(
                r["Algorithm"], r["Avg Wait"], r["Avg Turnaround"], r["Avg Response"],
                r["CPU Util%"], r["Throughput"], r["Context Switches"]
            ), tags=tags)
        Styles.update_empty_state(self.tree_metrics, self.empty_table)
            
    def update_view(self):
        self._populate_metrics()
