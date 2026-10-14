"""
D-RTOS: Multi-Core View
Renders CPU core utilization bars, lists active core processes, and
demonstrates the dynamic load balancing migration algorithm.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import Colors, Fonts, Styles

class MultiCoreView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="🧠 MULTI-CORE PROCESSOR HUD & BALANCER", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Grid frame split into Load Indicators and Balancer demo
        self.split_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left side: Live core meters & assigned processes
        self.cores_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.cores_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_c = tk.Label(self.cores_panel, text="CPU Core Activity Panel", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_c.pack(anchor="w", padx=10, pady=5)
        
        self.core_widgets = []
        for i in range(4):
            f_core = tk.Frame(self.cores_panel, bg=Colors.BG_TABLE, bd=1, relief="flat", padx=10, pady=10)
            f_core.pack(fill=tk.X, padx=10, pady=5)
            
            lbl_core = tk.Label(f_core, text=f"CPU CORE {i}", **Styles.label(fg=Colors.HUD_CYAN, bg=Colors.BG_TABLE, font=Fonts.TITLE))
            lbl_core.pack(side=tk.LEFT, padx=5)
            
            bar = ttk.Progressbar(f_core, length=200, mode='determinate')
            bar.pack(side=tk.LEFT, padx=15)
            
            lbl_val = tk.Label(f_core, text="0.0%", **Styles.label(fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TABLE, font=Fonts.MONO_MD))
            lbl_val.pack(side=tk.LEFT, padx=5)
            
            lbl_proc = tk.Label(f_core, text="Running: IDLE", **Styles.label(fg=Colors.TEXT_SECONDARY, bg=Colors.BG_TABLE, font=Fonts.LABEL_MD))
            lbl_proc.pack(side=tk.RIGHT, padx=10)
            
            self.core_widgets.append((bar, lbl_val, lbl_proc))
            
        # Right side: Load imbalance variance charts and balance trigger
        self.balancer_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, width=480, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.balancer_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.balancer_panel.pack_propagate(False)
        
        lbl_b = tk.Label(self.balancer_panel, text="Dynamic Load Balancing Station", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_b.pack(anchor="w", padx=10, pady=5)
        
        # Load Imbalance stats
        self.lbl_variance = tk.Label(self.balancer_panel, text="Core Spread Variance: 0.00", 
                                     **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.LABEL_MD))
        self.lbl_variance.pack(pady=10)
        
        # Chart display area
        self.chart_container = tk.Frame(self.balancer_panel, bg=Colors.BG_DEEP, height=220)
        self.chart_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Balance trigger buttons
        self.btn_balance = tk.Button(self.balancer_panel, text="⚖️ Trigger OS Load Balancer", 
                                     **Styles.success_button(), command=self._trigger_load_balance)
        self.btn_balance.pack(fill=tk.X, padx=20, pady=15)
        
    def _trigger_load_balance(self):
        # Perform dynamic load migration on ready list
        ready_queue = self.main_window.process_manager.ready_queue
        migrations = self.main_window.multicore_mgr.load_balance(ready_queue)
        
        # Show Matplotlib plot of load variance before and after
        before, after = self.main_window.multicore_mgr.simulate_load_imbalance()
        self._plot_load_balancing(before, after)
        
        if migrations:
            log_str = "\n".join([f"Process {m['pid']} migrated to Core {m['to_core']}" for m in migrations])
            messagebox.showinfo("Load Balancer Active", f"Load imbalance successfully balanced.\n\nMigrations:\n{log_str}")
        else:
            messagebox.showinfo("Load Balancer Active", "Core utilization variance within safe threshold limits. No process migration necessary.")
            
    def _plot_load_balancing(self, before: list[float], after: list[float]):
        # Clear container
        for widget in self.chart_container.winfo_children():
            widget.destroy()
            
        fig, ax = plt.subplots(figsize=(4.5, 2.2), facecolor=Colors.BG_DEEP)
        ax.set_facecolor(Colors.BG_PANEL)
        
        x = range(4)
        width = 0.35
        
        ax.bar([i - width/2 for i in x], before, width, label='Before', color=Colors.ALERT_RED)
        ax.bar([i + width/2 for i in x], after, width, label='After', color=Colors.RADAR_GREEN)
        
        ax.set_title("CPU Load Variance Shift", color=Colors.HUD_CYAN, fontsize=10, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([f"Core {i}" for i in x], color=Colors.TEXT_SECONDARY, fontsize=8)
        ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=8)
        ax.set_ylim(0, 100)
        ax.legend(facecolor=Colors.BG_DEEP, edgecolor=Colors.BORDER, labelcolor=Colors.TEXT_PRIMARY, fontsize=7)
        ax.spines['bottom'].set_color(Colors.BORDER)
        ax.spines['left'].set_color(Colors.BORDER)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def update_view(self):
        # Update core widgets
        stats = self.main_window.multicore_mgr.get_stats()
        self.lbl_variance.configure(text=f"Core Spread Variance: {stats.get('utilization_variance', 0.0):.2f}")
        
        for idx, core in enumerate(self.main_window.multicore_mgr.cores):
            bar, lbl_val, lbl_proc = self.core_widgets[idx]
            util = core.utilization
            bar['value'] = util
            lbl_val.configure(text=f"{util:.1f}%")
            
            p = core.current_process
            if p:
                lbl_proc.configure(text=f"Running: {p.pid} ({p.process_name})", fg=Colors.RADAR_GREEN)
            else:
                lbl_proc.configure(text="Running: IDLE", fg=Colors.TEXT_SECONDARY)
