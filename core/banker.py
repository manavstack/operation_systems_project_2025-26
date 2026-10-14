"""
D-RTOS: Banker's Algorithm
Deadlock avoidance via the Banker's Algorithm.
Computes system safety state and validates resource requests.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import copy
import time


@dataclass
class BankersState:
    """Encapsulates the complete state for Banker's Algorithm."""
    processes: List[str]          # PID list
    resources: List[str]          # Resource name list
    available: List[int]          # Available vector
    max_matrix: List[List[int]]   # Max demand matrix
    allocation: List[List[int]]   # Current allocation matrix

    @property
    def num_processes(self) -> int:
        return len(self.processes)

    @property
    def num_resources(self) -> int:
        return len(self.resources)

    @property
    def need_matrix(self) -> List[List[int]]:
        """Need = Max - Allocation"""
        return [
            [self.max_matrix[i][j] - self.allocation[i][j]
             for j in range(self.num_resources)]
            for i in range(self.num_processes)
        ]

    def to_dict(self) -> Dict[str, Any]:
        need = self.need_matrix
        return {
            "processes": self.processes,
            "resources": self.resources,
            "available": self.available,
            "max_matrix": self.max_matrix,
            "allocation": self.allocation,
            "need_matrix": need,
        }


@dataclass
class SafetyResult:
    is_safe: bool
    safe_sequence: List[str]
    steps: List[Dict[str, Any]]
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "safe_sequence": self.safe_sequence,
            "steps": self.steps,
            "reason": self.reason,
        }


@dataclass
class RequestResult:
    granted: bool
    safe_sequence: List[str]
    reason: str
    state_after: Optional[BankersState] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "granted": self.granted,
            "safe_sequence": self.safe_sequence,
            "reason": self.reason,
        }


