"""
D-RTOS: Paging View
Logical-to-physical address translator and step-by-step
page replacement simulator comparing FIFO and LRU algorithms.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import Colors, Fonts, Styles

class PagingView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="📖 PAGING & VIRTUAL MEMORY STATION", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Upper grid split into Logical Address Translation and Reference simulator
        self.split_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left side: Address translator calculator
        self.trans_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.trans_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_t = tk.Label(self.trans_panel, text="Logical Address Translation Engine", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_t.pack(anchor="w", padx=10, pady=5)
        
        frm_calc = tk.Frame(self.trans_panel, bg=Colors.BG_PANEL)
        frm_calc.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(frm_calc, text="Process PID:", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=0, column=0, sticky="w", pady=5)
        self.cb_pids = ttk.Combobox(frm_calc, state="readonly")
        self.cb_pids.grid(row=0, column=1, sticky="ew", pady=5)
        
        tk.Label(frm_calc, text="Logical Address (MB):", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=1, column=0, sticky="w", pady=5)
        self.ent_log_addr = tk.Entry(frm_calc, **Styles.entry())
        self.ent_log_addr.insert(0, "45")
        self.ent_log_addr.grid(row=1, column=1, sticky="ew", pady=5)
        
        btn_calc = tk.Button(frm_calc, text="🔍 Translate Address", **Styles.success_button(), command=self._translate_address)
        btn_calc.grid(row=2, columnspan=2, pady=10, sticky="ew")
        
        self.lbl_trans_result = tk.Label(self.trans_panel, text="Physical Frame: N/A  |  Offset: N/A\nPhysical Address: N/A",
                                         **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_MD))
        self.lbl_trans_result.pack(pady=15)
        
        # Right side: FIFO vs LRU reference string simulator
        self.page_sim_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, width=540, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.page_sim_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.page_sim_panel.pack_propagate(False)
        
        lbl_s = tk.Label(self.page_sim_panel, text="Page Replacement Algorithm Simulator", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_s.pack(anchor="w", padx=10, pady=5)
        
        frm_sim = tk.Frame(self.page_sim_panel, bg=Colors.BG_PANEL)
        frm_sim.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(frm_sim, text="Reference String:", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=0, column=0, sticky="w", pady=2)
        self.ent_ref = tk.Entry(frm_sim, **Styles.entry())
        self.ent_ref.insert(0, "7 0 1 2 0 3 0 4 2 3")
        self.ent_ref.grid(row=0, column=1, sticky="ew", pady=2)
        
        tk.Label(frm_sim, text="Physical Frames count:", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=1, column=0, sticky="w", pady=2)
        self.ent_frames = tk.Entry(frm_sim, **Styles.entry())
        self.ent_frames.insert(0, "3")
        self.ent_frames.grid(row=1, column=1, sticky="ew", pady=2)
        
        btn_sim = tk.Button(frm_sim, text="🧪 Run Replacement Test", **Styles.button(), command=self._run_page_test)
        btn_sim.grid(row=2, columnspan=2, pady=10, sticky="ew")
        
        # Matplotlib chart comparing faults
        self.chart_container = tk.Frame(self.page_sim_panel, bg=Colors.BG_DEEP, height=180)
        self.chart_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.lbl_chart_empty = tk.Label(
            self.chart_container, text="Run a reference string to compare FIFO and LRU.",
            **Styles.label(fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DEEP)
        )
        self.lbl_chart_empty.place(relx=0.5, rely=0.5, anchor="center")
        
    def _translate_address(self):
        pid = self.cb_pids.get()
        if not pid:
            messagebox.showwarning("Paging Manager", "No active processes available for address lookup. Generate some blips first.")
            self.main_window.show_feedback("No active process to translate", "warning")
            return
            
        try:
            addr = int(self.ent_log_addr.get())
        except ValueError:
            messagebox.showerror("Validation Error", "Logical Address must be numeric.")
            self.main_window.show_feedback("Logical address must be a whole number", "error")
            return
        if addr < 0:
            messagebox.showerror("Validation Error", "Logical Address cannot be negative.")
            self.main_window.show_feedback("Logical address cannot be negative", "error")
            return
            
        # Allocate page translation mock
        res = self.main_window.paging_mgr.translate(pid, addr)
        if res is not None:
            pg, off, frame, phy = res
            self.lbl_trans_result.configure(
                text=f"Page Number: {pg}  |  Offset: {off} MB\n"
                     f"Physical Frame Number: {frame}\n"
                     f"Physical Address: {phy} MB",
                fg=Colors.RADAR_GREEN
            )
        else:
            # Re-allocate pages if page fault occurs
            self.main_window.paging_mgr.allocate_pages(pid, self.main_window.paging_mgr.pages_required(128))
            res = self.main_window.paging_mgr.translate(pid, addr)
            if res:
                pg, off, frame, phy = res
                self.lbl_trans_result.configure(
                    text=f"⚠ PAGE FAULT -> Page Allocated dynamically.\n"
                         f"Page: {pg}  |  Offset: {off} MB\n"
                         f"Frame: {frame}  |  Physical Address: {phy} MB",
                    fg=Colors.AMBER_WARN
                )
            else:
                self.lbl_trans_result.configure(text="PAGE FAULT: Physical Memory Full", fg=Colors.ALERT_RED)
                
        self.main_window.views["Memory Manager"].update_view()
        if res:
            self.main_window.show_feedback(f"Translated address for {pid}", "success")
        else:
            self.main_window.show_feedback("Translation failed: physical memory is full", "error")
        
    def _run_page_test(self):
        tokens = self.ent_ref.get().split()
        try:
            ref_str = [int(x) for x in tokens]
            frames = int(self.ent_frames.get())
        except ValueError:
            messagebox.showerror("Invalid Test Input", "Use whole numbers for the reference string and frame count.")
            self.main_window.show_feedback("Reference string and frames must use whole numbers", "error")
            return
            
        if not ref_str or any(page < 0 for page in ref_str):
            messagebox.showwarning("Validation Error", "Enter one or more non-negative page numbers separated by spaces.")
            self.main_window.show_feedback("Enter non-negative page numbers", "error")
            return
        if frames <= 0:
            messagebox.showwarning("Validation Error", "Physical frame count must be greater than zero.")
            self.main_window.show_feedback("Frame count must be greater than zero", "error")
            return
            
        # Run FIFO & LRU replacement algorithms
        comp = self.main_window.paging_mgr.compare_algorithms(ref_str, frames)
        self._plot_page_faults(comp["fifo"]["page_faults"], comp["lru"]["page_faults"])
        self.main_window.show_feedback("FIFO and LRU comparison complete", "success")
        
    def _plot_page_faults(self, fifo_faults: int, lru_faults: int):
        for widget in self.chart_container.winfo_children():
            widget.destroy()
            
        fig, ax = plt.subplots(figsize=(4.0, 1.8), facecolor=Colors.BG_DEEP)
        ax.set_facecolor(Colors.BG_PANEL)
        
        algos = ['FIFO', 'LRU']
        faults = [fifo_faults, lru_faults]
        
        ax.bar(algos, faults, color=[Colors.AMBER_WARN, Colors.HUD_CYAN], width=0.4)
        ax.set_title("Page Fault Comparison", color=Colors.HUD_CYAN, fontsize=10, fontweight="bold")
        ax.set_ylabel("Faults", color=Colors.TEXT_SECONDARY, fontsize=8)
        ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=8)
        ax.spines['bottom'].set_color(Colors.BORDER)
        ax.spines['left'].set_color(Colors.BORDER)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def update_view(self):
        # Update process drop down lists
        pids = [p.pid for p in self.main_window.process_manager.get_all_active()]
        self.cb_pids['values'] = pids
        if pids:
            self.cb_pids.current(0)
