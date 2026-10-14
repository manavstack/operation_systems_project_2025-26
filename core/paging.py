"""
D-RTOS: Paging Manager
Implements logical-to-physical address translation via page tables.
Includes page replacement algorithms: FIFO and LRU.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import OrderedDict
import time

PAGE_SIZE_MB = 32       # Each page/frame = 32 MB
TOTAL_RAM_MB = 1024
NUM_FRAMES   = TOTAL_RAM_MB // PAGE_SIZE_MB   # 32 frames


@dataclass
class PageTableEntry:
    page_number: int
    frame_number: int
    valid: bool = True
    dirty: bool = False
    reference_count: int = 0


@dataclass
class PageReplacementStep:
    reference: int
    frames: List[Optional[int]]
    is_fault: bool
    evicted: Optional[int] = None
    algorithm: str = ""


class PagingManager:
    """
    Page-based memory management.
    - Maintains a per-process page table mapping logical pages to physical frames.
    - Provides address translation: logical_address -> physical_address.
    - Implements FIFO and LRU page replacement simulation on a reference string.
    """

    def __init__(self, page_size_mb: int = PAGE_SIZE_MB, total_ram_mb: int = TOTAL_RAM_MB):
        self.page_size = page_size_mb
        self.total_frames = total_ram_mb // page_size_mb
        # Frame table: frame_id -> pid or None
        self.frame_table: Dict[int, Optional[str]] = {i: None for i in range(self.total_frames)}
        # Per-process page tables
        self.page_tables: Dict[str, Dict[int, PageTableEntry]] = {}
        self.page_fault_count: int = 0
        self.page_hit_count: int = 0

    # ------------------------------------------------------------------ #
    #  Process Page Allocation                                              #
    # ------------------------------------------------------------------ #
    def allocate_pages(self, pid: str, num_pages: int) -> bool:
        """Allocate physical frames for a process."""
        free_frames = [f for f, p in self.frame_table.items() if p is None]
        if len(free_frames) < num_pages:
            return False

        page_table: Dict[int, PageTableEntry] = {}
        for page_num in range(num_pages):
            frame = free_frames[page_num]
            self.frame_table[frame] = pid
            page_table[page_num] = PageTableEntry(page_num, frame)

        self.page_tables[pid] = page_table
        return True

    def deallocate_pages(self, pid: str):
        """Release all frames belonging to a process."""
        if pid in self.page_tables:
            for entry in self.page_tables[pid].values():
                self.frame_table[entry.frame_number] = None
            del self.page_tables[pid]

    def pages_required(self, memory_mb: int) -> int:
        """Calculate number of pages needed for given memory size."""
        return (memory_mb + self.page_size - 1) // self.page_size

    # ------------------------------------------------------------------ #
    #  Address Translation                                                  #
    # ------------------------------------------------------------------ #
    def translate(self, pid: str, logical_address: int) -> Optional[Tuple[int, int, int, int]]:
        """
        Translate a logical address to a physical address.
        Returns (page_number, offset, frame_number, physical_address) or None on page fault.
        """
        page_number = logical_address // self.page_size
        offset      = logical_address %  self.page_size

        pt = self.page_tables.get(pid, {})
        entry = pt.get(page_number)

        if entry is None or not entry.valid:
            self.page_fault_count += 1
            return None

        self.page_hit_count += 1
        entry.reference_count += 1
        physical_address = entry.frame_number * self.page_size + offset
        return (page_number, offset, entry.frame_number, physical_address)

    def get_page_table(self, pid: str) -> List[Dict[str, Any]]:
        pt = self.page_tables.get(pid, {})
        return [
            {
                "page": e.page_number,
                "frame": e.frame_number,
                "valid": e.valid,
                "dirty": e.dirty,
                "ref_count": e.reference_count,
                "logical_base": e.page_number * self.page_size,
                "physical_base": e.frame_number * self.page_size,
            }
            for e in sorted(pt.values(), key=lambda x: x.page_number)
        ]

    # ------------------------------------------------------------------ #
    #  Page Replacement Simulation                                          #
    # ------------------------------------------------------------------ #
    def simulate_fifo(self, reference_string: List[int], num_frames: int) -> Tuple[List[PageReplacementStep], int]:
        """
        FIFO page replacement simulation.
        Returns (steps, total_page_faults).
        """
        frames: List[Optional[int]] = [None] * num_frames
        queue: List[int] = []
        steps: List[PageReplacementStep] = []
        faults = 0

        for ref in reference_string:
            if ref in frames:
                steps.append(PageReplacementStep(ref, list(frames), False, algorithm="FIFO"))
            else:
                faults += 1
                evicted = None
                if None in frames:
                    idx = frames.index(None)
                    frames[idx] = ref
                    queue.append(ref)
                else:
                    evicted = queue.pop(0)
                    idx = frames.index(evicted)
                    frames[idx] = ref
                    queue.append(ref)
                steps.append(PageReplacementStep(ref, list(frames), True, evicted, "FIFO"))

        return steps, faults

    def simulate_lru(self, reference_string: List[int], num_frames: int) -> Tuple[List[PageReplacementStep], int]:
        """
        LRU page replacement simulation using an ordered dict.
        Returns (steps, total_page_faults).
        """
        frames: OrderedDict[int, int] = OrderedDict()   # page -> last_used_index
        steps: List[PageReplacementStep] = []
        faults = 0

        for i, ref in enumerate(reference_string):
            if ref in frames:
                frames.move_to_end(ref)
                current = list(frames.keys())
                padded = current + [None] * (num_frames - len(current))
                steps.append(PageReplacementStep(ref, padded[:num_frames], False, algorithm="LRU"))
            else:
                faults += 1
                evicted = None
                if len(frames) >= num_frames:
                    evicted, _ = frames.popitem(last=False)
                frames[ref] = i
                frames.move_to_end(ref)
                current = list(frames.keys())
                padded = current + [None] * (num_frames - len(current))
                steps.append(PageReplacementStep(ref, padded[:num_frames], True, evicted, "LRU"))

        return steps, faults

    def compare_algorithms(self, reference_string: List[int], num_frames: int) -> Dict[str, Any]:
        """Compare FIFO vs LRU on the same reference string."""
        fifo_steps, fifo_faults = self.simulate_fifo(reference_string, num_frames)
        lru_steps,  lru_faults  = self.simulate_lru(reference_string, num_frames)
        total = len(reference_string)
        return {
            "reference_string": reference_string,
            "num_frames": num_frames,
            "total_references": total,
            "fifo": {
                "page_faults": fifo_faults,
                "page_hits": total - fifo_faults,
                "fault_rate": round(fifo_faults / total * 100, 1) if total else 0,
                "steps": [
                    {"ref": s.reference, "frames": s.frames, "fault": s.is_fault, "evicted": s.evicted}
                    for s in fifo_steps
                ],
            },
            "lru": {
                "page_faults": lru_faults,
                "page_hits": total - lru_faults,
                "fault_rate": round(lru_faults / total * 100, 1) if total else 0,
                "steps": [
                    {"ref": s.reference, "frames": s.frames, "fault": s.is_fault, "evicted": s.evicted}
                    for s in lru_steps
                ],
            },
            "winner": "LRU" if lru_faults < fifo_faults else ("FIFO" if fifo_faults < lru_faults else "TIE"),
        }

    def get_stats(self) -> Dict[str, Any]:
        free_frames = sum(1 for v in self.frame_table.values() if v is None)
        return {
            "total_frames": self.total_frames,
            "free_frames": free_frames,
            "used_frames": self.total_frames - free_frames,
            "page_faults": self.page_fault_count,
            "page_hits": self.page_hit_count,
            "active_processes": len(self.page_tables),
        }

    def reset(self):
        self.frame_table = {i: None for i in range(self.total_frames)}
        self.page_tables.clear()
        self.page_fault_count = 0
        self.page_hit_count = 0