class BankersAlgorithm:
    """
    Banker's Algorithm for deadlock avoidance.
    - Safety algorithm: determines if current state is safe.
    - Resource request algorithm: evaluates a process's resource request.
    """

    def __init__(self):
        self.state: Optional[BankersState] = None
        self.request_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    #  State Initialization                                                 #
    # ------------------------------------------------------------------ #
    def setup(self, state: BankersState):
        self.state = state

    def setup_from_dicts(self,
                          processes: List[str],
                          resources: List[str],
                          available: List[int],
                          max_matrix: List[List[int]],
                          allocation: List[List[int]]):
        self.state = BankersState(processes, resources, available, max_matrix, allocation)

    # ------------------------------------------------------------------ #
    #  Safety Algorithm                                                     #
    # ------------------------------------------------------------------ #
    def is_safe(self, state: Optional[BankersState] = None) -> SafetyResult:
        """
        Determine if the given state (or current state) is safe.
        Returns SafetyResult with safe_sequence and step-by-step trace.
        """
        s = state or self.state
        if s is None:
            return SafetyResult(False, [], [], "No state configured")

        n = s.num_processes
        m = s.num_resources
        need = s.need_matrix

        work = list(s.available)
        finish = [False] * n
        safe_sequence: List[str] = []
        steps: List[Dict[str, Any]] = []

        for _ in range(n):
            found = False
            for i in range(n):
                if finish[i]:
                    continue
                # Check if need[i] <= work
                if all(need[i][j] <= work[j] for j in range(m)):
                    # Simulate process finishing
                    old_work = list(work)
                    for j in range(m):
                        work[j] += s.allocation[i][j]
                    finish[i] = True
                    safe_sequence.append(s.processes[i])
                    steps.append({
                        "process": s.processes[i],
                        "need": list(need[i]),
                        "allocation": list(s.allocation[i]),
                        "work_before": old_work,
                        "work_after": list(work),
                        "finish": True,
                    })
                    found = True
                    break

            if not found:
                break

        is_safe_state = all(finish)
        unfinished = [s.processes[i] for i in range(n) if not finish[i]]

        return SafetyResult(
            is_safe=is_safe_state,
            safe_sequence=safe_sequence,
            steps=steps,
            reason=(
                f"Safe sequence found: {' → '.join(safe_sequence)}"
                if is_safe_state
                else f"Unsafe state: processes {unfinished} cannot complete"
            ),
        )

    # ------------------------------------------------------------------ #
    #  Resource Request Algorithm                                           #
    # ------------------------------------------------------------------ #
    def request_resources(self, pid: str, request: List[int]) -> RequestResult:
        """
        Process a resource request for a given PID.
        Returns RequestResult indicating whether the request is granted.
        """
        s = self.state
        if s is None:
            return RequestResult(False, [], "No state configured")

        if pid not in s.processes:
            return RequestResult(False, [], f"Process {pid} not found")

        i = s.processes.index(pid)
        need = s.need_matrix

        # Step 1: Request must not exceed need
        if any(request[j] > need[i][j] for j in range(s.num_resources)):
            result = RequestResult(False, [], f"Request exceeds maximum need for {pid}")
            self._log_request(pid, request, result)
            return result

        # Step 2: Request must not exceed available
        if any(request[j] > s.available[j] for j in range(s.num_resources)):
            result = RequestResult(False, [], f"Insufficient resources available (process must wait)")
            self._log_request(pid, request, result)
            return result

        # Step 3: Pretend to allocate and check safety
        test_state = copy.deepcopy(s)
        for j in range(s.num_resources):
            test_state.available[j]       -= request[j]
            test_state.allocation[i][j]   += request[j]
            test_state.max_matrix[i][j]   = max(test_state.max_matrix[i][j], test_state.allocation[i][j])

        safety = self.is_safe(test_state)

        if safety.is_safe:
            # Commit allocation
            for j in range(s.num_resources):
                s.available[j]     -= request[j]
                s.allocation[i][j] += request[j]
            result = RequestResult(
                granted=True,
                safe_sequence=safety.safe_sequence,
                reason=f"Request granted. System remains in safe state.",
                state_after=test_state,
            )
        else:
            result = RequestResult(
                granted=False,
                safe_sequence=[],
                reason=f"Request DENIED: granting would lead to unsafe state. {safety.reason}",
            )

        self._log_request(pid, request, result)
        return result

    # ------------------------------------------------------------------ #
    #  Demo State Builder                                                   #
    # ------------------------------------------------------------------ #
    def build_demo_state(self, scenario: str = "classic") -> BankersState:
        """Build a textbook Banker's Algorithm demonstration state."""
        if scenario == "classic":
            # Standard OS textbook example
            processes  = ["P0", "P1", "P2", "P3", "P4"]
            resources  = ["A", "B", "C"]
            available  = [3, 3, 2]
            max_matrix = [
                [7, 5, 3],
                [3, 2, 2],
                [9, 0, 2],
                [2, 2, 2],
                [4, 3, 3],
            ]
            allocation = [
                [0, 1, 0],
                [2, 0, 0],
                [3, 0, 2],
                [2, 1, 1],
                [0, 0, 2],
            ]
        elif scenario == "drtos":
            # D-RTOS themed scenario
            processes  = ["P1", "P2", "P3", "P4"]
            resources  = ["CPU", "GPU", "Radar Processor", "Comm Channel"]
            available  = [2, 1, 1, 2]
            max_matrix = [
                [4, 2, 2, 1],
                [3, 1, 1, 2],
                [2, 2, 1, 1],
                [1, 1, 2, 2],
            ]
            allocation = [
                [2, 0, 1, 0],
                [1, 1, 0, 1],
                [1, 0, 1, 0],
                [0, 0, 1, 1],
            ]
        else:
            # Unsafe demo
            processes  = ["P1", "P2", "P3"]
            resources  = ["R1", "R2"]
            available  = [0, 0]
            max_matrix = [[2, 1], [1, 2], [2, 2]]
            allocation = [[1, 0], [1, 1], [0, 1]]

        state = BankersState(processes, resources, available, max_matrix, allocation)
        self.state = state
        return state

    def _log_request(self, pid: str, request: List[int], result: RequestResult):
        self.request_log.append({
            "pid": pid,
            "request": request,
            "granted": result.granted,
            "reason": result.reason,
            "safe_sequence": result.safe_sequence,
            "timestamp": time.time(),
        })

    def reset(self):
        self.state = None
        self.request_log.clear()
