"""
D-RTOS: Multi-Core Manager
Simulates 4 CPU cores with process assignment, per-core utilization tracking,
and dynamic load balancing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
import time

from core.pcb import PCB
from core.process import ProcessState

NUM_CORES = 4


@dataclass
class CoreState:
    core_id: int
    current_process: Optional[PCB] = None
    busy_ticks: float = 0.0
    idle_ticks: float = 0.0
    total_ticks: float = 0.0
    processes_completed: int = 0
    context_switches: int = 0

    @property
    def utilization(self) -> float:
        if self.total_ticks == 0:
            return 0.0
        return (self.busy_ticks / self.total_ticks) * 100.0

    @property
    def is_idle(self) -> bool:
        return self.current_process is None

    def label(self) -> str:
        return f"CPU-{self.core_id}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "core_id": self.core_id,
            "current_pid": self.current_process.pid if self.current_process else None,
            "utilization": round(self.utilization, 1),
            "busy_ticks": round(self.busy_ticks, 2),
            "idle_ticks": round(self.idle_ticks, 2),
            "processes_completed": self.processes_completed,
            "context_switches": self.context_switches,
        }


class MultiCoreManager:
    """
    Manages 4 simulated CPU cores.
    Supports process assignment, tick-based utilization tracking, and load balancing.
    """

    def __init__(self, num_cores: int = NUM_CORES):
        self.num_cores = num_cores
        self.cores: List[CoreState] = [CoreState(i) for i in range(num_cores)]
        self.simulation_time: float = 0.0
        self.load_balance_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    #  Process Assignment                                                   #
    # ------------------------------------------------------------------ #
    def assign_process(self, pcb: PCB, policy: str = "least_loaded") -> Optional[int]:
        """
        Assign a process to a CPU core.
        Policies:
          - 'least_loaded': assign to core with lowest utilization
          - 'round_robin': assign to next core in rotation
          - 'threat_affinity': CRITICAL -> CPU0, HIGH -> CPU1, else least_loaded
        Returns core_id or None if all cores busy.
        """
        if policy == "threat_affinity":
            from core.process import ThreatLevel
            if pcb.threat_level == ThreatLevel.CRITICAL and self.cores[0].is_idle:
                return self._do_assign(pcb, 0)
            elif pcb.threat_level == ThreatLevel.HIGH and self.cores[1].is_idle:
                return self._do_assign(pcb, 1)
        # Fallback: find least loaded idle core
        idle_cores = [c for c in self.cores if c.is_idle]
        if not idle_cores:
            return None
        chosen = min(idle_cores, key=lambda c: c.utilization)
        return self._do_assign(pcb, chosen.core_id)

    def assign_to_core(self, pcb: PCB, core_id: int) -> bool:
        """Explicitly assign process to a specific core."""
        if 0 <= core_id < self.num_cores and self.cores[core_id].is_idle:
            self._do_assign(pcb, core_id)
            return True
        return False

    def _do_assign(self, pcb: PCB, core_id: int) -> int:
        core = self.cores[core_id]
        if core.current_process is not None:
            core.context_switches += 1
        core.current_process = pcb
        pcb.assigned_cpu = core_id
        return core_id

    def release_core(self, core_id: int) -> Optional[PCB]:
        """Release a core after process completion."""
        core = self.cores[core_id]
        released = core.current_process
        core.current_process = None
        if released:
            core.processes_completed += 1
        return released

    def get_idle_cores(self) -> List[int]:
        return [c.core_id for c in self.cores if c.is_idle]

    def get_busy_cores(self) -> List[Tuple[int, PCB]]:
        return [(c.core_id, c.current_process) for c in self.cores if not c.is_idle]

    # ------------------------------------------------------------------ #
    #  Tick-Based Utilization                                               #
    # ------------------------------------------------------------------ #
    def tick(self, delta: float = 1.0):
        """Advance simulation time by delta and update core utilization."""
        self.simulation_time += delta
        for core in self.cores:
            core.total_ticks += delta
            if core.current_process is not None:
                core.busy_ticks += delta
                # Reduce remaining burst
                core.current_process.remaining_burst = max(
                    0.0, core.current_process.remaining_burst - delta
                )
            else:
                core.idle_ticks += delta

    # ------------------------------------------------------------------ #
    #  Utilization Stats                                                    #
    # ------------------------------------------------------------------ #
    @property
    def overall_utilization(self) -> float:
        if not self.cores:
            return 0.0
        return sum(c.utilization for c in self.cores) / self.num_cores

    @property
    def utilization_variance(self) -> float:
        utils = [c.utilization for c in self.cores]
        if not utils:
            return 0.0
        mean = sum(utils) / len(utils)
        return sum((u - mean) ** 2 for u in utils) / len(utils)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "cores": [c.to_dict() for c in self.cores],
            "overall_utilization": round(self.overall_utilization, 1),
            "utilization_variance": round(self.utilization_variance, 2),
            "simulation_time": self.simulation_time,
        }

    # ------------------------------------------------------------------ #
    #  Load Balancing                                                       #
    # ------------------------------------------------------------------ #
    def load_balance(self, ready_queue: List[PCB], threshold: float = 20.0) -> List[Dict]:
        """
        Redistribute work from overloaded cores to underloaded cores.
        Returns a log of migrations performed.
        Returns list of migration records.
        """
        migrations = []
        utils = [(c.core_id, c.utilization) for c in self.cores]
        mean_util = sum(u for _, u in utils) / len(utils) if utils else 0.0

        overloaded  = [cid for cid, u in utils if u > mean_util + threshold]
        underloaded = [cid for cid, u in utils if u < mean_util - threshold]

        # Assign queued processes to underloaded cores
        for core_id in underloaded:
            core = self.cores[core_id]
            if core.is_idle and ready_queue:
                # Pick the highest priority ready process
                candidate = min(ready_queue, key=lambda p: p.priority)
                ready_queue.remove(candidate)
                self._do_assign(candidate, core_id)
                migrations.append({
                    "action": "MIGRATE_FROM_QUEUE",
                    "pid": candidate.pid,
                    "to_core": core_id,
                    "reason": f"Core {core_id} utilization below threshold",
                    "simulation_time": self.simulation_time,
                })

        before = [c.utilization for c in self.cores]

        if migrations:
            self.load_balance_log.extend(migrations)
            after = [c.utilization for c in self.cores]
            self.load_balance_log.append({
                "action": "BALANCE_SUMMARY",
                "before": before,
                "after": after,
                "simulation_time": self.simulation_time,
            })

        return migrations

    def simulate_load_imbalance(self) -> Tuple[List[float], List[float]]:
        """
        Simulate before/after load balancing for GUI demonstration.
        Returns (before_utils, after_utils).
        """
        import random
        before = [random.uniform(80, 99), random.uniform(10, 30),
                  random.uniform(10, 25), random.uniform(10, 20)]
        mean = sum(before) / len(before)
        spread = 8.0
        after = [max(0, min(100, mean + random.uniform(-spread, spread))) for _ in before]
        return before, after

    def reset(self):
        self.cores = [CoreState(i) for i in range(self.num_cores)]
        self.simulation_time = 0.0
        self.load_balance_log.clear()
