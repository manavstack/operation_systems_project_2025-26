"""
D-RTOS: Performance Manager
Aggregates and compares performance metrics across all scheduling algorithms.
Computes system-wide statistics for dashboard and analytics views.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import time

from core.scheduler import SchedulerResult


@dataclass
class SystemSnapshot:
    """Periodic snapshot of system metrics."""
    timestamp: float
    simulation_time: float
    cpu_utilization: float
    cpu0_utilization: float
    cpu1_utilization: float
    cpu2_utilization: float
    cpu3_utilization: float
    memory_utilization: float
    active_processes: int
    ready_processes: int
    waiting_processes: int
    running_processes: int
    terminated_processes: int
    deadline_success_rate: float
    context_switches: int
    page_faults: int
    threat_level: str = "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "simulation_time": self.simulation_time,
            "cpu_utilization": round(self.cpu_utilization, 1),
            "cpu0_utilization": round(self.cpu0_utilization, 1),
            "cpu1_utilization": round(self.cpu1_utilization, 1),
            "cpu2_utilization": round(self.cpu2_utilization, 1),
            "cpu3_utilization": round(self.cpu3_utilization, 1),
            "memory_utilization": round(self.memory_utilization, 1),
            "active_processes": self.active_processes,
            "ready_processes": self.ready_processes,
            "waiting_processes": self.waiting_processes,
            "running_processes": self.running_processes,
            "terminated_processes": self.terminated_processes,
            "deadline_success_rate": round(self.deadline_success_rate, 1),
            "context_switches": self.context_switches,
            "page_faults": self.page_faults,
            "threat_level": self.threat_level,
        }


class PerformanceManager:
    """
    Aggregates scheduling results and system metrics.
    Provides comparative analysis across algorithms and time-series tracking.
    """

    def __init__(self):
        self.scheduling_results: Dict[str, SchedulerResult] = {}
        self.snapshots: List[SystemSnapshot] = []
        self.session_start: float = time.time()

    # ------------------------------------------------------------------ #
    #  Scheduling Result Storage                                            #
    # ------------------------------------------------------------------ #
    def record_result(self, result: SchedulerResult):
        self.scheduling_results[result.algorithm] = result

    def record_all(self, results: Dict[str, SchedulerResult]):
        self.scheduling_results.update(results)

    # ------------------------------------------------------------------ #
    #  Comparative Analysis                                                 #
    # ------------------------------------------------------------------ #
    def compare(self) -> Dict[str, Any]:
        """Compare all recorded scheduling results on all metrics."""
        if not self.scheduling_results:
            return {}

        comparison = {}
        metrics = [
            ("avg_waiting_time",    "Avg Waiting Time"),
            ("avg_turnaround_time", "Avg Turnaround Time"),
            ("avg_response_time",   "Avg Response Time"),
            ("cpu_utilization",     "CPU Utilization (%)"),
            ("throughput",          "Throughput"),
            ("context_switches",    "Context Switches"),
            ("deadline_success_rate", "Deadline Success Rate (%)"),
        ]

        for attr, label in metrics:
            comparison[attr] = {
                "label": label,
                "values": {
                    algo: round(getattr(r, attr, 0), 3)
                    for algo, r in self.scheduling_results.items()
                },
            }

        # Best algorithm by avg waiting time
        best_wait = min(
            self.scheduling_results.items(),
            key=lambda x: x[1].avg_waiting_time
        )
        best_trt = min(
            self.scheduling_results.items(),
            key=lambda x: x[1].avg_turnaround_time
        )
        comparison["best_waiting_time"]    = best_wait[0]
        comparison["best_turnaround_time"] = best_trt[0]

        return comparison

    def summary_table(self) -> List[Dict[str, Any]]:
        """Return a table row for each algorithm with all metrics."""
        rows = []
        for algo, r in self.scheduling_results.items():
            rows.append({
                "Algorithm": algo,
                "Avg Wait": round(r.avg_waiting_time, 2),
                "Avg Turnaround": round(r.avg_turnaround_time, 2),
                "Avg Response": round(r.avg_response_time, 2),
                "CPU Util%": round(r.cpu_utilization, 1),
                "Throughput": round(r.throughput, 4),
                "Context Switches": r.context_switches,
                "Deadline Success%": round(r.deadline_success_rate, 1),
            })
        return rows

    # ------------------------------------------------------------------ #
    #  System Snapshots                                                     #
    # ------------------------------------------------------------------ #
    def take_snapshot(self, sim_time: float,
                      cpu_utils: List[float],
                      memory_util: float,
                      process_counts: Dict[str, int],
                      deadline_rate: float,
                      context_switches: int,
                      page_faults: int,
                      threat_level: str = "LOW") -> SystemSnapshot:

        while len(cpu_utils) < 4:
            cpu_utils.append(0.0)

        snapshot = SystemSnapshot(
            timestamp=time.time(),
            simulation_time=sim_time,
            cpu_utilization=sum(cpu_utils) / len(cpu_utils),
            cpu0_utilization=cpu_utils[0],
            cpu1_utilization=cpu_utils[1],
            cpu2_utilization=cpu_utils[2],
            cpu3_utilization=cpu_utils[3],
            memory_utilization=memory_util,
            active_processes=process_counts.get("active", 0),
            ready_processes=process_counts.get("ready", 0),
            waiting_processes=process_counts.get("waiting", 0),
            running_processes=process_counts.get("running", 0),
            terminated_processes=process_counts.get("terminated", 0),
            deadline_success_rate=deadline_rate,
            context_switches=context_switches,
            page_faults=page_faults,
            threat_level=threat_level,
        )
        self.snapshots.append(snapshot)
        return snapshot

    def get_timeseries(self) -> Dict[str, List]:
        """Return time-series data for plotting."""
        if not self.snapshots:
            return {}
        return {
            "time": [s.simulation_time for s in self.snapshots],
            "cpu_util": [s.cpu_utilization for s in self.snapshots],
            "memory_util": [s.memory_utilization for s in self.snapshots],
            "active_procs": [s.active_processes for s in self.snapshots],
            "deadline_rate": [s.deadline_success_rate for s in self.snapshots],
        }

    def get_final_stats(self) -> Dict[str, Any]:
        if not self.snapshots:
            return {}
        last = self.snapshots[-1]
        return {
            "session_duration": round(time.time() - self.session_start, 1),
            "total_snapshots": len(self.snapshots),
            "avg_cpu_utilization": round(
                sum(s.cpu_utilization for s in self.snapshots) / len(self.snapshots), 1
            ),
            "peak_cpu_utilization": round(max(s.cpu_utilization for s in self.snapshots), 1),
            "avg_memory_utilization": round(
                sum(s.memory_utilization for s in self.snapshots) / len(self.snapshots), 1
            ),
            "total_context_switches": last.context_switches,
            "total_page_faults": last.page_faults,
            "final_deadline_success_rate": round(last.deadline_success_rate, 1),
            "final_threat_level": last.threat_level,
        }

    def reset(self):
        self.scheduling_results.clear()
        self.snapshots.clear()
        self.session_start = time.time()
