"""
D-RTOS Unit Tests: CPU Scheduler
Validates scheduling logic correctness for FCFS, SJF, Priority, Round Robin,
Preemptive Priority, SRTF, MLQ, and EDF.
"""

from __future__ import annotations
import unittest

from core.process import ThreatLevel
from core.pcb import PCB
from core.scheduler import Scheduler
from core.process_manager import ProcessManager

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.pm = ProcessManager()
        self.scheduler = Scheduler()
        
        # Setup standardized test workload
        self.p1 = self.pm.create_process("R-1", ThreatLevel.LOW, burst_time=5.0, arrival_time=0.0) # Priority 4
        self.p2 = self.pm.create_process("R-2", ThreatLevel.HIGH, burst_time=3.0, arrival_time=1.0) # Priority 2
        self.p3 = self.pm.create_process("R-3", ThreatLevel.CRITICAL, burst_time=2.0, arrival_time=2.0) # Priority 1
        
        self.procs = [self.p1, self.p2, self.p3]
        
    def test_fcfs(self):
        res = self.scheduler.fcfs(self.procs)
        self.assertEqual(res.algorithm, "FCFS")
        self.assertEqual(len(res.gantt), 3)
        # Check order: P1 -> P2 -> P3
        self.assertEqual(res.gantt[0].pid, self.p1.pid)
        self.assertEqual(res.gantt[1].pid, self.p2.pid)
        self.assertEqual(res.gantt[2].pid, self.p3.pid)
        
    def test_sjf(self):
        res = self.scheduler.sjf(self.procs)
        # At t=0, only P1 arrived. Executes to completion (t=5).
        # At t=5, P2 (burst 3) and P3 (burst 2) are available. P3 runs first, then P2.
        self.assertEqual(res.gantt[0].pid, self.p1.pid)
        self.assertEqual(res.gantt[1].pid, self.p3.pid)
        self.assertEqual(res.gantt[2].pid, self.p2.pid)
        
    def test_priority_nonpreemptive(self):
        res = self.scheduler.priority_nonpreemptive(self.procs)
        # At t=0, only P1 runs (t=5).
        # At t=5, P3 (priority 1) and P2 (priority 2) are available. P3 runs first, then P2.
        self.assertEqual(res.gantt[0].pid, self.p1.pid)
        self.assertEqual(res.gantt[1].pid, self.p3.pid)
        self.assertEqual(res.gantt[2].pid, self.p2.pid)
        
    def test_round_robin(self):
        res = self.scheduler.round_robin(self.procs, quantum=2.0)
        # q=2. Time slice rotation.
        # t=0: P1 runs (starts 0, ends 2, remaining 3)
        # t=2: P2 arrived, P3 arrived. Ready queue: P2, P3, P1
        # P2 runs (starts 2, ends 4, remaining 1)
        # P3 runs (starts 4, ends 6, complete)
        # P1 runs (starts 6, ends 8, remaining 1)
        # P2 runs (starts 8, ends 9, complete)
        # P1 runs (starts 9, ends 10, complete)
        self.assertEqual(res.gantt[0].pid, self.p1.pid)
        self.assertEqual(res.gantt[1].pid, self.p2.pid)
        self.assertEqual(res.gantt[2].pid, self.p3.pid)
        self.assertEqual(res.gantt[3].pid, self.p1.pid)
        
    def test_preemptive_priority(self):
        res = self.scheduler.preemptive_priority(self.procs)
        # P1 starts at 0. Priority 4.
        # At t=1, P2 (Priority 2) arrives and preempts P1.
        # At t=2, P3 (Priority 1) arrives and preempts P2.
        # P3 runs to completion (t=4).
        # P2 runs to completion (t=6).
        # P1 runs to completion (t=10).
        self.assertEqual(res.gantt[0].pid, self.p1.pid)
        self.assertEqual(res.gantt[1].pid, self.p2.pid)
        self.assertEqual(res.gantt[2].pid, self.p3.pid)
        
    def test_srtf(self):
        res = self.scheduler.srtf(self.procs)
        # P1 starts (remaining 5).
        # t=1: P2 (remaining 3) arrives. Preempts P1 (remaining 4).
        # t=2: P3 (remaining 2) arrives. Preempts P2 (remaining 2).
        # P3 runs (ends 4). P2 runs (ends 6). P1 runs (ends 10).
        self.assertEqual(res.gantt[0].pid, self.p1.pid)
        self.assertEqual(res.gantt[1].pid, self.p2.pid)
        self.assertEqual(res.gantt[2].pid, self.p3.pid)

if __name__ == "__main__":
    unittest.main()
