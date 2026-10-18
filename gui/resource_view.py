"""
D-RTOS: Resource View
Displays allocated vs available instances of simulated multi-instance resources.
Provides a request builder interface for processes to request resources.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from gui.theme import Colors, Fonts, Styles

class ResourceView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="🛠️ SYSTEM RESOURCE CONTROL BOARD", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Upper grid split into inventory and request builder
        self.split_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left side: Current resource inventory
        self.inv_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.inv_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_i = tk.Label(self.inv_panel, text="System Resource Inventory & Allocation Table", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_i.pack(anchor="w", padx=10, pady=5)
        
        self.tree_inv = ttk.Treeview(self.inv_panel, columns=("res", "total", "avail", "alloc", "util"), 
                                     show="headings", style="Custom.Treeview")
        self.tree_inv.heading("res", text="Resource Name")
        self.tree_inv.heading("total", text="Total Instances")
        self.tree_inv.heading("avail", text="Available")
        self.tree_inv.heading("alloc", text="Allocated")
        self.tree_inv.heading("util", text="Utilization %")
        
        for col in ("res", "total", "avail", "alloc", "util"):
            self.tree_inv.column(col, width=100, anchor="center")
            
        xscroll = ttk.Scrollbar(self.inv_panel, orient="horizontal", command=self.tree_inv.xview)
        self.tree_inv.configure(xscrollcommand=xscroll.set)
        self.tree_inv.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        xscroll.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.empty_table = Styles.empty_state(self.inv_panel, "No resource inventory is available.")
        Styles.prepare_tree(self.tree_inv)
        
        # Right side: Request builder
        self.req_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, width=420, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.req_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.req_panel.pack_propagate(False)
        
        lbl_r = tk.Label(self.req_panel, text="Interactive Resource Allocator Form", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_r.pack(anchor="w", padx=10, pady=5)
        
        # Form PID combobox
        frm_pid = tk.Frame(self.req_panel, bg=Colors.BG_PANEL)
        frm_pid.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(frm_pid, text="Requester PID:", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(side=tk.LEFT, padx=5)
        self.cb_pids = ttk.Combobox(frm_pid, state="readonly")
        self.cb_pids.pack(side=tk.LEFT, padx=5)
        
        # Grid of resource sliders/entries
        frm_grid = tk.Frame(self.req_panel, bg=Colors.BG_PANEL)
        frm_grid.pack(fill=tk.X, padx=10, pady=5)
        
        self.sliders = {}
        row = 0
        for name in ["CPU", "Radar Processor", "GPU", "Communication Channel"]:
            tk.Label(frm_grid, text=f"{name}:", **Styles.label(fg=Colors.TEXT_SECONDARY)).grid(row=row, column=0, sticky="w", pady=5)
            ent = tk.Entry(frm_grid, width=5, **Styles.entry())
            ent.insert(0, "0")
            ent.grid(row=row, column=1, sticky="w", pady=5, padx=10)
            self.sliders[name] = ent
            row += 1
            
        btn_req = tk.Button(self.req_panel, text="📥 Submit Allocation Request", 
                             **Styles.success_button(), command=self._submit_request)
        btn_req.pack(fill=tk.X, padx=20, pady=15)
        
        btn_rel = tk.Button(self.req_panel, text="📤 Release Resources", 
                             **Styles.danger_button(), command=self._release_resources)
        btn_rel.pack(fill=tk.X, padx=20, pady=5)
        
    def _submit_request(self):
        pid = self.cb_pids.get()
        if not pid:
            messagebox.showwarning("Resource Manager", "Choose a requester Process PID from the dropdown first.")
            return
            
        request = {}
        for name, ent in self.sliders.items():
            try:
                val = int(ent.get())
            except ValueError:
                messagebox.showerror("Invalid Resource Count", f"{name} must be a whole number.")
                self.main_window.show_feedback(f"Invalid count for {name}", "error")
                return
            if val < 0:
                messagebox.showerror("Invalid Resource Count", "Resource counts cannot be negative.")
                self.main_window.show_feedback("Resource counts cannot be negative", "error")
                return
            if val > 0:
                request[name] = val
                
        if not request:
            messagebox.showwarning("Resource Manager", "Enter at least 1 resource request instance count.")
            return
            
        success = self.main_window.resource_mgr.request(pid, request)
        
        # Save resource event to DB
        self.main_window.db_service.save_resource_event({
            "session_id": self.main_window.current_session_id,
            "pid": pid,
            "request": request,
            "success": success
        })
        
        self.update_view()
        if success:
            self.main_window.show_feedback(f"Resources allocated to {pid}", "success")
            messagebox.showinfo("Allocation Success", f"Resources successfully allocated to Process {pid}.")
        else:
            self.main_window.show_feedback(f"Request for {pid} was refused: capacity unavailable", "error")
            messagebox.showerror("Allocation Refused", "Insufficient system resource capacity to fulfill request.")
            
    def _release_resources(self):
        pid = self.cb_pids.get()
        if not pid:
            messagebox.showwarning("Resource Manager", "Choose a process PID to release resources.")
            return
            
        released = self.main_window.resource_mgr.release(pid)
        
        self.main_window.db_service.save_resource_event({
            "session_id": self.main_window.current_session_id,
            "pid": pid,
            "action": "RELEASE",
            "released": released,
            "success": True
        })
        
        self.update_view()
        if released:
            self.main_window.show_feedback(f"Resources released by {pid}", "success")
            messagebox.showinfo("Resources Released", f"Successfully reclaimed resources: {released} from Process {pid}.")
        else:
            self.main_window.show_feedback(f"No resources held by {pid}", "warning")
            messagebox.showinfo("Resource Manager", f"Process {pid} holds no active resource allocations.")
            
    def update_view(self):
        # Update Table list
        self.tree_inv.delete(*self.tree_inv.get_children())
        rows = self.main_window.resource_mgr.get_all_stats()
        for index, stats in enumerate(rows):
            tags = ("alternate",) if index % 2 else ()
            self.tree_inv.insert("", "end", values=(
                stats["name"], stats["total"], stats["available"],
                stats["allocated"], f"{stats['utilization']:.1f}%"
            ), tags=tags)
        Styles.update_empty_state(self.tree_inv, self.empty_table)
            
        # Update PIDs dropdown
        pids = [p.pid for p in self.main_window.process_manager.get_all_active()]
        self.cb_pids['values'] = pids
        if pids:
            self.cb_pids.current(0)
