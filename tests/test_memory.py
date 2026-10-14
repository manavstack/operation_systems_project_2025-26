"""
D-RTOS Unit Tests: Memory Management
Validates First Fit, Best Fit, and Worst Fit contiguous partition managers,
logical address translation paging, and FIFO/LRU replacement counts.
"""

from __future__ import annotations
import unittest

from core.memory import MemoryManager
from core.paging import PagingManager

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.mm = MemoryManager(total_mb=1024)
        self.pm = PagingManager(page_size_mb=32, total_ram_mb=1024)
        
    def test_contiguous_allocations(self):
        # 1. Test First Fit
        self.mm.strategy = "First Fit"
        start_p1 = self.mm.allocate("P1", "Proc1", 200)
        self.assertEqual(start_p1, 0)
        
        start_p2 = self.mm.allocate("P2", "Proc2", 300)
        self.assertEqual(start_p2, 200)
        
        # Deallocate P1 (creates a free block size 200 at 0)
        self.mm.deallocate("P1")
        
        # Allocate P3 size 100. In First Fit it should occupy the block at 0
        start_p3 = self.mm.allocate("P3", "Proc3", 100)
        self.assertEqual(start_p3, 0)
        
    def test_best_fit(self):
        # Setup blocks with dividers so they don't coalesce
        self.mm.allocate("H1", "H", 100) # 0-100 (Free soon)
        self.mm.allocate("D1", "D", 50)  # 100-150 (Keep Allocated)
        self.mm.allocate("H2", "H", 300) # 150-450 (Free soon)
        self.mm.allocate("D2", "D", 50)  # 450-500 (Keep Allocated)
        self.mm.allocate("H3", "H", 150) # 500-650 (Free soon)
        self.mm.allocate("D3", "D", 374) # 650-1024 (Keep Allocated)
        
        self.mm.deallocate("H1")
        self.mm.deallocate("H2")
        self.mm.deallocate("H3")
        
        # Free holes: 100 MB at 0, 300 MB at 150, 150 MB at 500
        # Request 120 MB. Best Fit should select Hole 3 (150 MB at 500).
        start = self.mm.allocate("P5", "Proc5", 120, strategy="Best Fit")
        self.assertEqual(start, 500)
        
    def test_worst_fit(self):
        self.mm.allocate("H1", "H", 100) # 0-100 (Free soon)
        self.mm.allocate("D1", "D", 50)  # 100-150 (Keep Allocated)
        self.mm.allocate("H2", "H", 300) # 150-450 (Free soon)
        self.mm.allocate("D2", "D", 50)  # 450-500 (Keep Allocated)
        self.mm.allocate("H3", "H", 150) # 500-650 (Free soon)
        self.mm.allocate("D3", "D", 374) # 650-1024 (Keep Allocated)
        
        self.mm.deallocate("H1")
        self.mm.deallocate("H2")
        self.mm.deallocate("H3")
        
        # Free holes: 100 MB at 0, 300 MB at 150, 150 MB at 500
        # Request 120 MB. Worst Fit should select the largest hole: 300 MB at 150.
        start = self.mm.allocate("P5", "Proc5", 120, strategy="Worst Fit")
        self.assertEqual(start, 150)
        
    def test_paging_translation(self):
        # Allocate pages for a process
        success = self.pm.allocate_pages("P1", num_pages=4) # Maps to frame 0, 1, 2, 3
        self.assertTrue(success)
        
        # Logical address 70. Page size 32 MB.
        # pg = 70 // 32 = 2. offset = 70 % 32 = 6.
        # pg 2 should map to frame 2. physical address = 2 * 32 + 6 = 70.
        res = self.pm.translate("P1", 70)
        self.assertIsNotNone(res)
        pg, off, frame, phy = res
        self.assertEqual(pg, 2)
        self.assertEqual(off, 6)
        self.assertEqual(frame, 2)
        self.assertEqual(phy, 70)
        
    def test_page_replacements(self):
        ref_str = [7, 0, 1, 2, 0, 3, 0, 4]
        
        # FIFO replacement faults with 3 frames
        _, fifo_faults = self.pm.simulate_fifo(ref_str, num_frames=3)
        self.assertEqual(fifo_faults, 7) # Expected: 7
        
        # LRU replacement faults with 3 frames
        _, lru_faults = self.pm.simulate_lru(ref_str, num_frames=3)
        self.assertEqual(lru_faults, 6) # Expected: 6


if __name__ == "__main__":
    unittest.main()
