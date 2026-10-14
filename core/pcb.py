"""
D-RTOS: Process Control Block (PCB)
Complete PCB definition with all tracking fields required by the project specification.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from core.process import ProcessState, ThreatLevel, ProcessType


@dataclass
class PCB:
    """
    Process Control Block — the complete representation of an OS process.
    All timing values are in simulated 'ticks' (1 tick = 1 time unit).
    """
    # Identifiers
    pid: str
    process_name: str
    object_id: str                          # Radar object that triggered this process
    event_id: str = ""                      # MongoDB radar event reference

    # Scheduling parameters
    arrival_time: float = 0.0
    burst_time: float = 0.0
    remaining_burst: float = 0.0
    priority: int = 4                       # 1 = highest, 4 = lowest
    threat_level: ThreatLevel = ThreatLevel.LOW
    deadline: Optional[float] = None        # Absolute deadline in simulation ticks
    process_type: ProcessType = ProcessType.RADAR_SCAN

    # Memory & Resources
    memory_requirement: int = 64            # MB
    required_resources: Dict[str, int] = field(default_factory=dict)
    allocated_resources: Dict[str, int] = field(default_factory=dict)

    # CPU Assignment
    assigned_cpu: Optional[int] = None      # Core index 0-3

    # State
    state: ProcessState = ProcessState.NEW

    # Timestamps (simulation ticks)
    creation_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    completion_time: Optional[float] = None

    # Computed metrics (filled in after scheduling)
    waiting_time: float = 0.0
    turnaround_time: float = 0.0
    response_time: float = -1.0             # -1 = not started yet

    # Execution tracking
    preemption_count: int = 0
    context_switches: int = 0
    page_faults: int = 0
    deadline_status: str = "PENDING"        # PENDING | WARNING | MET | MISSED

    # Memory mapping
    memory_start: Optional[int] = None      # Physical start address
    page_table: Dict[int, int] = field(default_factory=dict)   # page -> frame

    # History / log
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    preemption_log: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.remaining_burst == 0.0:
            self.remaining_burst = self.burst_time
        self._log_state_change(None, self.state)

    # ------------------------------------------------------------------ #
    #  State Transitions                                                    #
    # ------------------------------------------------------------------ #
    def transition(self, new_state: ProcessState, reason: str = ""):
        old_state = self.state
        self.state = new_state
        self._log_state_change(old_state, new_state, reason)
        if new_state == ProcessState.RUNNING and self.start_time is None:
            self.start_time = time.time()
            if self.response_time < 0:
                self.response_time = 0.0   # will be computed in scheduler

    def _log_state_change(self, old: Optional[ProcessState], new: ProcessState, reason: str = ""):
        self.state_history.append({
            "from": old.value if old else None,
            "to": new.value,
            "reason": reason,
            "timestamp": time.time(),
        })

    def log_preemption(self, preempted_by: str, reason: str, simulation_time: float):
        self.preemption_count += 1
        self.preemption_log.append({
            "preempted_by": preempted_by,
            "reason": reason,
            "simulation_time": simulation_time,
        })

    # ------------------------------------------------------------------ #
    #  Computed Properties                                                  #
    # ------------------------------------------------------------------ #
    @property
    def is_real_time(self) -> bool:
        return self.deadline is not None

    @property
    def time_to_deadline(self) -> Optional[float]:
        """Remaining time before deadline (requires current_time parameter for accuracy)."""
        return self.deadline  # Raw deadline tick; caller subtracts current time

    def update_deadline_status(self, current_time: float):
        if self.deadline is None:
            self.deadline_status = "N/A"
            return
        remaining = self.deadline - current_time
        if self.state == ProcessState.TERMINATED:
            if self.completion_time is not None and self.completion_time <= self.deadline:
                self.deadline_status = "MET"
            else:
                self.deadline_status = "MISSED"
        elif remaining <= 0:
            self.deadline_status = "MISSED"
        elif remaining <= self.deadline * 0.25:
            self.deadline_status = "WARNING"
        else:
            self.deadline_status = "PENDING"

    # ------------------------------------------------------------------ #
    #  Serialization for MongoDB                                            #
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "event_id": self.event_id,
            "process_name": self.process_name,
            "object_id": self.object_id,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "remaining_burst": self.remaining_burst,
            "priority": self.priority,
            "threat_level": self.threat_level.name,
            "deadline": self.deadline,
            "memory_requirement": self.memory_requirement,
            "required_resources": self.required_resources,
            "allocated_resources": self.allocated_resources,
            "assigned_cpu": self.assigned_cpu,
            "state": self.state.value,
            "creation_time": self.creation_time,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
            "preemption_count": self.preemption_count,
            "context_switches": self.context_switches,
            "page_faults": self.page_faults,
            "deadline_status": self.deadline_status,
            "state_history": self.state_history,
            "preemption_log": self.preemption_log,
        }

    def __repr__(self) -> str:
        return (
            f"PCB({self.pid} | {self.process_name} | "
            f"State={self.state.value} | Priority={self.priority} | "
            f"Burst={self.burst_time} | Remaining={self.remaining_burst:.1f})"
        )
