"""
D-RTOS: CPU Scheduler
Implements FCFS, SJF, Priority, Round Robin, Preemptive Priority, SRTF,
Multilevel Queue (MLQ), and EDF scheduling algorithms.
All algorithms return a SchedulerResult with Gantt chart data and metrics.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

from core.pcb import PCB
from core.process import ProcessState


# ============================================================
# Scheduler Result
# ============================================================

@dataclass
class GanttEntry:
    pid: str
    process_name: str
    start: float
    end: float
    cpu_id: int = 0


@dataclass
class ProcessMetrics:
    pid: str
    process_name: str
    arrival_time: float
    burst_time: float
    completion_time: float = 0.0
    turnaround_time: float = 0.0
    waiting_time: float = 0.0
    response_time: float = 0.0


@dataclass
class SchedulerResult:
    algorithm: str
    gantt: List[GanttEntry] = field(default_factory=list)
    metrics: List[ProcessMetrics] = field(default_factory=list)

    avg_waiting_time: float = 0.0
    avg_turnaround_time: float = 0.0
    avg_response_time: float = 0.0
    cpu_utilization: float = 0.0
    throughput: float = 0.0
    context_switches: int = 0
    total_time: float = 0.0

    deadline_met: int = 0
    deadline_missed: int = 0
    deadline_success_rate: float = 0.0

    def compute_averages(self):
        if not self.metrics:
            return
        n = len(self.metrics)
        self.avg_waiting_time    = sum(m.waiting_time    for m in self.metrics) / n
        self.avg_turnaround_time = sum(m.turnaround_time for m in self.metrics) / n
        self.avg_response_time   = sum(m.response_time   for m in self.metrics) / n
        if self.total_time > 0:
            busy_time = sum(e.end - e.start for e in self.gantt if e.pid != "IDLE")
            self.cpu_utilization = (busy_time / self.total_time) * 100.0
            self.throughput = n / self.total_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "avg_waiting_time": round(self.avg_waiting_time, 3),
            "avg_turnaround_time": round(self.avg_turnaround_time, 3),
            "avg_response_time": round(self.avg_response_time, 3),
            "cpu_utilization": round(self.cpu_utilization, 2),
            "throughput": round(self.throughput, 4),
            "context_switches": self.context_switches,
            "total_time": self.total_time,
            "deadline_met": self.deadline_met,
            "deadline_missed": self.deadline_missed,
            "deadline_success_rate": round(self.deadline_success_rate, 2),
        }


# ============================================================
# Helpers
# ============================================================

def _clone_processes(processes: List[PCB]) -> List[Dict]:
    """Return lightweight mutable dicts for scheduling simulation."""
    clones = []
    for p in processes:
        clones.append({
            "pid": p.pid,
            "name": p.process_name,
            "arrival": p.arrival_time,
            "burst": p.burst_time,
            "remaining": p.burst_time,
            "priority": p.priority,
            "deadline": p.deadline,
            "threat": p.threat_level,
            "first_run": None,
            "completion": None,
        })
    return clones


def _build_metrics(clones: List[Dict]) -> List[ProcessMetrics]:
    metrics = []
    for c in clones:
        ct = c["completion"] or 0.0
        tat = ct - c["arrival"]
        wt = tat - c["burst"]
        rt = (c["first_run"] or c["arrival"]) - c["arrival"]
        metrics.append(ProcessMetrics(
            pid=c["pid"],
            process_name=c["name"],
            arrival_time=c["arrival"],
            burst_time=c["burst"],
            completion_time=ct,
            turnaround_time=max(0.0, tat),
            waiting_time=max(0.0, wt),
            response_time=max(0.0, rt),
        ))
    return metrics


# ============================================================
# Scheduler Algorithms
# ============================================================

class Scheduler:
    """Central scheduler: all algorithms, no GUI code."""

    # --------------------------------------------------------
    # FCFS
    # --------------------------------------------------------
    def fcfs(self, processes: List[PCB]) -> SchedulerResult:
        result = SchedulerResult(algorithm="FCFS")
        if not processes:
            return result

        clones = sorted(_clone_processes(processes), key=lambda x: (x["arrival"], x["pid"]))
        time_ = 0.0
        cs = 0

        for c in clones:
            if time_ < c["arrival"]:
                result.gantt.append(GanttEntry("IDLE", "Idle", time_, c["arrival"]))
                time_ = c["arrival"]
            if c["first_run"] is None:
                c["first_run"] = time_
            start = time_
            time_ += c["burst"]
            c["completion"] = time_
            result.gantt.append(GanttEntry(c["pid"], c["name"], start, time_))
            cs += 1

        result.context_switches = max(0, cs - 1)
        result.total_time = time_
        result.metrics = _build_metrics(clones)
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # SJF (Non-preemptive)
    # --------------------------------------------------------
    def sjf(self, processes: List[PCB]) -> SchedulerResult:
        result = SchedulerResult(algorithm="SJF")
        if not processes:
            return result

        clones = _clone_processes(processes)
        remaining = list(clones)
        time_ = 0.0
        done = []
        cs = 0
        prev_pid = None

        while remaining:
            available = [c for c in remaining if c["arrival"] <= time_]
            if not available:
                next_arr = min(c["arrival"] for c in remaining)
                result.gantt.append(GanttEntry("IDLE", "Idle", time_, next_arr))
                time_ = next_arr
                continue
            chosen = min(available, key=lambda x: (x["burst"], x["arrival"]))
            remaining.remove(chosen)
            if chosen["first_run"] is None:
                chosen["first_run"] = time_
            start = time_
            if prev_pid and prev_pid != chosen["pid"]:
                cs += 1
            time_ += chosen["burst"]
            chosen["completion"] = time_
            result.gantt.append(GanttEntry(chosen["pid"], chosen["name"], start, time_))
            prev_pid = chosen["pid"]
            done.append(chosen)

        result.context_switches = cs
        result.total_time = time_
        result.metrics = _build_metrics(done)
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # Priority (Non-preemptive, lower number = higher priority)
    # --------------------------------------------------------
    def priority_nonpreemptive(self, processes: List[PCB]) -> SchedulerResult:
        result = SchedulerResult(algorithm="Priority")
        if not processes:
            return result

        clones = _clone_processes(processes)
        remaining = list(clones)
        time_ = 0.0
        done = []
        cs = 0
        prev_pid = None

        while remaining:
            available = [c for c in remaining if c["arrival"] <= time_]
            if not available:
                next_arr = min(c["arrival"] for c in remaining)
                result.gantt.append(GanttEntry("IDLE", "Idle", time_, next_arr))
                time_ = next_arr
                continue
            chosen = min(available, key=lambda x: (x["priority"], x["arrival"]))
            remaining.remove(chosen)
            if chosen["first_run"] is None:
                chosen["first_run"] = time_
            start = time_
            if prev_pid and prev_pid != chosen["pid"]:
                cs += 1
            time_ += chosen["burst"]
            chosen["completion"] = time_
            result.gantt.append(GanttEntry(chosen["pid"], chosen["name"], start, time_))
            prev_pid = chosen["pid"]
            done.append(chosen)

        result.context_switches = cs
        result.total_time = time_
        result.metrics = _build_metrics(done)
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # Round Robin
    # --------------------------------------------------------
    def round_robin(self, processes: List[PCB], quantum: float = 2.0) -> SchedulerResult:
        result = SchedulerResult(algorithm=f"Round Robin (q={quantum})")
        if not processes:
            return result

        clones = sorted(_clone_processes(processes), key=lambda x: x["arrival"])
        queue: List[Dict] = []
        time_ = 0.0
        cs = 0
        prev_pid = None
        remaining_map = {c["pid"]: c for c in clones}
        all_pids_in_order = [c["pid"] for c in clones]
        idx = 0  # pointer for arrival tracking
        done_map: Dict[str, Dict] = {}

        # Seed queue with processes that arrive at t=0
        while idx < len(clones) and clones[idx]["arrival"] <= time_:
            queue.append(clones[idx])
            idx += 1

        while queue or idx < len(clones):
            if not queue:
                time_ = clones[idx]["arrival"]
                queue.append(clones[idx])
                idx += 1

            current = queue.pop(0)
            if current["first_run"] is None:
                current["first_run"] = time_

            if prev_pid and prev_pid != current["pid"]:
                cs += 1

            exec_time = min(quantum, current["remaining"])
            start = time_
            time_ += exec_time
            current["remaining"] -= exec_time
            result.gantt.append(GanttEntry(current["pid"], current["name"], start, time_))
            prev_pid = current["pid"]

            # Enqueue newly arrived processes
            while idx < len(clones) and clones[idx]["arrival"] <= time_:
                queue.append(clones[idx])
                idx += 1

            if current["remaining"] > 0:
                queue.append(current)
            else:
                current["completion"] = time_
                done_map[current["pid"]] = current

        result.context_switches = cs
        result.total_time = time_
        result.metrics = _build_metrics(list(done_map.values()))
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # Preemptive Priority
    # --------------------------------------------------------
    def preemptive_priority(self, processes: List[PCB]) -> SchedulerResult:
        result = SchedulerResult(algorithm="Preemptive Priority")
        if not processes:
            return result

        clones = _clone_processes(processes)
        remaining = {c["pid"]: c for c in clones}
        time_ = 0.0
        cs = 0
        prev_pid = None
        done: List[Dict] = []
        all_clones = list(clones)

        while remaining:
            available = [c for c in remaining.values() if c["arrival"] <= time_]
            if not available:
                next_arr = min(c["arrival"] for c in remaining.values())
                result.gantt.append(GanttEntry("IDLE", "Idle", time_, next_arr))
                time_ = next_arr
                continue

            chosen = min(available, key=lambda x: (x["priority"], x["arrival"]))

            if chosen["first_run"] is None:
                chosen["first_run"] = time_

            if prev_pid and prev_pid != chosen["pid"]:
                cs += 1

            # Run for 1 tick (preemptive)
            start = time_
            time_ += 1.0
            chosen["remaining"] -= 1.0

            # Check if new higher priority arrived
            new_available = [c for c in remaining.values()
                             if c["arrival"] <= time_ and c["pid"] != chosen["pid"]]
            will_preempt = any(c["priority"] < chosen["priority"] for c in new_available)

            if chosen["remaining"] <= 0:
                chosen["completion"] = time_
                result.gantt.append(GanttEntry(chosen["pid"], chosen["name"], start, time_))
                del remaining[chosen["pid"]]
                done.append(chosen)
                prev_pid = None
            elif will_preempt:
                result.gantt.append(GanttEntry(chosen["pid"], chosen["name"], start, time_))
                prev_pid = chosen["pid"]
            else:
                result.gantt.append(GanttEntry(chosen["pid"], chosen["name"], start, time_))
                prev_pid = chosen["pid"]

        # Merge consecutive same-pid gantt entries
        result.gantt = _merge_gantt(result.gantt)
        result.context_switches = cs
        result.total_time = time_
        result.metrics = _build_metrics(done)
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # SRTF (Shortest Remaining Time First)
    # --------------------------------------------------------
    def srtf(self, processes: List[PCB]) -> SchedulerResult:
        result = SchedulerResult(algorithm="SRTF")
        if not processes:
            return result

        clones = _clone_processes(processes)
        remaining = {c["pid"]: c for c in clones}
        time_ = 0.0
        cs = 0
        prev_pid = None
        done: List[Dict] = []

        while remaining:
            available = [c for c in remaining.values() if c["arrival"] <= time_]
            if not available:
                next_arr = min(c["arrival"] for c in remaining.values())
                result.gantt.append(GanttEntry("IDLE", "Idle", time_, next_arr))
                time_ = next_arr
                continue

            chosen = min(available, key=lambda x: (x["remaining"], x["arrival"]))

            if chosen["first_run"] is None:
                chosen["first_run"] = time_

            if prev_pid and prev_pid != chosen["pid"]:
                cs += 1

            start = time_
            time_ += 1.0
            chosen["remaining"] -= 1.0
            result.gantt.append(GanttEntry(chosen["pid"], chosen["name"], start, time_))
            prev_pid = chosen["pid"]

            if chosen["remaining"] <= 0:
                chosen["completion"] = time_
                del remaining[chosen["pid"]]
                done.append(chosen)
                prev_pid = None

        result.gantt = _merge_gantt(result.gantt)
        result.context_switches = cs
        result.total_time = time_
        result.metrics = _build_metrics(done)
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # Multilevel Queue (MLQ)
    # Queue 0: Critical (Priority 1) — Preemptive Priority
    # Queue 1: Interactive (Priority 2) — Round Robin q=3
    # Queue 2: Batch (Priority 3-4) — FCFS
    # --------------------------------------------------------
    def multilevel_queue(self, processes: List[PCB], quantum: float = 3.0) -> SchedulerResult:
        result = SchedulerResult(algorithm="Multilevel Queue")
        if not processes:
            return result

        q0 = [p for p in processes if p.priority == 1]
        q1 = [p for p in processes if p.priority == 2]
        q2 = [p for p in processes if p.priority in (3, 4)]

        all_done: List[ProcessMetrics] = []
        gantt: List[GanttEntry] = []
        time_ = 0.0
        cs = 0

        def run_queue(qprocs, algo_name):
            nonlocal time_, cs
            if not qprocs:
                return
            if algo_name == "pp":
                sub = self.preemptive_priority(qprocs)
            elif algo_name == "rr":
                sub = self.round_robin(qprocs, quantum)
            else:
                sub = self.fcfs(qprocs)
            offset = time_
            for g in sub.gantt:
                gantt.append(GanttEntry(g.pid, g.process_name, g.start + offset, g.end + offset))
            time_ += sub.total_time
            cs += sub.context_switches
            all_done.extend(sub.metrics)

        run_queue(q0, "pp")
        run_queue(q1, "rr")
        run_queue(q2, "fcfs")

        result.gantt = gantt
        result.context_switches = cs
        result.total_time = time_
        result.metrics = all_done
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # EDF (Earliest Deadline First)
    # --------------------------------------------------------
    def edf(self, processes: List[PCB]) -> SchedulerResult:
        result = SchedulerResult(algorithm="EDF")
        if not processes:
            return result

        # Processes without deadline get very large deadline
        clones = _clone_processes(processes)
        for c in clones:
            if c["deadline"] is None:
                c["deadline"] = 1e9

        remaining = {c["pid"]: c for c in clones}
        time_ = 0.0
        cs = 0
        prev_pid = None
        done: List[Dict] = []

        while remaining:
            available = [c for c in remaining.values() if c["arrival"] <= time_]
            if not available:
                next_arr = min(c["arrival"] for c in remaining.values())
                result.gantt.append(GanttEntry("IDLE", "Idle", time_, next_arr))
                time_ = next_arr
                continue

            chosen = min(available, key=lambda x: (x["deadline"], x["arrival"]))

            if chosen["first_run"] is None:
                chosen["first_run"] = time_

            if prev_pid and prev_pid != chosen["pid"]:
                cs += 1

            start = time_
            time_ += 1.0
            chosen["remaining"] -= 1.0
            result.gantt.append(GanttEntry(chosen["pid"], chosen["name"], start, time_))
            prev_pid = chosen["pid"]

            if chosen["remaining"] <= 0:
                chosen["completion"] = time_
                del remaining[chosen["pid"]]
                done.append(chosen)
                prev_pid = None

        result.gantt = _merge_gantt(result.gantt)
        result.context_switches = cs
        result.total_time = time_
        result.metrics = _build_metrics(done)
        result.compute_averages()
        self._compute_deadlines(processes, result)
        return result

    # --------------------------------------------------------
    # Dispatcher: run algorithm by name
    # --------------------------------------------------------
    def run(self, algorithm: str, processes: List[PCB], quantum: float = 2.0) -> SchedulerResult:
        algo = algorithm.upper().replace(" ", "_")
        if "FCFS" in algo:
            return self.fcfs(processes)
        elif "SJF" in algo:
            return self.sjf(processes)
        elif "SRTF" in algo:
            return self.srtf(processes)
        elif "PREEMPTIVE" in algo or "PP" in algo:
            return self.preemptive_priority(processes)
        elif "PRIORITY" in algo:
            return self.priority_nonpreemptive(processes)
        elif "ROUND" in algo or "RR" in algo:
            return self.round_robin(processes, quantum)
        elif "MLQ" in algo or "MULTI" in algo:
            return self.multilevel_queue(processes, quantum)
        elif "EDF" in algo:
            return self.edf(processes)
        else:
            raise ValueError(f"Unknown scheduling algorithm: {algorithm}")

    def run_all(self, processes: List[PCB], quantum: float = 2.0) -> Dict[str, SchedulerResult]:
        """Run all algorithms on same process set and return comparative results."""
        algorithms = [
            "FCFS", "SJF", "Priority", "Round Robin",
            "Preemptive Priority", "SRTF", "MLQ", "EDF"
        ]
        return {algo: self.run(algo, processes, quantum) for algo in algorithms}

    # --------------------------------------------------------
    # Internal
    # --------------------------------------------------------
    def _compute_deadlines(self, original: List[PCB], result: SchedulerResult):
        deadline_map = {p.pid: p.deadline for p in original}
        met = 0
        missed = 0
        for m in result.metrics:
            dl = deadline_map.get(m.pid)
            if dl is not None:
                if m.completion_time <= dl:
                    met += 1
                else:
                    missed += 1
        result.deadline_met = met
        result.deadline_missed = missed
        total = met + missed
        result.deadline_success_rate = (met / total * 100.0) if total > 0 else 100.0


def _merge_gantt(gantt: List[GanttEntry]) -> List[GanttEntry]:
    """Merge consecutive entries with the same PID into single blocks."""
    if not gantt:
        return gantt
    merged = [gantt[0]]
    for entry in gantt[1:]:
        last = merged[-1]
        if entry.pid == last.pid and abs(entry.start - last.end) < 1e-9:
            merged[-1] = GanttEntry(last.pid, last.process_name, last.start, entry.end, last.cpu_id)
        else:
            merged.append(entry)
    return merged
