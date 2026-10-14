"""
D-RTOS Unit Tests: Process Management
Validates process control block fields, priorities and transitions.
"""

from __future__ import annotations
import unittest

from core.process import ProcessState, ThreatLevel, next_pid
from core.pcb import PCB
from core.process_manager import ProcessManager

class TestProcess(unittest.TestCase):
    def setUp(self):
        self.pm = ProcessManager()
        
    def test_pcb_creation(self):
        pcb = self.pm.create_process(
            object_id="R-100",
            threat_level=ThreatLevel.CRITICAL,
            burst_time=5.0,
            deadline=10.0,
            memory_requirement=200
        )
        self.assertEqual(pcb.threat_level, ThreatLevel.CRITICAL)
        self.assertEqual(pcb.priority, 1)
        self.assertEqual(pcb.burst_time, 5.0)
        self.assertEqual(pcb.deadline, 10.0)
        self.assertEqual(pcb.memory_requirement, 200)
        self.assertEqual(pcb.state, ProcessState.NEW)
        
    def test_state_transitions(self):
        pcb = self.pm.create_process(object_id="R-101", threat_level=ThreatLevel.LOW)
        self.assertEqual(pcb.state, ProcessState.NEW)
        
        # NEW -> READY
        self.pm.admit_process(pcb)
        self.assertEqual(pcb.state, ProcessState.READY)
        self.assertIn(pcb, self.pm.ready_queue)
        
        # READY -> RUNNING
        self.pm.start_process(pcb, cpu_id=2)
        self.assertEqual(pcb.state, ProcessState.RUNNING)
        self.assertEqual(pcb.assigned_cpu, 2)
        self.assertEqual(self.pm.running_processes[2], pcb)
        
        # RUNNING -> WAITING
        self.pm.block_process(pcb, "Wait for disk")
        self.assertEqual(pcb.state, ProcessState.WAITING)
        self.assertIsNone(self.pm.running_processes[2])
        self.assertIn(pcb, self.pm.waiting_queue)
        
        # WAITING -> READY
        self.pm.unblock_process(pcb)
        self.assertEqual(pcb.state, ProcessState.READY)
        self.assertNotIn(pcb, self.pm.waiting_queue)
        self.assertIn(pcb, self.pm.ready_queue)
        
        # READY -> TERMINATED
        self.pm.terminate_process(pcb, simulation_time=15.0)
        self.assertEqual(pcb.state, ProcessState.TERMINATED)
        self.assertNotIn(pcb, self.pm.ready_queue)
        self.assertIn(pcb, self.pm.terminated)
        
    def test_dynamic_priority(self):
        pcb = self.pm.create_process(object_id="R-102", threat_level=ThreatLevel.LOW)
        self.assertEqual(pcb.priority, 4)
        self.pm.elevate_to_critical(pcb.pid)
        self.assertEqual(pcb.priority, 1)

if __name__ == "__main__":
    unittest.main()
