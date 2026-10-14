"""
D-RTOS: Process Manager View
Displays the process table with process states, threat associations, and
features a detail inspector for inspecting the Process Control Block (PCB).
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from gui.theme import Colors, Fonts, Styles

class ProcessView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="⚙️ OS PROCESS & PCB CONTROL BOARD", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Grid frame for Process Control and inspector
        self.grid_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Left side: Process queue table
        self.table_frame = tk.Frame(self.grid_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_t_hdr = tk.Label(self.table_frame, text="Active Process Queue Status Table", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_t_hdr.pack(anchor="w", padx=10, pady=5)
        
        self.tree = ttk.Treeview(self.table_frame, columns=("pid", "name", "threat", "priority", "deadline", "mem", "state"), 
                                 show="headings", style="Custom.Treeview")
        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="Process")
        self.tree.heading("threat", text="Threat")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("deadline", text="Deadline")
        self.tree.heading("mem", text="Memory")
        self.tree.heading("state", text="State")
        
        self.tree.column("pid", width=60, anchor="center")
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("threat", width=80, anchor="center")
        self.tree.column("priority", width=60, anchor="center")
        self.tree.column("deadline", width=80, anchor="center")
        self.tree.column("mem", width=80, anchor="center")
        self.tree.column("state", width=100, anchor="center")
        
        scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0,10))
        
        # Bind double-click or select event to load detailed inspector
        self.tree.bind("<<TreeviewSelect>>", self._on_select_process)
        
        # Right side: PCB Inspector Panel
        self.inspector_frame = tk.Frame(self.grid_frame, bg=Colors.BG_PANEL, width=400, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.inspector_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.inspector_frame.pack_propagate(False)
        
        lbl_i_hdr = tk.Label(self.inspector_frame, text="PCB BLOCK INSPECTOR", **Styles.label(fg=Colors.ALERT_RED, font=Fonts.TITLE))
        lbl_i_hdr.pack(anchor="w", padx=10, pady=5)
        
        self.txt_pcb = tk.Text(self.inspector_frame, **Styles.text_widget(), wrap=tk.WORD)
        self.txt_pcb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Priority elevation utility
        self.ctrl_frame = tk.Frame(self.inspector_frame, bg=Colors.BG_PANEL)
        self.ctrl_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.btn_elevate = tk.Button(self.ctrl_frame, text="⚡ Elevate Priority (P1)", 
                                     **Styles.success_button(), command=self._elevate_selected)
        self.btn_elevate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.btn_kill = tk.Button(self.ctrl_frame, text="💀 Terminate / Kill", 
                                  **Styles.danger_button(), command=self._kill_selected)
        self.btn_kill.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        
        self.selected_pid = None
        
    def _on_select_process(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if vals:
            self.selected_pid = vals[0]
            self._load_pcb_details(self.selected_pid)
            
    def _load_pcb_details(self, pid: str):
        pcb = self.main_window.process_manager.get_process(pid)
        if not pcb:
            return
            
        details = (
            f"PROCESS CONTROL BLOCK: {pcb.pid}\n"
            f"===================================\n"
            f"Process Name : {pcb.process_name}\n"
            f"Target Ref   : {pcb.object_id}\n"
            f"Current State: {pcb.state.value}\n\n"
            f"--- Scheduling Properties ---\n"
            f"Priority     : {pcb.priority} (1=Max, 4=Min)\n"
            f"Threat Level : {pcb.threat_level.name}\n"
            f"Arrival Time : {pcb.arrival_time:.1f} ticks\n"
            f"Burst Time   : {pcb.burst_time:.1f} ticks\n"
            f"Remaining    : {pcb.remaining_burst:.1f} ticks\n"
            f"Deadline     : {pcb.deadline:.1f} ticks\n"
            f"RT Status    : {pcb.deadline_status}\n\n"
            f"--- RAM & CPU Allocation ---\n"
            f"Memory Req   : {pcb.memory_requirement} MB\n"
            f"Assigned CPU : CPU-{pcb.assigned_cpu if pcb.assigned_cpu is not None else 'N/A'}\n"
            f"Resources Req: {pcb.required_resources}\n\n"
            f"--- Performance Counters ---\n"
            f"Context Sw.  : {pcb.context_switches}\n"
            f"Preemptions  : {pcb.preemption_count}\n"
            f"Page Faults  : {pcb.page_faults}\n"
        )
        self.txt_pcb.config(state=tk.NORMAL)
        self.txt_pcb.delete("1.0", tk.END)
        self.txt_pcb.insert("1.0", details)
        self.txt_pcb.config(state=tk.DISABLED)
        
    def _elevate_selected(self):
        if not self.selected_pid:
            messagebox.showwarning("Process Manager", "Select a process from the queue table first.")
            return
        self.main_window.process_manager.elevate_to_critical(self.selected_pid)
        self._load_pcb_details(self.selected_pid)
        self.update_view()
        
    def _kill_selected(self):
        if not self.selected_pid:
            messagebox.showwarning("Process Manager", "Select a process from the queue table first.")
            return
        pcb = self.main_window.process_manager.get_process(self.selected_pid)
        if pcb:
            self.main_window.process_manager.terminate_process(pcb)
            self.main_window.memory_mgr.deallocate(pcb.pid)
            self.main_window.resource_mgr.release(pcb.pid)
            self.main_window.paging_mgr.deallocate_pages(pcb.pid)
            # Release core assignment
            for cid, active_p in list(self.main_window.multicore_mgr.get_busy_cores()):
                if active_p.pid == pcb.pid:
                    self.main_window.multicore_mgr.release_core(cid)
                    
            self.selected_pid = None
            self.txt_pcb.config(state=tk.NORMAL)
            self.txt_pcb.delete("1.0", tk.END)
            self.txt_pcb.config(state=tk.DISABLED)
            self.update_view()
            messagebox.showinfo("Process Control", f"Process {pcb.pid} terminated and resources reclaimed.")
            
    def update_view(self):
        self.tree.delete(*self.tree.get_children())
        # Populate active (non-terminated) processes
        for p in self.main_window.process_manager.get_all_active():
            self.tree.insert("", "end", values=(
                p.pid, p.process_name, p.threat_level.name,
                p.priority, f"{p.deadline:.1f}" if p.deadline else "None",
                f"{p.memory_requirement} MB", p.state.value
            ))
        if self.selected_pid:
            self._load_pcb_details(self.selected_pid)
