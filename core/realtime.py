"""
D-RTOS: Real-Time Scheduler & Deadline Monitor
Implements EDF as a real-time scheduling policy and continuously tracks
deadline status for all active processes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable, Any
import time

from core.pcb import PCB
from core.process import ProcessState


@dataclass
class DeadlineRecord:
    pid: str
    process_name: str
    priority: int
    deadline: float
    arrival_time: float
    burst_time: float
    remaining: float
    state: str
    current_time: float

    @property
    def time_to_deadline(self) -> float:
        return max(0.0, self.deadline - self.current_time)

    @property
    def status(self) -> str:
        if self.state == ProcessState.TERMINATED.value:
            return "MET" if self.time_to_deadline >= 0 else "MISSED"
        if self.time_to_deadline <= 0:
            return "MISSED"
        if self.time_to_deadline <= (self.deadline * 0.20):
            return "WARNING"
        return "PENDING"

    @property
    def urgency_ratio(self) -> float:
        """0.0 = plenty of time, 1.0 = at deadline."""
        span = self.deadline - self.arrival_time
        if span <= 0:
            return 1.0
        elapsed = self.current_time - self.arrival_time
        return min(1.0, max(0.0, elapsed / span))


class RealTimeScheduler:
    """
    Real-Time scheduler layer using EDF (Earliest Deadline First) policy.
    Tracks deadline states for all active processes and fires warning hooks.
    """

    def __init__(self):
        self.simulation_time: float = 0.0
        self._warning_hooks: List[Callable[[DeadlineRecord], None]] = []
        self._missed_hooks: List[Callable[[DeadlineRecord], None]] = []
        self._records: Dict[str, DeadlineRecord] = {}

        # Cumulative stats
        self.total_deadlines: int = 0
        self.deadlines_met: int = 0
        self.deadlines_missed: int = 0

    # ------------------------------------------------------------------ #
    #  EDF ordering                                                         #
    # ------------------------------------------------------------------ #
    def edf_order(self, processes: List[PCB]) -> List[PCB]:
        """Return processes sorted by EDF policy (earliest deadline first)."""
        rt_procs = [p for p in processes if p.deadline is not None
                    and p.state in (ProcessState.READY, ProcessState.RUNNING)]
        non_rt   = [p for p in processes if p.deadline is None
                    and p.state in (ProcessState.READY, ProcessState.RUNNING)]
        rt_procs.sort(key=lambda p: (p.deadline, p.arrival_time))
        return rt_procs + non_rt

    def next_to_run(self, ready_queue: List[PCB]) -> Optional[PCB]:
        """Pick the next process to run based on EDF."""
        ordered = self.edf_order(ready_queue)
        return ordered[0] if ordered else None

    # ------------------------------------------------------------------ #
    #  Deadline Monitoring                                                  #
    # ------------------------------------------------------------------ #
    def update(self, processes: List[PCB], current_time: float):
        """Scan all active processes and update deadline records + fire hooks."""
        self.simulation_time = current_time

        for p in processes:
            if p.deadline is None:
                continue
            if p.state == ProcessState.TERMINATED:
                continue

            rec = DeadlineRecord(
                pid=p.pid,
                process_name=p.process_name,
                priority=p.priority,
                deadline=p.deadline,
                arrival_time=p.arrival_time,
                burst_time=p.burst_time,
                remaining=p.remaining_burst,
                state=p.state.value,
                current_time=current_time,
            )
            self._records[p.pid] = rec

            if rec.status == "MISSED":
                p.deadline_status = "MISSED"
                for hook in self._missed_hooks:
                    hook(rec)
            elif rec.status == "WARNING":
                p.deadline_status = "WARNING"
                for hook in self._warning_hooks:
                    hook(rec)
            else:
                p.deadline_status = "PENDING"

    def finalize_process(self, p: PCB, completion_time: float):
        """Record deadline outcome when a process terminates."""
        if p.deadline is None:
            return
        self.total_deadlines += 1
        if completion_time <= p.deadline:
            self.deadlines_met += 1
            p.deadline_status = "MET"
        else:
            self.deadlines_missed += 1
            p.deadline_status = "MISSED"

    @property
    def success_rate(self) -> float:
        if self.total_deadlines == 0:
            return 100.0
        return (self.deadlines_met / self.total_deadlines) * 100.0

    def get_records(self) -> List[DeadlineRecord]:
        return sorted(self._records.values(), key=lambda r: r.time_to_deadline)

    # ------------------------------------------------------------------ #
    #  Hooks                                                                #
    # ------------------------------------------------------------------ #
    def on_deadline_warning(self, hook: Callable[[DeadlineRecord], None]):
        self._warning_hooks.append(hook)

    def on_deadline_missed(self, hook: Callable[[DeadlineRecord], None]):
        self._missed_hooks.append(hook)

    # ------------------------------------------------------------------ #
    #  Stats                                                                #
    # ------------------------------------------------------------------ #
    def stats(self) -> Dict[str, Any]:
        return {
            "total_deadlines": self.total_deadlines,
            "deadlines_met": self.deadlines_met,
            "deadlines_missed": self.deadlines_missed,
            "success_rate": round(self.success_rate, 2),
            "active_records": len(self._records),
        }

    def reset(self):
        self.simulation_time = 0.0
        self.total_deadlines = 0
        self.deadlines_met = 0
        self.deadlines_missed = 0
        self._records.clear()
