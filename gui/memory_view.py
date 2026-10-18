"""
D-RTOS: Memory View
Visualizes contiguous memory block partitions, free blocks, and
evaluates First Fit, Best Fit, and Worst Fit allocation strategies.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from gui.theme import Colors, Fonts, Styles

class MemoryView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="💾 CONTIGUOUS PHYSICAL RAM ALLOCATOR", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Split layout
        self.split_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left side: Memory Map Block Canvas
        self.map_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.map_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_m = tk.Label(self.map_panel, text="Physical RAM Address Block Map (1024 MB)", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_m.pack(anchor="w", padx=10, pady=5)
        
        self.canvas_mem = tk.Canvas(self.map_panel, bg=Colors.BG_DEEP, highlightthickness=0)
        self.canvas_mem.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas_mem.bind("<Configure>", lambda e: self._draw_mem_map())
        
        # Right side: Allocator Strategy Control panel
        self.control_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, width=420, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.control_panel.pack_propagate(False)
        
        lbl_c = tk.Label(self.control_panel, text="Allocation Parameters", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_c.pack(anchor="w", padx=10, pady=5)
        
        # Allocation strategy dropdown
        frm_strat = tk.Frame(self.control_panel, bg=Colors.BG_PANEL)
        frm_strat.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(frm_strat, text="Strategy Policy:", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(side=tk.LEFT, padx=5)
        self.cb_strat = ttk.Combobox(frm_strat, values=["First Fit", "Best Fit", "Worst Fit"], state="readonly")
        self.cb_strat.current(0)
        self.cb_strat.pack(side=tk.LEFT, padx=5)
        self.cb_strat.bind("<<ComboboxSelected>>", self._change_strategy)
        
        # Manual Alloc Form
        lbl_f = tk.Label(self.control_panel, text="Simulated Memory Request Injector", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_f.pack(anchor="w", padx=10, pady=15)
        
        frm_form = tk.Frame(self.control_panel, bg=Colors.BG_PANEL)
        frm_form.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(frm_form, text="PID:", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=0, column=0, sticky="w", pady=5)
        self.ent_pid = tk.Entry(frm_form, **Styles.entry())
        self.ent_pid.insert(0, "P99")
        self.ent_pid.grid(row=0, column=1, sticky="ew", pady=5)
        
        tk.Label(frm_form, text="Size (MB):", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=1, column=0, sticky="w", pady=5)
        self.ent_size = tk.Entry(frm_form, **Styles.entry())
        self.ent_size.insert(0, "150")
        self.ent_size.grid(row=1, column=1, sticky="ew", pady=5)
        
        btn_alloc = tk.Button(frm_form, text="📥 Allocate Memory Block", **Styles.success_button(), command=self._manual_allocate)
        btn_alloc.grid(row=2, columnspan=2, pady=15, sticky="ew")
        
        # Memory metrics
        lbl_s = tk.Label(self.control_panel, text="Fragmentation Stats", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_s.pack(anchor="w", padx=10, pady=15)
        
        self.lbl_stats = tk.Label(self.control_panel, text="Used: 0 MB  |  Free: 1024 MB\nExternal Fragmentation: 0.0%", 
                                  **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_MD))
        self.lbl_stats.pack(pady=10)
        
    def _change_strategy(self, event):
        self.main_window.memory_mgr.strategy = self.cb_strat.get()
        
    def _manual_allocate(self):
        pid = self.ent_pid.get().upper()
        try:
            size = int(self.ent_size.get())
        except ValueError:
            messagebox.showerror("Validation Error", "Size must be an integer.")
            self.main_window.show_feedback("Memory size must be a whole number", "error")
            return
        if size <= 0:
            messagebox.showerror("Validation Error", "Size must be greater than zero.")
            self.main_window.show_feedback("Memory size must be greater than zero", "error")
            return
            
        start = self.main_window.memory_mgr.allocate(pid, f"Manual-{pid}", size)
        
        # Log database memory event
        self.main_window.db_service.save_memory_event({
            "session_id": self.main_window.current_session_id,
            "action": "ALLOCATE",
            "pid": pid,
            "size_mb": size,
            "start_addr": start if start is not None else -1,
            "success": start is not None
        })
        
        self.update_view()
        if start is not None:
            self.main_window.show_feedback(f"Allocated {size} MB to {pid}", "success")
            messagebox.showinfo("Memory Manager", f"Successfully allocated {size} MB at address {start} MB.")
        else:
            self.main_window.show_feedback(f"Could not allocate {size} MB to {pid}", "error")
            messagebox.showerror("Allocation Failed", "Out of Memory (No contiguous block fits requirements). Try running deallocation.")
            
    def _draw_mem_map(self):
        self.canvas_mem.delete("all")
        w = self.canvas_mem.winfo_width()
        h = self.canvas_mem.winfo_height()
        if w < 10 or h < 10:
            return
            
        blocks = self.main_window.memory_mgr.blocks
        total = self.main_window.memory_mgr.total_mb
        
        # Draw blocks inside grid
        y_top = 20
        y_bottom = h - 40
        x_left = 30
        x_right = w - 30
        
        scale_x = (x_right - x_left) / total
        
        colors_map = {}
        color_idx = 0
        
        for b in blocks:
            bx_start = x_left + (b.start * scale_x)
            bx_end = x_left + (b.end * scale_x)
            
            if b.is_free:
                col = Colors.BG_INPUT
                lbl = "FREE"
            else:
                if b.pid not in colors_map:
                    colors_map[b.pid] = Colors.CHART_PALETTE[color_idx % len(Colors.CHART_PALETTE)]
                    color_idx += 1
                col = colors_map[b.pid]
                lbl = f"{b.pid}\n({b.size}MB)"
                
            self.canvas_mem.create_rectangle(bx_start, y_top, bx_end, y_bottom, fill=col, outline=Colors.BORDER)
            
            # Text label
            self.canvas_mem.create_text((bx_start+bx_end)/2, (y_top+y_bottom)/2, text=lbl,
                                          fill=Colors.BG_DEEP if not b.is_free else Colors.TEXT_PRIMARY, 
                                          font=Fonts.TITLE, justify="center")
            
            # Address tick
            self.canvas_mem.create_line(bx_start, y_bottom, bx_start, y_bottom + 5, fill=Colors.TEXT_SECONDARY)
            self.canvas_mem.create_text(bx_start, y_bottom + 15, text=f"{b.start}", fill=Colors.TEXT_SECONDARY, font=Fonts.MONO_SM)
            
        # Draw final tick
        self.canvas_mem.create_line(x_right, y_bottom, x_right, y_bottom + 5, fill=Colors.TEXT_SECONDARY)
        self.canvas_mem.create_text(x_right, y_bottom + 15, text=f"{total}", fill=Colors.TEXT_SECONDARY, font=Fonts.MONO_SM)
        
    def update_view(self):
        # Update metrics labels
        stats = self.main_window.memory_mgr.get_stats()
        self.lbl_stats.configure(
            text=f"Used: {stats.get('used_mb', 0)} MB  |  Free: {stats.get('free_mb', 0)} MB\n"
                 f"Allocation Failures: {stats.get('allocation_failures', 0)}\n"
                 f"External Fragmentation: {stats.get('fragmentation', 0.0):.1f}%"
        )
        self._draw_mem_map()
        self.cb_strat.set(self.main_window.memory_mgr.strategy)
