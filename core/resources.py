"""
D-RTOS: Resource Manager
Manages multi-instance system resources.
Processes request/release resources; manager validates availability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time


# Default simulated system resources
DEFAULT_RESOURCES = {
    "CPU":                  4,
    "RAM":                  8,
    "Radar Processor":      2,
    "GPU":                  2,
    "Communication Channel": 3,
    "Storage":              4,
}


@dataclass
class Resource:
    name: str
    total: int
    available: int = 0

    def __post_init__(self):
        if self.available == 0:
            self.available = self.total

    @property
    def allocated(self) -> int:
        return self.total - self.available

    @property
    def utilization(self) -> float:
        return (self.allocated / self.total * 100.0) if self.total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total": self.total,
            "available": self.available,
            "allocated": self.allocated,
            "utilization": round(self.utilization, 1),
        }


class ResourceManager:
    """
    Multi-instance resource manager.
    Tracks available vs allocated resource instances.
    Processes can request and release resource bundles.
    """

    def __init__(self, resource_config: Optional[Dict[str, int]] = None):
        cfg = resource_config or DEFAULT_RESOURCES
        self.resources: Dict[str, Resource] = {
            name: Resource(name, total) for name, total in cfg.items()
        }
        # Allocation table: pid -> {resource_name -> amount_held}
        self.allocation_table: Dict[str, Dict[str, int]] = {}
        self.request_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    #  Request & Release                                                    #
    # ------------------------------------------------------------------ #
    def request(self, pid: str, request: Dict[str, int]) -> bool:
        """
        Request resources for a process.
        Returns True if allocation succeeded, False if insufficient resources.
        """
        # Validate availability
        for res_name, amount in request.items():
            res = self.resources.get(res_name)
            if res is None or res.available < amount:
                self.request_log.append({
                    "action": "REQUEST_DENIED",
                    "pid": pid,
                    "request": request,
                    "reason": f"Insufficient {res_name}",
                    "timestamp": time.time(),
                })
                return False

        # Allocate
        for res_name, amount in request.items():
            self.resources[res_name].available -= amount
            if pid not in self.allocation_table:
                self.allocation_table[pid] = {}
            self.allocation_table[pid][res_name] = (
                self.allocation_table[pid].get(res_name, 0) + amount
            )

        self.request_log.append({
            "action": "REQUEST_GRANTED",
            "pid": pid,
            "request": request,
            "timestamp": time.time(),
        })
        return True

    def release(self, pid: str) -> Dict[str, int]:
        """Release all resources held by a process."""
        held = self.allocation_table.pop(pid, {})
        for res_name, amount in held.items():
            if res_name in self.resources:
                self.resources[res_name].available = min(
                    self.resources[res_name].total,
                    self.resources[res_name].available + amount,
                )
        if held:
            self.request_log.append({
                "action": "RELEASE",
                "pid": pid,
                "released": held,
                "timestamp": time.time(),
            })
        return held

    def release_partial(self, pid: str, release_map: Dict[str, int]) -> bool:
        """Release a specific subset of resources held by a process."""
        held = self.allocation_table.get(pid, {})
        for res_name, amount in release_map.items():
            if held.get(res_name, 0) < amount:
                return False
        for res_name, amount in release_map.items():
            held[res_name] -= amount
            if held[res_name] == 0:
                del held[res_name]
            self.resources[res_name].available += amount
        return True

    # ------------------------------------------------------------------ #
    #  Queries                                                              #
    # ------------------------------------------------------------------ #
    def get_available(self) -> Dict[str, int]:
        return {name: r.available for name, r in self.resources.items()}

    def get_allocation(self, pid: str) -> Dict[str, int]:
        return self.allocation_table.get(pid, {})

    def can_satisfy(self, request: Dict[str, int]) -> bool:
        return all(
            self.resources.get(name, Resource("", 0)).available >= amount
            for name, amount in request.items()
        )

    def get_all_stats(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.resources.values()]

    def get_allocation_table(self) -> Dict[str, Dict[str, int]]:
        return dict(self.allocation_table)

    def reset(self):
        for res in self.resources.values():
            res.available = res.total
        self.allocation_table.clear()
        self.request_log.clear()
