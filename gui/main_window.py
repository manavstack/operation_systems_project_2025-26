"""
D-RTOS: Main Window
The central dashboard controller managing navigation, status bar, and page transitions.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading

from gui.theme import Colors, Fonts, Styles, apply_dark_titlebar
from gui.dashboard import DashboardView
from gui.radar_view import RadarView
from gui.process_view import ProcessView
from gui.scheduler_view import SchedulerView
from gui.realtime_view import RealTimeView
from gui.multicore_view import MultiCoreView
from gui.memory_view import MemoryView
from gui.paging_view import PagingView
from gui.resource_view import ResourceView
from gui.deadlock_view import DeadlockView
from gui.synchronization_view import SynchronizationView
from gui.analytics_view import AnalyticsView
from gui.history_view import HistoryView
from gui.scenario_view import ScenarioView
from gui.settings_view import SettingsView

class MainWindow:
    """Main window coordinating navigation, system clock ticks, and views."""
    def __init__(self, root, simulator, process_manager, scheduler,
                 realtime_sched, multicore_mgr, memory_mgr, paging_mgr,
                 resource_mgr, deadlock_det, banker_algo, sync_mgr,
                 perf_mgr, db_service):
        self.root = root
        self.root.title("D-RTOS — Defense Radar Real-Time Operating System Simulator")
        self.root.geometry("1280x800")
        self.root.minsize(1050, 680)
        self.root.configure(bg=Colors.BG_DEEP)
        self.root.bind_all("<Control-k>", self._focus_navigation_search)
        self.root.bind_all("<Escape>", self._clear_navigation_search)
        
        apply_dark_titlebar(self.root)
        
        # OS Engines reference
        self.simulator = simulator
        self.process_manager = process_manager
        self.scheduler = scheduler
        self.realtime_sched = realtime_sched
        self.multicore_mgr = multicore_mgr
        self.memory_mgr = memory_mgr
        self.paging_mgr = paging_mgr
        self.resource_mgr = resource_mgr
        self.deadlock_det = deadlock_det
        self.banker_algo = banker_algo
        self.sync_mgr = sync_mgr
        self.perf_mgr = perf_mgr
        self.db_service = db_service
        
        # State
        self.current_session_id = self.db_service.create_session()
        self.simulation_tick_rate = 1.0  # seconds per tick
        self.tick_counter = 0
        self.is_running = True
        
        # Layout Setup
        self._setup_style()
        self._build_layout()
        self._load_views()
        self.show_view("Dashboard")
        
        # Start main tick loop
        self._tick_loop()
        
    def _setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        Styles.treeview_style(self.style)
        self.root.bind_class("Button", "<Enter>", self._button_hover, add="+")
        self.root.bind_class("Button", "<Leave>", self._button_unhover, add="+")

    @staticmethod
    def _button_hover(event):
        button = event.widget
        if button.cget("state") == tk.DISABLED:
            return
        button._resting_background = button.cget("bg")
        button.configure(bg=button.cget("activebackground"))

    @staticmethod
    def _button_unhover(event):
        button = event.widget
        resting = getattr(button, "_resting_background", None)
        if resting is not None:
            button.configure(bg=resting)
        
    def _build_layout(self):
        # 1. Header Bar
        self.header = tk.Frame(self.root, bg=Colors.BG_HEADER, height=58)
        self.header.pack(side=tk.TOP, fill=tk.X)
        self.header.pack_propagate(False)
        
        lbl_title = tk.Label(self.header, text="🛡️ D-RTOS COMMAND CENTER",
                             fg=Colors.HUD_CYAN, bg=Colors.BG_HEADER,
                             font=Fonts.HEADER)
        lbl_title.pack(side=tk.LEFT, padx=15, pady=5)

        self.lbl_current_view = tk.Label(self.header, text="DASHBOARD",
                                          fg=Colors.TEXT_SECONDARY, bg=Colors.BG_HEADER,
                                          font=Fonts.LABEL_SM)
        self.lbl_current_view.pack(side=tk.RIGHT, padx=(12, 18), pady=10)
        
        self.lbl_session = tk.Label(self.header, text=f"SESSION: {self.current_session_id}",
                                     fg=Colors.TEXT_SECONDARY, bg=Colors.BG_HEADER,
                                     font=Fonts.MONO_MD)
        self.lbl_session.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # 2. Main Content Frame (Sidebar + Viewport)
        self.container = tk.Frame(self.root, bg=Colors.BG_DEEP)
        self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.sidebar = tk.Frame(self.container, bg=Colors.BG_SIDEBAR, width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        self.viewport = tk.Frame(self.container, bg=Colors.BG_DEEP)
        self.viewport.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 3. Status Bar
        self.statusbar = tk.Frame(self.root, bg=Colors.BG_SIDEBAR, height=30)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbar.pack_propagate(False)
        
        self.lbl_status = tk.Label(self.statusbar, text="SYSTEM ONLINE  •  SIM 0.0s  •  TICK 0000",
                                    fg=Colors.RADAR_GREEN, bg=Colors.BG_SIDEBAR,
                                     font=Fonts.MONO_SM)
        self.lbl_status.pack(side=tk.LEFT, padx=10)
        
        self.lbl_db_status = tk.Label(self.statusbar, text=f"DATABASE: {self.db_service.status}",
                                       fg=Colors.HUD_CYAN if self.db_service.connected else Colors.AMBER_WARN,
                                       bg=Colors.BG_SIDEBAR, font=Fonts.MONO_SM)
        self.lbl_db_status.pack(side=tk.RIGHT, padx=10)
        
        # Sidebar navigation
        tk.Label(self.sidebar, text="NAVIGATION", anchor="w",
                 fg=Colors.TEXT_DIM, bg=Colors.BG_SIDEBAR,
                 font=Fonts.LABEL_SM).pack(fill=tk.X, padx=12, pady=(14, 5))

        self._navigation_items = []
        self.navigation_query = tk.StringVar()
        self.navigation_search = tk.Entry(
            self.sidebar, textvariable=self.navigation_query,
            **Styles.entry()
        )
        self.navigation_search.pack(fill=tk.X, padx=8, pady=(0, 8), ipady=4)
        self.navigation_search.insert(0, "Search views…")
        self.navigation_search.configure(fg=Colors.TEXT_DIM)
        self.navigation_search.bind("<FocusIn>", self._clear_search_hint)
        self.navigation_search.bind("<FocusOut>", self._restore_search_hint)
        self.navigation_query.trace_add("write", self._filter_navigation)

        self.nav_list = tk.Frame(self.sidebar, bg=Colors.BG_SIDEBAR)
        self.nav_list.pack(fill=tk.BOTH, expand=True)

        # Sidebar Menu Buttons
        self.menu_buttons: dict[str, tk.Button] = {}
        menu_items = [
            ("Dashboard", "📊 Dashboard"),
            ("Radar Simulation", "📡 Radar Scope"),
            ("Process Manager", "⚙️ Process Control"),
            ("CPU Scheduler", "🎛️ CPU Scheduling"),
            ("Real-Time Scheduler", "⏰ Real-Time Monitor"),
            ("Multi-Core", "🧠 Multi-Core Util"),
            ("Memory Manager", "💾 Memory Alloc"),
            ("Paging", "📖 Virtual Memory"),
            ("Resource Manager", "🛠️ Resources"),
            ("Deadlock / Banker", "🔒 Deadlock Avoidance"),
            ("Synchronization", "🔄 Synchronization"),
            ("Performance", "📈 Performance"),
            ("Simulation History", "📜 DB Session History"),
            ("Scenario Runner", "🎮 Scenario Runner"),
            ("Settings", "🔧 Config Settings")
        ]
        
        for row, (view_name, display_text) in enumerate(menu_items):
            btn = tk.Button(self.nav_list, text=display_text, anchor="w",
                            command=lambda name=view_name: self.show_view(name),
                            **Styles.button(bg=Colors.BG_SIDEBAR, fg=Colors.TEXT_SECONDARY))
            btn.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
            self.menu_buttons[view_name] = btn
            self._navigation_items.append((view_name, display_text, btn, row))
        self.nav_list.grid_columnconfigure(0, weight=1)
        self._filter_navigation()

    def _focus_navigation_search(self, _event=None):
        self.navigation_search.focus_set()
        return "break"

    def _clear_search_hint(self, _event=None):
        if self.navigation_search.get() == "Search views…":
            self.navigation_search.delete(0, tk.END)
            self.navigation_search.configure(fg=Colors.TEXT_PRIMARY)

    def _restore_search_hint(self, _event=None):
        if not self.navigation_search.get():
            self.navigation_search.insert(0, "Search views…")
            self.navigation_search.configure(fg=Colors.TEXT_DIM)

    def _clear_navigation_search(self, _event=None):
        if self.root.focus_get() == self.navigation_search:
            self.navigation_search.delete(0, tk.END)
            self.navigation_search.configure(fg=Colors.TEXT_PRIMARY)
            self.navigation_search.focus_set()
            return "break"

    def _filter_navigation(self, *_args):
        query = self.navigation_query.get().strip().lower()
        if query == "search views…":
            query = ""
        for view_name, display_text, button, row in self._navigation_items:
            if query in view_name.lower() or query in display_text.lower():
                button.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
            else:
                button.grid_remove()
            
    def _load_views(self):
        self.views = {
            "Dashboard": DashboardView(self.viewport, self),
            "Radar Simulation": RadarView(self.viewport, self),
            "Process Manager": ProcessView(self.viewport, self),
            "CPU Scheduler": SchedulerView(self.viewport, self),
            "Real-Time Scheduler": RealTimeView(self.viewport, self),
            "Multi-Core": MultiCoreView(self.viewport, self),
            "Memory Manager": MemoryView(self.viewport, self),
            "Paging": PagingView(self.viewport, self),
            "Resource Manager": ResourceView(self.viewport, self),
            "Deadlock / Banker": DeadlockView(self.viewport, self),
            "Synchronization": SynchronizationView(self.viewport, self),
            "Performance": AnalyticsView(self.viewport, self),
            "Simulation History": HistoryView(self.viewport, self),
            "Scenario Runner": ScenarioView(self.viewport, self),
            "Settings": SettingsView(self.viewport, self)
        }
        
    def show_view(self, name: str):
        self.lbl_current_view.configure(text=name.upper())
        for view_name, view_obj in self.views.items():
            if view_name == name:
                view_obj.pack(fill=tk.BOTH, expand=True)
                view_obj.update_view()
                self.menu_buttons[view_name].configure(bg=Colors.BG_HOVER, fg=Colors.HUD_CYAN)
            else:
                view_obj.pack_forget()
                self.menu_buttons[view_name].configure(bg=Colors.BG_SIDEBAR, fg=Colors.TEXT_SECONDARY)
                
    def _tick_loop(self):
        """Simulates periodic OS interrupts, ticks cores, updates views."""
        if not self.is_running:
            return
        
        # Advance multicore simulator by 1 tick
        self.multicore_mgr.tick(1.0)
        self.tick_counter += 1
        self.lbl_status.configure(
            text=f"SYSTEM ONLINE  •  SIM {self.multicore_mgr.simulation_time:.1f}s  •  TICK {self.tick_counter:04d}"
        )
        self.lbl_db_status.configure(
            text=f"DATABASE: {self.db_service.status}",
            fg=Colors.HUD_CYAN if self.db_service.connected else Colors.AMBER_WARN
        )
        
        # Core CPU utilization & metric calculation
        active_processes = self.process_manager.get_all_active()
        self.realtime_sched.update(active_processes, self.multicore_mgr.simulation_time)
        
        # Clean finished running processes from cores
        for core_id, pcb in list(self.multicore_mgr.get_busy_cores()):
            if pcb.remaining_burst <= 0:
                self.multicore_mgr.release_core(core_id)
                self.process_manager.terminate_process(pcb, self.multicore_mgr.simulation_time)
                self.realtime_sched.finalize_process(pcb, self.multicore_mgr.simulation_time)
                self.memory_mgr.deallocate(pcb.pid)
                self.paging_mgr.deallocate_pages(pcb.pid)
                self.resource_mgr.release(pcb.pid)
                self.db_service.save_process(pcb.to_dict())
                
        # Populate scheduler queue automatically if in running mode
        # (Dispatch waiting to ready or running based on core availability)
        idle_cores = self.multicore_mgr.get_idle_cores()
        for core_id in idle_cores:
            if self.process_manager.ready_queue:
                # Assign based on EDF if real-time, otherwise Priority or FCFS
                next_p = self.realtime_sched.next_to_run(self.process_manager.ready_queue)
                if next_p:
                    self.process_manager.start_process(next_p, core_id)
                    self.multicore_mgr.assign_to_core(next_p, core_id)
                    
        # Periodic DB logging of system metrics
        if self.tick_counter % 5 == 0:
            cpu_utils = [c.utilization for c in self.multicore_mgr.cores]
            mem_util = self.memory_mgr.utilization
            ready_len = len(self.process_manager.ready_queue)
            wait_len = len(self.process_manager.waiting_queue)
            running_len = sum(1 for c in self.multicore_mgr.cores if not c.is_idle)
            counts = {
                "active": len(active_processes),
                "ready": ready_len,
                "waiting": wait_len,
                "running": running_len,
                "terminated": len(self.process_manager.terminated)
            }
            snapshot = self.perf_mgr.take_snapshot(
                sim_time=self.multicore_mgr.simulation_time,
                cpu_utils=cpu_utils,
                memory_util=mem_util,
                process_counts=counts,
                deadline_rate=self.realtime_sched.success_rate,
                context_switches=self.process_manager.context_switch_count,
                page_faults=self.paging_mgr.page_fault_count
            )
            self.db_service.save_system_metrics({
                "session_id": self.current_session_id,
                **snapshot.to_dict()
            })
            
        # Update currently active view dynamically
        for view_name, btn in self.menu_buttons.items():
            if btn.cget("bg") == Colors.BG_HOVER:
                self.views[view_name].update_view()
                
        # Schedule next tick
        self.root.after(int(self.simulation_tick_rate * 1000), self._tick_loop)
        
    def reset_simulation(self):
        self.simulator.reset()
        self.process_manager.reset()
        self.realtime_sched.reset()
        self.multicore_mgr.reset()
        self.memory_mgr.reset()
        self.paging_mgr.reset()
        self.resource_mgr.reset()
        self.deadlock_det.reset()
        self.banker_algo.reset()
        self.sync_mgr.reset()
        self.perf_mgr.reset()
        self.current_session_id = self.db_service.create_session()
        self.lbl_session.configure(text=f"SESSION: {self.current_session_id}")
        messagebox.showinfo("D-RTOS", "Simulation state has been fully reset. New session started.")
        self.show_view("Dashboard")
        
    def on_closing(self):
        self.is_running = False
        stats = self.perf_mgr.get_final_stats()
        self.db_service.close_session(self.current_session_id, stats)
        self.root.destroy()
