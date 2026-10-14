"""
D-RTOS: Memory Manager
Simulates fixed-size RAM with contiguous allocation strategies:
First Fit, Best Fit, Worst Fit.
Tracks fragmentation, utilization, and allocation failures.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import time


TOTAL_RAM_MB = 1024  # Simulated RAM in MB


@dataclass
class MemoryBlock:
    start: int          # Start address in MB
    size: int           # Block size in MB
    pid: Optional[str] = None
    process_name: Optional[str] = None
    allocated_at: float = field(default_factory=time.time)

    @property
    def end(self) -> int:
        return self.start + self.size

    @property
    def is_free(self) -> bool:
        return self.pid is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "size": self.size,
            "end": self.end,
            "pid": self.pid,
            "process_name": self.process_name,
            "is_free": self.is_free,
        }


class MemoryManager:
    """
    Contiguous memory allocation manager.
    Manages a fixed 1024 MB address space.
    Supports First Fit, Best Fit, Worst Fit allocation strategies.
    """

    def __init__(self, total_mb: int = TOTAL_RAM_MB):
        self.total_mb = total_mb
        self.blocks: List[MemoryBlock] = [MemoryBlock(0, total_mb)]  # One big free block
        self.allocation_log: List[Dict[str, Any]] = []
        self.failure_count: int = 0
        self.total_allocations: int = 0
        self.strategy: str = "First Fit"

    # ------------------------------------------------------------------ #
    #  Allocation                                                           #
    # ------------------------------------------------------------------ #
    def allocate(self, pid: str, process_name: str, size_mb: int,
                 strategy: Optional[str] = None) -> Optional[int]:
        """
        Allocate memory using the specified strategy.
        Returns start address on success, None on failure.
        """
        strat = (strategy or self.strategy).lower().replace(" ", "_")
        block = None

        free_blocks = [(i, b) for i, b in enumerate(self.blocks) if b.is_free and b.size >= size_mb]

        if not free_blocks:
            self.failure_count += 1
            self.allocation_log.append({
                "action": "FAILURE",
                "pid": pid,
                "requested_mb": size_mb,
                "reason": "No sufficient free block",
                "strategy": strat,
                "timestamp": time.time(),
            })
            return None

        if "first" in strat:
            idx, block = free_blocks[0]
        elif "best" in strat:
            idx, block = min(free_blocks, key=lambda x: x[1].size)
        elif "worst" in strat:
            idx, block = max(free_blocks, key=lambda x: x[1].size)
        else:
            idx, block = free_blocks[0]  # default first fit

        start = block.start

        # Split block if leftover
        if block.size > size_mb:
            leftover = MemoryBlock(start + size_mb, block.size - size_mb)
            self.blocks[idx] = MemoryBlock(start, size_mb, pid, process_name)
            self.blocks.insert(idx + 1, leftover)
        else:
            self.blocks[idx] = MemoryBlock(start, size_mb, pid, process_name)

        self.total_allocations += 1
        self.allocation_log.append({
            "action": "ALLOCATE",
            "pid": pid,
            "process_name": process_name,
            "start_address": start,
            "size_mb": size_mb,
            "strategy": strat,
            "timestamp": time.time(),
        })
        return start

    # ------------------------------------------------------------------ #
    #  Deallocation                                                         #
    # ------------------------------------------------------------------ #
    def deallocate(self, pid: str) -> bool:
        """Release all memory blocks belonging to a process."""
        freed = False
        for block in self.blocks:
            if block.pid == pid:
                block.pid = None
                block.process_name = None
                freed = True

        if freed:
            self._coalesce_free_blocks()
            self.allocation_log.append({
                "action": "DEALLOCATE",
                "pid": pid,
                "timestamp": time.time(),
            })
        return freed

    def _coalesce_free_blocks(self):
        """Merge adjacent free blocks to reduce external fragmentation."""
        merged = [self.blocks[0]]
        for block in self.blocks[1:]:
            last = merged[-1]
            if last.is_free and block.is_free:
                merged[-1] = MemoryBlock(last.start, last.size + block.size)
            else:
                merged.append(block)
        self.blocks = merged

    # ------------------------------------------------------------------ #
    #  Metrics                                                              #
    # ------------------------------------------------------------------ #
    @property
    def used_mb(self) -> int:
        return sum(b.size for b in self.blocks if not b.is_free)

    @property
    def free_mb(self) -> int:
        return self.total_mb - self.used_mb

    @property
    def utilization(self) -> float:
        return (self.used_mb / self.total_mb) * 100.0

    @property
    def fragmentation(self) -> float:
        """External fragmentation: % of free memory in non-contiguous blocks."""
        free_blocks = [b for b in self.blocks if b.is_free]
        if not free_blocks or self.free_mb == 0:
            return 0.0
        largest_free = max(b.size for b in free_blocks)
        return (1.0 - largest_free / self.free_mb) * 100.0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_mb": self.total_mb,
            "used_mb": self.used_mb,
            "free_mb": self.free_mb,
            "utilization": round(self.utilization, 1),
            "fragmentation": round(self.fragmentation, 1),
            "total_allocations": self.total_allocations,
            "allocation_failures": self.failure_count,
            "num_blocks": len(self.blocks),
            "num_free_blocks": sum(1 for b in self.blocks if b.is_free),
        }

    def get_blocks(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self.blocks]

    # ------------------------------------------------------------------ #
    #  Reset                                                               #
    # ------------------------------------------------------------------ #
    def reset(self):
        self.blocks = [MemoryBlock(0, self.total_mb)]
        self.allocation_log.clear()
        self.failure_count = 0
        self.total_allocations = 0
