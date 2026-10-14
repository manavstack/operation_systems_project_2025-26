"""
D-RTOS: Process Manager
Manages process lifecycle, queues, state transitions, and dynamic priority.
"""

from __future__ import annotations
import time
import random
from typing import List, Optional, Dict, Callable, Any

from core.process import ProcessState, ThreatLevel, ProcessType, THREAT_PROFILE, next_pid
from core.pcb import PCB


class ProcessManager:
    """
    Central OS process manager responsible for:
    - Creating processes from radar events
    - Managing process queues (new, ready, running, waiting, terminated)
    - Handling state transitions with event hooks
    - Providing dynamic priority adjustment
    """

    def __init__(self):
        self.new_queue: List[PCB] = []
        self.ready_queue: List[PCB] = []
        self.running_processes: Dict[int, Optional[PCB]] = {0: None, 1: None, 2: None, 3: None}
        self.waiting_queue: List[PCB] = []
        self.terminated: List[PCB] = []
        self.all_processes: Dict[str, PCB] = {}

        # Simulation clock
        self.simulation_time: float = 0.0
        self.tick_size: float = 1.0          # 1 tick per unit

        # Event hooks: list of callables notified on state changes
        self._state_change_hooks: List[Callable[[PCB, ProcessState, ProcessState], None]] = []
        self._preemption_hooks: List[Callable[[PCB, PCB, str], None]] = []

        # Preemption log (global)
        self.preemption_log: List[Dict[str, Any]] = []
        self.context_switch_count: int = 0

    # ------------------------------------------------------------------ #
    #  Process Creation                                                     #
    # ------------------------------------------------------------------ #
    def create_process(
        self,
        object_id: str,
        threat_level: ThreatLevel,
        event_id: str = "",
        burst_time: Optional[float] = None,
        deadline: Optional[float] = None,
        memory_requirement: Optional[int] = None,
        required_resources: Optional[Dict[str, int]] = None,
        custom_name: Optional[str] = None,
        arrival_time: Optional[float] = None,
    ) -> PCB:
        """Create a new PCB from a radar event. All parameters are simulated."""
        profile = THREAT_PROFILE[threat_level]
        pid = next_pid()

        if burst_time is None:
            lo, hi = profile["burst_range"]
            burst_time = round(random.uniform(lo, hi), 1)

        if deadline is None:
            lo, hi = profile["deadline_range"]
            abs_deadline = self.simulation_time + random.uniform(lo, hi)
            deadline = round(abs_deadline, 1)

        if memory_requirement is None:
            lo, hi = profile["memory_range"]
            memory_requirement = random.randint(lo, hi)

        if required_resources is None:
            required_resources = self._default_resources(threat_level)

        if custom_name is None:
            custom_name = profile["process_type"].value

        arr = arrival_time if arrival_time is not None else self.simulation_time

        pcb = PCB(
            pid=pid,
            process_name=custom_name,
            object_id=object_id,
            event_id=event_id,
            arrival_time=arr,
            burst_time=burst_time,
            remaining_burst=burst_time,
            priority=profile["priority"],
            threat_level=threat_level,
            deadline=deadline,
            memory_requirement=memory_requirement,
            required_resources=required_resources,
            process_type=profile["process_type"],
        )

        self.all_processes[pid] = pcb
        self.new_queue.append(pcb)
        return pcb

    def _default_resources(self, threat: ThreatLevel) -> Dict[str, int]:
        if threat == ThreatLevel.CRITICAL:
            return {"CPU": 1, "GPU": 1, "Radar Processor": 1}
        elif threat == ThreatLevel.HIGH:
            return {"CPU": 1, "Radar Processor": 1, "Communication Channel": 1}
        elif threat == ThreatLevel.MEDIUM:
            return {"CPU": 1, "Radar Processor": 1}
        else:
            return {"CPU": 1}

    # ------------------------------------------------------------------ #
    #  State Transitions                                                    #
    # ------------------------------------------------------------------ #
    def admit_process(self, pcb: PCB):
        """Transition NEW → READY."""
        if pcb.state == ProcessState.NEW:
            old = pcb.state
            pcb.transition(ProcessState.READY, "Admitted to ready queue")
            self.new_queue = [p for p in self.new_queue if p.pid != pcb.pid]
            self.ready_queue.append(pcb)
            self._notify_state_change(pcb, old, ProcessState.READY)

    def admit_all_new(self):
        """Admit all new processes to ready queue."""
        for p in list(self.new_queue):
            self.admit_process(p)

    def start_process(self, pcb: PCB, cpu_id: int):
        """Transition READY → RUNNING on a specific CPU."""
        if pcb.state in (ProcessState.READY, ProcessState.WAITING):
            old = pcb.state
            pcb.transition(ProcessState.RUNNING, f"Assigned to CPU-{cpu_id}")
            pcb.assigned_cpu = cpu_id
            if pcb.start_time is None:
                pcb.start_time = self.simulation_time
            self.ready_queue = [p for p in self.ready_queue if p.pid != pcb.pid]
            self.waiting_queue = [p for p in self.waiting_queue if p.pid != pcb.pid]
            self.running_processes[cpu_id] = pcb
            self._notify_state_change(pcb, old, ProcessState.RUNNING)

    def preempt_process(self, running_pcb: PCB, new_pcb: PCB, reason: str, cpu_id: int):
        """Preempt RUNNING → READY and start new process."""
        if running_pcb.state == ProcessState.RUNNING:
            old = running_pcb.state
            running_pcb.transition(ProcessState.READY, f"Preempted by {new_pcb.pid}")
            running_pcb.preemption_count += 1
            running_pcb.context_switches += 1
            self.context_switch_count += 1
            self.running_processes[cpu_id] = None
            self.ready_queue.append(running_pcb)

            entry = {
                "preempted_pid": running_pcb.pid,
                "preempted_name": running_pcb.process_name,
                "new_pid": new_pcb.pid,
                "new_name": new_pcb.process_name,
                "reason": reason,
                "simulation_time": self.simulation_time,
                "cpu_id": cpu_id,
            }
            self.preemption_log.append(entry)
            running_pcb.log_preemption(new_pcb.pid, reason, self.simulation_time)

            for hook in self._preemption_hooks:
                hook(running_pcb, new_pcb, reason)

            self._notify_state_change(running_pcb, old, ProcessState.READY)

    def block_process(self, pcb: PCB, reason: str = "I/O"):
        """Transition RUNNING → WAITING."""
        if pcb.state == ProcessState.RUNNING:
            old = pcb.state
            cpu = pcb.assigned_cpu
            pcb.transition(ProcessState.WAITING, reason)
            if cpu is not None:
                self.running_processes[cpu] = None
            self.waiting_queue.append(pcb)
            self._notify_state_change(pcb, old, ProcessState.WAITING)

    def unblock_process(self, pcb: PCB):
        """Transition WAITING → READY."""
        if pcb.state == ProcessState.WAITING:
            old = pcb.state
            pcb.transition(ProcessState.READY, "I/O or wait complete")
            self.waiting_queue = [p for p in self.waiting_queue if p.pid != pcb.pid]
            self.ready_queue.append(pcb)
            self._notify_state_change(pcb, old, ProcessState.READY)

    def terminate_process(self, pcb: PCB, simulation_time: Optional[float] = None):
        """Transition RUNNING → TERMINATED."""
        if pcb.state in (ProcessState.RUNNING, ProcessState.READY, ProcessState.WAITING):
            old = pcb.state
            pcb.transition(ProcessState.TERMINATED, "Execution complete")
            t = simulation_time if simulation_time is not None else self.simulation_time
            pcb.completion_time = t
            pcb.turnaround_time = t - pcb.arrival_time
            pcb.waiting_time = pcb.turnaround_time - pcb.burst_time
            if pcb.waiting_time < 0:
                pcb.waiting_time = 0.0
            pcb.update_deadline_status(t)
            cpu = pcb.assigned_cpu
            if cpu is not None and self.running_processes.get(cpu) is pcb:
                self.running_processes[cpu] = None
            self.ready_queue = [p for p in self.ready_queue if p.pid != pcb.pid]
            self.waiting_queue = [p for p in self.waiting_queue if p.pid != pcb.pid]
            self.terminated.append(pcb)
            self._notify_state_change(pcb, old, ProcessState.TERMINATED)

    # ------------------------------------------------------------------ #
    #  Dynamic Priority                                                     #
    # ------------------------------------------------------------------ #
    def update_priority(self, pid: str, new_priority: int, reason: str = ""):
        """Dynamically change a process's priority."""
        pcb = self.all_processes.get(pid)
        if pcb and pcb.state != ProcessState.TERMINATED:
            pcb.priority = max(1, min(4, new_priority))
            pcb.state_history.append({
                "action": "PRIORITY_CHANGE",
                "new_priority": new_priority,
                "reason": reason,
                "timestamp": time.time(),
            })

    def elevate_to_critical(self, pid: str):
        self.update_priority(pid, 1, "Elevated to critical threat")

    # ------------------------------------------------------------------ #
    #  Queries                                                              #
    # ------------------------------------------------------------------ #
    def get_all_active(self) -> List[PCB]:
        result = []
        result.extend(self.new_queue)
        result.extend(self.ready_queue)
        result.extend(self.waiting_queue)
        for p in self.running_processes.values():
            if p:
                result.append(p)
        return result

    def get_process(self, pid: str) -> Optional[PCB]:
        return self.all_processes.get(pid)

    def counts(self) -> Dict[str, int]:
        running = sum(1 for p in self.running_processes.values() if p)
        return {
            "new": len(self.new_queue),
            "ready": len(self.ready_queue),
            "running": running,
            "waiting": len(self.waiting_queue),
            "terminated": len(self.terminated),
            "total": len(self.all_processes),
        }

    # ------------------------------------------------------------------ #
    #  Hooks                                                                #
    # ------------------------------------------------------------------ #
    def on_state_change(self, hook: Callable):
        self._state_change_hooks.append(hook)

    def on_preemption(self, hook: Callable):
        self._preemption_hooks.append(hook)

    def _notify_state_change(self, pcb: PCB, old: ProcessState, new: ProcessState):
        for hook in self._state_change_hooks:
            try:
                hook(pcb, old, new)
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    #  Reset                                                               #
    # ------------------------------------------------------------------ #
    def reset(self):
        from core.process import reset_pid_counter
        reset_pid_counter()
        self.new_queue.clear()
        self.ready_queue.clear()
        self.waiting_queue.clear()
        self.terminated.clear()
        self.all_processes.clear()
        self.running_processes = {0: None, 1: None, 2: None, 3: None}
        self.simulation_time = 0.0
        self.context_switch_count = 0
        self.preemption_log.clear()
