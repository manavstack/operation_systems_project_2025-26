"""
D-RTOS: Synchronization View
Simulates Mutex and Counting Semaphore locking constraints on the
shared Radar Data Buffer. Includes a race condition demonstrator.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import time

from gui.theme import Colors, Fonts, Styles

class SynchronizationView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self.main_window.sync_mgr.radar_buffer.on_change(lambda rb: self.update_view())
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="🔄 PROCESS SYNCHRONIZATION MONITOR", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Grid layout splitting buffer monitor and lock simulator
        self.split_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left Panel: Shared Resource (Radar Data Buffer status)
        self.buffer_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.buffer_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_b = tk.Label(self.buffer_panel, text="Shared Resource: RADAR DATA BUFFER", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_b.pack(anchor="w", padx=10, pady=5)
        
        # Buffer Display Text
        self.lbl_buf_data = tk.Label(self.buffer_panel, text="Buffer Data: [EMPTY]", 
                                     bg=Colors.BG_DEEP, fg=Colors.RADAR_GREEN, font=Fonts.MONO_LG, height=3, relief="solid", bd=1)
        self.lbl_buf_data.pack(fill=tk.X, padx=15, pady=10)
        
        # Stats & status
        self.lbl_buf_stats = tk.Label(self.buffer_panel, text="Status: UNLOCKED\nReads: 0  |  Writes: 0", 
                                      **Styles.label(fg=Colors.TEXT_SECONDARY, font=Fonts.MONO_MD))
        self.lbl_buf_stats.pack(pady=10)
        
        # Competition list
        self.lbl_waiting = tk.Label(self.buffer_panel, text="Waiting Queue: None", 
                                    **Styles.label(fg=Colors.AMBER_WARN, font=Fonts.MONO_MD))
        self.lbl_waiting.pack(pady=10)
        
        # Right Panel: Mutex / Semaphore Lock Simulation
        self.lock_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, width=480, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.lock_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.lock_panel.pack_propagate(False)
        
        lbl_l = tk.Label(self.lock_panel, text="Lock Primitive & Race Simulator", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_l.pack(anchor="w", padx=10, pady=5)
        
        # Sync type radio selections
        frm_type = tk.Frame(self.lock_panel, bg=Colors.BG_PANEL)
        frm_type.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(frm_type, text="Synchronization Type:", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(anchor="w")
        
        self.sync_type_var = tk.StringVar(value="MUTEX")
        ttk.Radiobutton(frm_type, text="Mutex Lock Protection", variable=self.sync_type_var, value="MUTEX", 
                        command=self._change_sync_type).pack(anchor="w", pady=2)
        ttk.Radiobutton(frm_type, text="Counting Semaphore Protection", variable=self.sync_type_var, value="SEMAPHORE",
                        command=self._change_sync_type).pack(anchor="w", pady=2)
        ttk.Radiobutton(frm_type, text="None (Disable Sync / Race Condition)", variable=self.sync_type_var, value="NONE",
                        command=self._change_sync_type).pack(anchor="w", pady=2)
        
        # Competitors PIDs
        frm_pids = tk.Frame(self.lock_panel, bg=Colors.BG_PANEL)
        frm_pids.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frm_pids, text="Competitor PID:", **Styles.label(fg=Colors.TEXT_SECONDARY)).pack(side=tk.LEFT, padx=5)
        self.cb_pids = ttk.Combobox(frm_pids, state="readonly")
        self.cb_pids.pack(side=tk.LEFT, padx=5)
        
        btn_acq = tk.Button(self.lock_panel, text="🔒 Request Buffer Access", 
                             **Styles.success_button(), command=self._acquire_access)
        btn_acq.pack(fill=tk.X, padx=20, pady=10)
        
        btn_write = tk.Button(self.lock_panel, text="📝 Write Radar Update", 
                               **Styles.button(), command=self._write_buffer)
        btn_write.pack(fill=tk.X, padx=20, pady=5)
        
        btn_rel = tk.Button(self.lock_panel, text="🔓 Release Buffer Access", 
                             **Styles.danger_button(), command=self._release_access)
        btn_rel.pack(fill=tk.X, padx=20, pady=10)
        
    def _change_sync_type(self):
        st = self.sync_type_var.get()
        self.main_window.sync_mgr.radar_buffer.sync_type = st
        self.main_window.sync_mgr.radar_buffer.sync_enabled = (st != "NONE")
        self.update_view()
        
    def _acquire_access(self):
        pid = self.cb_pids.get()
        if not pid:
            messagebox.showwarning("Sync Control", "Choose a competitor PID from the dropdown first.")
            return
            
        success = self.main_window.sync_mgr.radar_buffer.acquire_access(pid)
        
        # Save synchronization event to DB
        self.main_window.db_service.save_sync_event({
            "session_id": self.main_window.current_session_id,
            "pid": pid,
            "action": "ACQUIRE",
            "sync_type": self.sync_type_var.get(),
            "granted": success
        })
        
        self.update_view()
        if success:
            messagebox.showinfo("Sync Success", f"Process {pid} successfully acquired buffer lock access.")
        else:
            messagebox.showwarning("Lock Contention", f"Lock busy! Process {pid} added to buffer waiting queue.")
            
    def _write_buffer(self):
        pid = self.cb_pids.get()
        if not pid:
            messagebox.showwarning("Sync Control", "Choose a competitor PID.")
            return
            
        data = f"TARGET_TRACK_UPDATE_BY_{pid}"
        res = self.main_window.sync_mgr.radar_buffer.write(pid, data, 
                                                            protected=(self.sync_type_var.get() != "NONE"))
        
        self.main_window.db_service.save_sync_event({
            "session_id": self.main_window.current_session_id,
            "pid": pid,
            "action": "WRITE",
            "data": data,
            "success": res.get("success", False),
            "corrupted": res.get("corrupted", False)
        })
        
        self.update_view()
        if res.get("success"):
            messagebox.showinfo("Buffer Write", f"Buffer updated with data: {data}")
        elif res.get("corrupted"):
            messagebox.showerror("Race Condition Alert", "DATA CORRUPTED! Simultaneous concurrent write race condition detected.")
        else:
            messagebox.showerror("Access Denied", "Process must acquire lock access before writing to resource.")
            
    def _release_access(self):
        pid = self.cb_pids.get()
        if not pid:
            messagebox.showwarning("Sync Control", "Choose a competitor PID.")
            return
            
        next_pid = self.main_window.sync_mgr.radar_buffer.release_access(pid)
        
        self.main_window.db_service.save_sync_event({
            "session_id": self.main_window.current_session_id,
            "pid": pid,
            "action": "RELEASE",
            "next_pid": next_pid
        })
        
        self.update_view()
        msg = f"Buffer access released by {pid}."
        if next_pid:
            msg += f"\nLock passed to next in queue: Process {next_pid}."
        messagebox.showinfo("Buffer Released", msg)
        
    def update_view(self):
        # Update PIDs dropdown
        pids = [p.pid for p in self.main_window.process_manager.get_all_active()]
        self.cb_pids['values'] = pids
        if pids and not self.cb_pids.get():
            self.cb_pids.current(0)
            
        # Update buffer details
        rb = self.main_window.sync_mgr.radar_buffer
        self.lbl_buf_data.configure(text=f"Buffer Data: {rb.buffer_data}")
        
        state = rb.get_state()
        lock = state["lock_state"]
        
        # Color coding buffer data if corrupted
        if "CORRUPTED" in rb.buffer_data:
            self.lbl_buf_data.configure(fg=Colors.ALERT_RED)
        else:
            self.lbl_buf_data.configure(fg=Colors.RADAR_GREEN)
            
        st_type = rb.sync_type
        if st_type == "NONE":
            lbl_status_str = f"Status: UNPROTECTED\nWrites: {rb.write_count}  |  Reads: {rb.read_count}\nRace Corruptions: {state['corruption_events']}"
            lbl_wait_str = "Waiting Queue: N/A"
        elif st_type == "MUTEX":
            owner = lock.get("owner")
            lbl_status_str = f"Status: {'LOCKED (Owner: ' + owner + ')' if owner else 'UNLOCKED'}\nWrites: {rb.write_count}  |  Reads: {rb.read_count}"
            lbl_wait_str = f"Waiting Queue: {', '.join(lock.get('waiting', [])) or 'None'}"
        else: # SEMAPHORE
            holders = lock.get("holders", [])
            lbl_status_str = f"Status: SEMAPHORE (Available slots: {lock.get('count')})\nHolders: {', '.join(holders) or 'None'}\nWrites: {rb.write_count}"
            lbl_wait_str = f"Waiting Queue: {', '.join(lock.get('waiting', [])) or 'None'}"
            
        self.lbl_buf_stats.configure(text=lbl_status_str)
        self.lbl_waiting.configure(text=lbl_wait_str)
        self.sync_type_var.set(st_type)
