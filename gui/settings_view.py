"""
D-RTOS: Settings View
Provides options for configuring the MongoDB URI connection, tick rates, and simulation resets.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import math

from gui.theme import Colors, Fonts, Styles

class SettingsView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="🔧 CONFIGURATION SETTINGS PANEL", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Grid frame
        frm_body = tk.Frame(self, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        frm_body.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        lbl_db = tk.Label(frm_body, text="MongoDB Database Connectivity Config", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_db.pack(anchor="w", padx=15, pady=15)
        
        # Connection URI entry
        frm_uri = tk.Frame(frm_body, bg=Colors.BG_PANEL)
        frm_uri.pack(fill=tk.X, padx=15, pady=5)
        tk.Label(frm_uri, text="MongoDB Connection Connection URI:", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(anchor="w")
        self.ent_uri = tk.Entry(frm_uri, **Styles.entry())
        self.ent_uri.insert(0, self.main_window.db_service.connection_uri)
        self.ent_uri.pack(fill=tk.X, pady=5)
        
        btn_conn = tk.Button(frm_body, text="🔌 Apply Connection & Reconnect", 
                             **Styles.button(), command=self._reconnect_db)
        btn_conn.pack(anchor="w", padx=15, pady=10)
        
        # Simulation parameters
        lbl_sim = tk.Label(frm_body, text="D-RTOS Simulation Ticks Speed Parameters", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_sim.pack(anchor="w", padx=15, pady=15)
        
        frm_ticks = tk.Frame(frm_body, bg=Colors.BG_PANEL)
        frm_ticks.pack(fill=tk.X, padx=15, pady=5)
        tk.Label(frm_ticks, text="Tick Size Rate (Seconds / Sim Tick):", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(anchor="w")
        self.ent_tick = tk.Entry(frm_ticks, **Styles.entry())
        self.ent_tick.insert(0, str(self.main_window.simulation_tick_rate))
        self.ent_tick.pack(anchor="w", pady=5)
        
        btn_tick = tk.Button(frm_body, text="⚙️ Apply Tick Configurations", 
                             **Styles.button(), command=self._apply_ticks)
        btn_tick.pack(anchor="w", padx=15, pady=10)
        
        # System control reset
        lbl_sys = tk.Label(frm_body, text="System Danger Zone Actions", **Styles.label(fg=Colors.ALERT_RED, font=Fonts.TITLE))
        lbl_sys.pack(anchor="w", padx=15, pady=20)
        
        btn_reset = tk.Button(frm_body, text="⚠️ Fully Reset Simulation State", 
                               **Styles.danger_button(), command=self._reset_sim)
        btn_reset.pack(anchor="w", padx=15, pady=10)
        
    def _reconnect_db(self):
        uri = self.ent_uri.get()
        self.main_window.db_service.reconnect(uri)
        
        self.main_window.lbl_db_status.configure(
            text=f"DATABASE: {self.main_window.db_service.status}",
            fg=Colors.HUD_CYAN if self.main_window.db_service.connected else Colors.AMBER_WARN
        )
        if self.main_window.db_service.connected:
            self.main_window.show_feedback("Connected to MongoDB", "success")
            messagebox.showinfo("Database Config", "Successfully connected to MongoDB server.")
        else:
            self.main_window.show_feedback("MongoDB unavailable; using in-memory storage", "warning")
            messagebox.showwarning("Database Config", "Failed to connect to MongoDB server. Falling back to local in-memory mock storage.")
            
    def _apply_ticks(self):
        try:
            tick = float(self.ent_tick.get())
        except ValueError:
            messagebox.showerror("Validation Error", "Tick Size must be numeric.")
            self.main_window.show_feedback("Tick interval must be a positive number", "error")
            return
        if not math.isfinite(tick) or tick <= 0:
            messagebox.showerror("Validation Error", "Tick Size must be a finite number greater than zero.")
            self.main_window.show_feedback("Tick interval must be greater than zero", "error")
            return
            
        self.main_window.simulation_tick_rate = tick
        self.main_window.show_feedback(f"Tick interval set to {tick:g} seconds", "success")
        messagebox.showinfo("Sim Settings", f"Simulation tick rate successfully adjusted to {tick} seconds.")
        
    def _reset_sim(self):
        confirm = messagebox.askyesno("Confirm Full Reset", "Are you sure you want to clear all active queues, caches, and parameters to start a clean simulation run?")
        if confirm:
            self.main_window.reset_simulation()
            
    def update_view(self):
        pass
