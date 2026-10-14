"""
D-RTOS: Deadlock & Banker View
Displays Resource Allocation Graphs (RAG) cycle status, and evaluates
deadlock avoidance parameters using the Banker's Algorithm safety check.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from gui.theme import Colors, Fonts, Styles

class DeadlockView(tk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent, bg=Colors.BG_DEEP)
        self.main_window = main_window
        self._build_ui()
        
    def _build_ui(self):
        lbl_title = tk.Label(self, text="🔒 DEADLOCK DETECTION & BANKER'S SAFETY STATION", **Styles.header_label())
        lbl_title.pack(anchor="w", padx=15, pady=10)
        
        # Grid frame split into deadlock cycle checker and banker's matrices
        self.split_frame = tk.Frame(self, bg=Colors.BG_DEEP)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left Panel: Deadlock Detection (Cycle Visualizer)
        self.deadlock_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.deadlock_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        lbl_d = tk.Label(self.deadlock_panel, text="Resource Allocation Graph (RAG) Cycle Status", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_d.pack(anchor="w", padx=10, pady=5)
        
        self.btn_run_rag = tk.Button(self.deadlock_panel, text="🔍 Scan RAG for Circular Cycles", 
                                     **Styles.button(), command=self._scan_rag_cycles)
        self.btn_run_rag.pack(fill=tk.X, padx=15, pady=10)
        
        self.btn_demo_deadlock = tk.Button(self.deadlock_panel, text="⚠️ Inject Circular Deadlock Scenario", 
                                          **Styles.danger_button(), command=self._inject_circular_deadlock)
        self.btn_demo_deadlock.pack(fill=tk.X, padx=15, pady=5)
        
        self.txt_rag = tk.Text(self.deadlock_panel, **Styles.text_widget(), wrap=tk.WORD, height=12)
        self.txt_rag.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Right Panel: Banker's Algorithm Matrix grid & safety check
        self.banker_panel = tk.Frame(self.split_frame, bg=Colors.BG_PANEL, width=540, bd=1, relief="solid", highlightbackground=Colors.BORDER)
        self.banker_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.banker_panel.pack_propagate(False)
        
        lbl_b = tk.Label(self.banker_panel, text="Banker's Algorithm Safety Monitor", **Styles.label(fg=Colors.HUD_CYAN, font=Fonts.TITLE))
        lbl_b.pack(anchor="w", padx=10, pady=5)
        
        # Matrix summary text
        self.txt_banker = tk.Text(self.banker_panel, **Styles.text_widget(), wrap=tk.WORD, height=15)
        self.txt_banker.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Action Buttons
        self.btn_bankers_demo = tk.Button(self.banker_panel, text="⚡ Load Banker's Demo State", 
                                           **Styles.button(), command=self._load_bankers_demo)
        self.btn_bankers_demo.pack(fill=tk.X, padx=20, pady=5)
        
        self.btn_run_banker = tk.Button(self.banker_panel, text="⚖️ Run Bankers Safety Evaluation", 
                                         **Styles.success_button(), command=self._evaluate_safety)
        self.btn_run_banker.pack(fill=tk.X, padx=20, pady=10)
        
    def _scan_rag_cycles(self):
        # Sync RAG edges with Resource Manager & Process ready/waiting queue allocations
        waiting = {}
        for p in self.main_window.process_manager.waiting_queue:
            waiting[p.pid] = p.required_resources
            
        allocation = self.main_window.resource_mgr.get_allocation_table()
        self.main_window.deadlock_det.sync_from_resource_manager(allocation, waiting)
        
        has_deadlock, cycles = self.main_window.deadlock_det.detect_cycle()
        desc = self.main_window.deadlock_det.describe_deadlock(cycles)
        
        self.main_window.db_service.save_deadlock_event({
            "session_id": self.main_window.current_session_id,
            "has_deadlock": has_deadlock,
            "cycles": cycles
        })
        
        self.txt_rag.config(state=tk.NORMAL)
        self.txt_rag.delete("1.0", tk.END)
        self.txt_rag.insert("1.0", desc if has_deadlock else "🔍 SCAN COMPLETE: NO CIRCULAR CYCLES DETECTED IN RAG.\nSystem resources are allocated safely.")
        self.txt_rag.config(state=tk.DISABLED)
        
    def _inject_circular_deadlock(self):
        self.main_window.deadlock_det.build_scenario("classic")
        has_deadlock, cycles = self.main_window.deadlock_det.detect_cycle()
        desc = self.main_window.deadlock_det.describe_deadlock(cycles)
        
        self.txt_rag.config(state=tk.NORMAL)
        self.txt_rag.delete("1.0", tk.END)
        self.txt_rag.insert("1.0", desc)
        self.txt_rag.config(state=tk.DISABLED)
        messagebox.showwarning("Deadlock Injected", "Predefined circular resource wait (P1->GPU->P2->Comm->P3->CPU->P1) successfully loaded into RAG graph.")
        
    def _load_bankers_demo(self):
        state = self.main_window.banker_algo.build_demo_state("drtos")
        self._render_bankers_matrix(state)
        messagebox.showinfo("Banker's Load", "D-RTOS themed bankers resource state matrices successfully set up.")
        
    def _render_bankers_matrix(self, state):
        need = state.need_matrix
        m_str = (
            f"RESOURCES IN PLAY: {', '.join(state.resources)}\n"
            f"AVAILABLE VECTOR : {state.available}\n\n"
            f"PROCESS MATRIX DEFINITIONS:\n"
            f"----------------------------------------------------\n"
            f"PID  |  ALLOCATED    |  MAX DEMAND   |  NEED MATRIX\n"
            f"----------------------------------------------------\n"
        )
        for idx, pid in enumerate(state.processes):
            m_str += f"{pid:<4} |  {state.allocation[idx]}    |  {state.max_matrix[idx]}    |  {need[idx]}\n"
            
        self.txt_banker.config(state=tk.NORMAL)
        self.txt_banker.delete("1.0", tk.END)
        self.txt_banker.insert("1.0", m_str)
        self.txt_banker.config(state=tk.DISABLED)
        
    def _evaluate_safety(self):
        if not self.main_window.banker_algo.state:
            messagebox.showwarning("Banker's Algorithm", "Setup or Load a Bankers Demo State matrices first.")
            return
            
        res = self.main_window.banker_algo.is_safe()
        
        self.main_window.db_service.save_deadlock_event({
            "session_id": self.main_window.current_session_id,
            "algorithm": "BANKERS",
            "is_safe": res.is_safe,
            "safe_sequence": res.safe_sequence,
            "reason": res.reason
        })
        
        steps_str = "\n\nEvaluation Steps Traced:\n"
        for idx, step in enumerate(res.steps):
            steps_str += f"Step {idx+1}: Process {step['process']} executes to completion. Work vector becomes {step['work_after']}\n"
            
        self.txt_banker.config(state=tk.NORMAL)
        self.txt_banker.insert(tk.END, f"\n====================================\n"
                                        f"EVALUATION RESULT: {'SAFE STATE' if res.is_safe else 'UNSAFE STATE'}\n"
                                        f"{res.reason}{steps_str}")
        self.txt_banker.config(state=tk.DISABLED)
        
        if res.is_safe:
            messagebox.showinfo("Banker's Safety Check", f"SAFE STATE: Safe sequence found -> {' -> '.join(res.safe_sequence)}")
        else:
            messagebox.showerror("Banker's Safety Check", "UNSAFE STATE DETECTED! Deadlock possible. Allocations must be restricted.")
            
    def update_view(self):
        if self.main_window.banker_algo.state:
            self._render_bankers_matrix(self.main_window.banker_algo.state)
        else:
            self.txt_banker.config(state=tk.NORMAL)
            self.txt_banker.delete("1.0", tk.END)
            self.txt_banker.insert("1.0", "No active Bankers matrices loaded. Click 'Load Banker's Demo State' to initialize.")
            self.txt_banker.config(state=tk.DISABLED)
        self._scan_rag_cycles()
        
    def reset(self):
        self.update_view()
