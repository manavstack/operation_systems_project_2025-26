"""
D-RTOS: Deadlock Detection
Implements Resource Allocation Graph (RAG) with cycle detection
to identify potential deadlocks.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
import time


@dataclass
class RAGEdge:
    """Directed edge in the Resource Allocation Graph."""
    source: str         # PID (request) or resource name (assignment)
    target: str         # Resource name (request) or PID (assignment)
    edge_type: str      # "REQUEST" | "ASSIGNMENT"
    amount: int = 1


class DeadlockDetector:
    """
    Resource Allocation Graph (RAG) based deadlock detection.

    Nodes:
      - Process nodes (PIDs)
      - Resource nodes (resource names)

    Edges:
      - REQUEST edge:    process -> resource  (process waiting for resource)
      - ASSIGNMENT edge: resource -> process  (resource instance held by process)

    A cycle in the RAG indicates a potential deadlock.
    """

    def __init__(self):
        self.process_nodes: Set[str] = set()
        self.resource_nodes: Set[str] = set()
        self.request_edges: List[RAGEdge] = []      # process -> resource
        self.assignment_edges: List[RAGEdge] = []   # resource -> process
        self.detection_log: List[Dict[str, Any]] = []
        self.deadlock_history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    #  Graph Building                                                       #
    # ------------------------------------------------------------------ #
    def add_process(self, pid: str):
        self.process_nodes.add(pid)

    def remove_process(self, pid: str):
        self.process_nodes.discard(pid)
        self.request_edges = [e for e in self.request_edges if e.source != pid]
        self.assignment_edges = [e for e in self.assignment_edges if e.target != pid]

    def add_resource(self, name: str):
        self.resource_nodes.add(name)

    def add_request(self, pid: str, resource: str, amount: int = 1):
        """Add a request edge: process is waiting for resource."""
        self.process_nodes.add(pid)
        self.resource_nodes.add(resource)
        self.request_edges.append(RAGEdge(pid, resource, "REQUEST", amount))

    def add_assignment(self, resource: str, pid: str, amount: int = 1):
        """Add an assignment edge: resource is held by process."""
        self.process_nodes.add(pid)
        self.resource_nodes.add(resource)
        self.assignment_edges.append(RAGEdge(resource, pid, "ASSIGNMENT", amount))

    def remove_request(self, pid: str, resource: str):
        self.request_edges = [e for e in self.request_edges
                              if not (e.source == pid and e.target == resource)]

    def remove_assignment(self, resource: str, pid: str):
        self.assignment_edges = [e for e in self.assignment_edges
                                 if not (e.source == resource and e.target == pid)]

    def sync_from_resource_manager(self, allocation_table: Dict[str, Dict[str, int]],
                                    waiting: Dict[str, Dict[str, int]]):
        """
        Sync RAG from resource manager state.
        allocation_table: {pid: {resource: amount_held}}
        waiting: {pid: {resource: amount_requested}}
        """
        self.request_edges.clear()
        self.assignment_edges.clear()
        self.process_nodes = set(allocation_table.keys()) | set(waiting.keys())

        for pid, held in allocation_table.items():
            for res, amt in held.items():
                self.resource_nodes.add(res)
                self.assignment_edges.append(RAGEdge(res, pid, "ASSIGNMENT", amt))

        for pid, req in waiting.items():
            for res, amt in req.items():
                self.resource_nodes.add(res)
                self.request_edges.append(RAGEdge(pid, res, "REQUEST", amt))

    # ------------------------------------------------------------------ #
    #  Cycle Detection (DFS)                                               #
    # ------------------------------------------------------------------ #
    def detect_cycle(self) -> Tuple[bool, List[List[str]]]:
        """
        Detect cycles in the RAG using DFS.
        A cycle involving processes only (following request/assignment edges) is a deadlock.
        Returns (has_deadlock, list_of_cycles).
        """
        # Build adjacency: process -> [processes it's waiting on via resources]
        # P requests R, R is held by Q => P waits on Q
        held_by: Dict[str, str] = {}   # resource -> pid (simplified: first holder)
        for edge in self.assignment_edges:
            held_by[edge.source] = edge.target   # resource -> holder_pid

        wait_for: Dict[str, List[str]] = {pid: [] for pid in self.process_nodes}
        for edge in self.request_edges:
            req_resource = edge.target
            holder = held_by.get(req_resource)
            if holder and holder != edge.source:
                wait_for[edge.source].append(holder)

        # DFS cycle detection
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in wait_for.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle — extract it
                    cycle_start = path.index(neighbor)
                    cycles.append(list(path[cycle_start:]))
                    return True

            path.pop()
            rec_stack.discard(node)
            return False

        for pid in list(self.process_nodes):
            if pid not in visited:
                if dfs(pid, []):
                    pass  # continue to find all cycles

        has_deadlock = len(cycles) > 0

        # Log detection result
        entry = {
            "timestamp": time.time(),
            "has_deadlock": has_deadlock,
            "cycles": cycles,
            "processes": list(self.process_nodes),
        }
        self.detection_log.append(entry)

        if has_deadlock:
            self.deadlock_history.append(entry)

        return has_deadlock, cycles

    def describe_deadlock(self, cycles: List[List[str]]) -> str:
        """Return human-readable description of detected deadlock cycle."""
        if not cycles:
            return "No deadlock detected."
        lines = ["⚠  POTENTIAL DEADLOCK DETECTED\n"]
        for i, cycle in enumerate(cycles):
            chain = " → ".join(cycle + [cycle[0]])
            lines.append(f"  Cycle {i+1}: {chain}")

        # Explain resource dependency
        held_by: Dict[str, str] = {e.source: e.target for e in self.assignment_edges}
        lines.append("\nResource Dependencies:")
        for edge in self.request_edges:
            holder = held_by.get(edge.target, "?")
            if holder and holder != edge.source:
                lines.append(f"  {edge.source} needs {edge.target} (held by {holder})")
        return "\n".join(lines)

    def get_graph_data(self) -> Dict[str, Any]:
        return {
            "processes": list(self.process_nodes),
            "resources": list(self.resource_nodes),
            "request_edges": [(e.source, e.target) for e in self.request_edges],
            "assignment_edges": [(e.source, e.target) for e in self.assignment_edges],
        }

    def build_scenario(self, scenario: str = "classic"):
        """Build a predefined deadlock scenario for demonstration."""
        self.reset()
        if scenario == "classic":
            # Classic 3-process deadlock: P1→CPU→P2→GPU→P3→Comm→P1
            self.add_process("P1")
            self.add_process("P2")
            self.add_process("P3")
            self.add_resource("CPU")
            self.add_resource("GPU")
            self.add_resource("Communication")
            # Assignments
            self.add_assignment("CPU", "P1")
            self.add_assignment("GPU", "P2")
            self.add_assignment("Communication", "P3")
            # Requests (creates circular wait)
            self.add_request("P1", "GPU")
            self.add_request("P2", "Communication")
            self.add_request("P3", "CPU")

    def reset(self):
        self.process_nodes.clear()
        self.resource_nodes.clear()
        self.request_edges.clear()
        self.assignment_edges.clear()
        self.detection_log.clear()
