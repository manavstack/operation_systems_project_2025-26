"""
D-RTOS: Radar View
Renders an interactive circular Plan Position Indicator (PPI) radar sweep canvas
showing target blips, live tracking tables, and manual target injection.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import math

from gui.theme import Colors, Fonts, Styles

class RadarView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self.sweep_angle = 0
        self._animation_job = None
        self._build_ui()
        self._start_scope_animation()
        
    def _build_ui(self):
        # 1. Left Side: Circular Scope
        self.scope_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.scope_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas_scope = tk.Canvas(self.scope_frame, bg=Colors.BG_DEEP, highlightthickness=1, highlightbackground=Colors.BORDER)
        self.canvas_scope.pack(fill=tk.BOTH, expand=True)
        self.canvas_scope.bind("<Configure>", self._resize_canvas)
        
        # 2. Right Side: Controls and Tracking Table
        self.sidebar_frame = tk.Frame(self, bg=Colors.BG_PANEL, width=420, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.sidebar_frame.pack_propagate(False)
        
        # Title
        lbl_st = tk.Label(self.sidebar_frame, text="TRACKING INFORMATION & CONTROLS", **Styles.header_label())
        lbl_st.pack(anchor="w", padx=10, pady=10)
        
        # Manual Object Injection Form
        frm_inj = tk.Frame(self.sidebar_frame, bg=Colors.BG_PANEL)
        frm_inj.pack(fill=tk.X, padx=10, pady=5)
        frm_inj.grid_columnconfigure(1, weight=1)
        
        tk.Label(frm_inj, text="Type:", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=0, column=0, sticky="w", pady=2)
        self.cb_type = ttk.Combobox(frm_inj, values=[
            "Friendly Aircraft", "Unknown Aircraft", "Drone", 
            "Weather Object", "Unidentified Object", "Potential Threat", "Critical Threat"
        ], state="readonly")
        self.cb_type.current(1)
        self.cb_type.grid(row=0, column=1, sticky="ew", pady=2)
        
        tk.Label(frm_inj, text="Dist (km):", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=1, column=0, sticky="w", pady=2)
        self.ent_dist = tk.Entry(frm_inj, **Styles.entry())
        self.ent_dist.insert(0, "120")
        self.ent_dist.grid(row=1, column=1, sticky="ew", pady=2)
        
        tk.Label(frm_inj, text="Speed (km/h):", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=2, column=0, sticky="w", pady=2)
        self.ent_speed = tk.Entry(frm_inj, **Styles.entry())
        self.ent_speed.insert(0, "720")
        self.ent_speed.grid(row=2, column=1, sticky="ew", pady=2)
        
        tk.Label(frm_inj, text="Heading:", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=3, column=0, sticky="w", pady=2)
        self.cb_dir = ttk.Combobox(frm_inj, values=["N", "NE", "E", "SE", "S", "SW", "W", "NW"], state="readonly")
        self.cb_dir.current(1)
        self.cb_dir.grid(row=3, column=1, sticky="ew", pady=2)
        
        btn_inject = tk.Button(frm_inj, text="💥 Inject Object Event", **Styles.danger_button(), command=self._inject_manual)
        btn_inject.grid(row=4, columnspan=2, pady=10, sticky="ew")
        
        # Threat Probability slider
        frm_prob = tk.Frame(self.sidebar_frame, bg=Colors.BG_PANEL)
        frm_prob.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frm_prob, text="Threat Probability Level:", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(anchor="w")
        self.sld_prob = tk.Scale(frm_prob, from_=0.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL,
                                 bg=Colors.BG_PANEL, fg=Colors.TEXT_PRIMARY, highlightthickness=0)
        self.sld_prob.set(0.3)
        self.sld_prob.pack(fill=tk.X)
        
        # Auto-generation controls
        self.btn_auto = tk.Button(self.sidebar_frame, text="🟢 Start Radar Scanner", 
                                  **Styles.success_button(), command=self._toggle_auto)
        self.btn_auto.pack(fill=tk.X, padx=10, pady=5)
        self.lbl_scanner_state = tk.Label(self.sidebar_frame, text="SCANNER STOPPED  •  0 TRACKS",
                                          **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_SM))
        self.lbl_scanner_state.pack(anchor="w", padx=12, pady=(2, 4))
        
        # Radar Detection Logs Table
        lbl_tbl = tk.Label(self.sidebar_frame, text="Live Target Detection Table", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_tbl.pack(anchor="w", padx=10, pady=10)
        
        tbl_frame = tk.Frame(self.sidebar_frame, bg=Colors.BG_PANEL)
        tbl_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(tbl_frame, columns=("id", "type", "threat", "dist", "speed"), 
                                 show="headings", style="Custom.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("threat", text="Threat")
        self.tree.heading("dist", text="Dist (km)")
        self.tree.heading("speed", text="Vel (km/h)")
        
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("type", width=140, anchor="w")
        self.tree.column("threat", width=80, anchor="center")
        self.tree.column("dist", width=80, anchor="center")
        self.tree.column("speed", width=80, anchor="center")
        
        scroll = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(tbl_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll.set, xscrollcommand=xscroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.empty_table = Styles.empty_state(tbl_frame, "No radar tracks yet.\nStart the scanner or inject a target.")
        Styles.prepare_tree(self.tree)
        
    def _resize_canvas(self, event):
        self._redraw_scope()
        
    def _redraw_scope(self):
        self.canvas_scope.delete("all")
        w = self.canvas_scope.winfo_width()
        h = self.canvas_scope.winfo_height()
        cx, cy = w / 2, h / 2
        r = min(cx, cy) - 20
        if r < 10:
            return
            
        # Draw background concentric circles
        for mult in [0.25, 0.5, 0.75, 1.0]:
            cr = r * mult
            self.canvas_scope.create_oval(cx - cr, cy - cr, cx + cr, cy + cr, 
                                          outline=Colors.BORDER, width=1)
            
        # Draw crosshairs
        self.canvas_scope.create_line(cx - r, cy, cx + r, cy, fill=Colors.BORDER)
        self.canvas_scope.create_line(cx, cy - r, cx, cy + r, fill=Colors.BORDER)
        
        # Draw sweep line
        rad = math.radians(self.sweep_angle)
        sx = cx + r * math.cos(rad)
        sy = cy + r * math.sin(rad)
        self.canvas_scope.create_line(cx, cy, sx, sy, fill=Colors.RADAR_GREEN, width=2, tags="sweep")
        
        # Plot blips
        objs = self.main_window.simulator.detected_objects
        for obj in objs[-15:]:  # Draw last 15 detected blips
            # Convert polar coordinates to Cartesian
            # We map direction headings (N, NE, etc) to angles
            dir_angles = {"E": 0, "SE": 45, "S": 90, "SW": 135, "W": 180, "NW": 225, "N": 270, "NE": 315}
            angle = dir_angles.get(obj.direction, 0)
            rad_obj = math.radians(angle)
            
            # Map distance (max 300km) to radius
            dist_fraction = min(1.0, obj.distance_km / 300.0)
            dist_r = r * dist_fraction
            
            bx = cx + dist_r * math.cos(rad_obj)
            by = cy + dist_r * math.sin(rad_obj)
            
            # Determine color by threat level
            color = Colors.for_threat(obj.threat_level.name)
            
            # Blip size
            bs = 6
            self.canvas_scope.create_oval(bx - bs, by - bs, bx + bs, by + bs, 
                                          fill=color, outline=Colors.BG_DEEP)
            self.canvas_scope.create_text(bx, by - 12, text=obj.object_id, 
                                          fill=color, font=Fonts.MONO_SM)
            
    def _start_scope_animation(self):
        if not self.main_window.is_running or not self.winfo_exists():
            return
        self.sweep_angle = (self.sweep_angle + 3) % 360
        self._redraw_scope()
        self._animation_job = self.after(50, self._start_scope_animation)
        
    def _toggle_auto(self):
        # Update simulator threat config
        self.main_window.simulator.threat_probability = self.sld_prob.get()
        
        if self.main_window.simulator.auto_running:
            self.main_window.simulator.stop_auto()
            self.btn_auto.configure(text="🟢 Start Radar Scanner", **Styles.success_button())
            self.main_window.show_feedback("Radar scanner stopped", "info")
        else:
            self.main_window.simulator.start_auto(callback=self._handle_new_target)
            self.btn_auto.configure(text="🔴 Stop Radar Scanner", **Styles.danger_button())
            self.main_window.show_feedback("Radar scanner started", "success")
        self.update_view()
            
    def _handle_new_target(self, obj):
        # Convert radar target to OS Process
        pcb = self.main_window.process_manager.create_process(
            object_id=obj.object_id,
            threat_level=obj.threat_level,
            event_id=obj.event_id
        )
        # Log to MongoDB
        self.main_window.db_service.save_radar_event(obj.to_dict())
        self.main_window.db_service.save_process(pcb.to_dict())
        
        # Auto-coalesce/admit to READY queue
        self.main_window.process_manager.admit_all_new()
        
    def _inject_manual(self):
        try:
            dist = float(self.ent_dist.get())
            speed = float(self.ent_speed.get())
        except ValueError:
            messagebox.showerror("Validation Error", "Distance and Speed must be numeric.")
            self.main_window.show_feedback("Target values must be numeric", "error")
            return
        if not 0 < dist <= 300 or speed < 0:
            messagebox.showerror("Validation Error", "Distance must be greater than 0 and at most 300 km; speed cannot be negative.")
            self.main_window.show_feedback("Target values are outside the valid range", "error")
            return
            
        obj = self.main_window.simulator.generate_manual(
            object_type=self.cb_type.get(),
            distance_km=dist,
            velocity_kmh=speed,
            direction=self.cb_dir.get()
        )
        self._handle_new_target(obj)
        self.update_view()
        self.main_window.show_feedback(f"Target {obj.object_id} injected", "success")
        messagebox.showinfo("Radar Injector", f"Fictional target {obj.object_id} successfully injected and PCB created.")
        
    def update_view(self):
        # Redraw list of blips in tree table
        self.tree.delete(*self.tree.get_children())
        objects = list(reversed(self.main_window.simulator.detected_objects))
        for index, obj in enumerate(objects):
            tags = [obj.threat_level.name]
            if index % 2:
                tags.insert(0, "alternate")
            self.tree.insert("", "end", values=(
                obj.object_id, obj.object_type, obj.threat_level.name,
                f"{obj.distance_km:.1f}", f"{obj.velocity_kmh:.0f}"
            ), tags=tuple(tags))
        active = self.main_window.simulator.auto_running
        self.lbl_scanner_state.configure(
            text=f"SCANNER {'ACTIVE' if active else 'STOPPED'}  •  {len(objects)} TRACKS",
            fg=Colors.RADAR_GREEN if active else Colors.TEXT_SECONDARY
        )
        Styles.update_empty_state(self.tree, self.empty_table)
        self._redraw_scope()
