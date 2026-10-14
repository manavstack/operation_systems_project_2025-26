"""
D-RTOS: Performance Analytics View
Visualizes scheduling algorithm comparisons (Average Wait, Turnaround,
Context Switches) using embedded Matplotlib figures.
"""

from __future__ import annotations
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import Colors, Fonts, Styles

class AnalyticsView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="📈 SCHEDULER PERFORMANCE ANALYTICS", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Grid layout splitting chart views
        self.grid_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.chart_frame_left = tk.Frame(self.grid_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.chart_frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chart_frame_right = tk.Frame(self.grid_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.chart_frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def update_view(self):
        # Fetch scheduling comparison metrics from Performance Manager
        comp = self.main_window.perf_mgr.compare()
        if not comp:
            # Render empty state message if no runs exist
            self._render_empty_state()
            return
            
        self._plot_waiting_times(comp.get("avg_waiting_time", {}))
        self._plot_turnaround_times(comp.get("avg_turnaround_time", {}))
        
    def _render_empty_state(self):
        for widget in self.chart_frame_left.winfo_children():
            widget.destroy()
        for widget in self.chart_frame_right.winfo_children():
            widget.destroy()
            
        lbl_l = tk.Label(self.chart_frame_left, text="No scheduling runs recorded.\nRun scheduler comparisons to populate graphs.", 
                         **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_MD))
        lbl_l.pack(fill=tk.BOTH, expand=True)
        
        lbl_r = tk.Label(self.chart_frame_right, text="No scheduling runs recorded.\nRun scheduler comparisons to populate graphs.", 
                         **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_MD))
        lbl_r.pack(fill=tk.BOTH, expand=True)
        
    def _plot_waiting_times(self, metric_data: dict):
        for widget in self.chart_frame_left.winfo_children():
            widget.destroy()
            
        vals = metric_data.get("values", {})
        if not vals:
            return
            
        fig, ax = plt.subplots(figsize=(5, 4), facecolor=Colors.BG_DEEP)
        ax.set_facecolor(Colors.BG_PANEL)
        
        algos = list(vals.keys())
        times = list(vals.values())
        
        # Plot horizontal bar chart
        bars = ax.barh(algos, times, color=Colors.CHART_PALETTE[:len(algos)])
        ax.set_title("Average Waiting Time (Lower is Better)", color=Colors.HUD_CYAN, fontsize=12, fontweight="bold")
        ax.set_xlabel("Time (Seconds)", color=Colors.TEXT_SECONDARY)
        ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=9)
        ax.spines['bottom'].set_color(Colors.BORDER)
        ax.spines['left'].set_color(Colors.BORDER)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add labels to bars
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f"{width:.2f}s", 
                    color=Colors.TEXT_PRIMARY, ha="left", va="center", fontsize=8)
            
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame_left)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def _plot_turnaround_times(self, metric_data: dict):
        for widget in self.chart_frame_right.winfo_children():
            widget.destroy()
            
        vals = metric_data.get("values", {})
        if not vals:
            return
            
        fig, ax = plt.subplots(figsize=(5, 4), facecolor=Colors.BG_DEEP)
        ax.set_facecolor(Colors.BG_PANEL)
        
        algos = list(vals.keys())
        times = list(vals.values())
        
        # Plot bar chart
        bars = ax.bar(algos, times, color=Colors.CHART_PALETTE[::-1][:len(algos)], width=0.4)
        ax.set_title("Average Turnaround Time (Lower is Better)", color=Colors.HUD_CYAN, fontsize=12, fontweight="bold")
        ax.set_ylabel("Time (Seconds)", color=Colors.TEXT_SECONDARY)
        ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=9)
        plt.xticks(rotation=15)
        ax.spines['bottom'].set_color(Colors.BORDER)
        ax.spines['left'].set_color(Colors.BORDER)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f"{height:.2f}s",
                    color=Colors.TEXT_PRIMARY, ha="center", va="bottom", fontsize=8)
            
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame_right)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
