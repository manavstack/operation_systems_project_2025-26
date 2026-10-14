"""
D-RTOS Unit Tests: Process Synchronization
Validates Mutex locking locks, Counting Semaphores queue operations,
and buffer protection mutual exclusions.
"""

from __future__ import annotations
import unittest

from core.synchronization import SynchronizationManager

class TestSynchronization(unittest.TestCase):
    def setUp(self):
        self.sm = SynchronizationManager()
        
    def test_mutex_mutual_exclusion(self):
        buf = self.sm.radar_buffer
        buf.sync_type = "MUTEX"
        buf.sync_enabled = True
        
        # P1 acquires lock
        self.assertTrue(buf.acquire_access("P1"))
        self.assertEqual(buf.mutex.owner, "P1")
        
        # P2 tries to acquire lock and blocks (enters wait queue)
        self.assertFalse(buf.acquire_access("P2"))
        self.assertIn("P2", buf.mutex.waiting_queue)
        
        # P1 writes successfully
        res = buf.write("P1", "P1_TRACK_DATA")
        self.assertTrue(res["success"])
        
        # P2 tries to write and is blocked (no access)
        res_fail = buf.write("P2", "P2_TRACK_DATA")
        self.assertFalse(res_fail["success"])
        
        # P1 releases access, P2 auto acquires
        next_owner = buf.release_access("P1")
        self.assertEqual(next_owner, "P2")
        self.assertEqual(buf.mutex.owner, "P2")
        
    def test_semaphore_counting(self):
        buf = self.sm.radar_buffer
        buf.sync_type = "SEMAPHORE"
        buf.sync_enabled = True
        
        # Set max slot = 2
        buf.semaphore.max_count = 2
        buf.semaphore.count = 2
        
        # P1 acquires
        self.assertTrue(buf.acquire_access("P1"))
        self.assertEqual(buf.semaphore.count, 1)
        self.assertIn("P1", buf.semaphore.holders)
        
        # P2 acquires
        self.assertTrue(buf.acquire_access("P2"))
        self.assertEqual(buf.semaphore.count, 0)
        self.assertIn("P2", buf.semaphore.holders)
        
        # P3 tries to acquire and blocks
        self.assertFalse(buf.acquire_access("P3"))
        self.assertEqual(buf.semaphore.count, 0)
        self.assertIn("P3", buf.semaphore.waiting_queue)

if __name__ == "__main__":
    unittest.main()
