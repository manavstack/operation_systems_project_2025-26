"""
D-RTOS Unit Tests: Banker's Algorithm
Validates safety sequence determination, requests approval and denials.
"""

from __future__ import annotations
import unittest

from core.banker import BankersAlgorithm, BankersState

class TestBanker(unittest.TestCase):
    def setUp(self):
        self.banker = BankersAlgorithm()
        
    def test_safe_state(self):
        # Setup textbook safe state
        state = BankersState(
            processes=["P0", "P1", "P2"],
            resources=["A", "B"],
            available=[2, 2],
            max_matrix=[
                [3, 2],
                [2, 1],
                [2, 2]
            ],
            allocation=[
                [1, 0],
                [1, 1],
                [0, 1]
            ]
        )
        self.banker.setup(state)
        res = self.banker.is_safe()
        self.assertTrue(res.is_safe)
        self.assertIn("P1", res.safe_sequence)
        
    def test_unsafe_request(self):
        state = BankersState(
            processes=["P0", "P1"],
            resources=["R1"],
            available=[1],
            max_matrix=[[3], [2]],
            allocation=[[1], [1]]
        )
        self.banker.setup(state)
        # P0 requests 2 units. Need is 2. Available is 1. Should be denied (insufficient available).
        res1 = self.banker.request_resources("P0", [2])
        self.assertFalse(res1.granted)
        
        # P0 requests 1 unit. If granted, available becomes 0. Need is 1. Allocation is 2.
        # Check safety: state becomes unsafe since no processes can finish.
        res2 = self.banker.request_resources("P0", [1])
        self.assertFalse(res2.granted)

if __name__ == "__main__":
    unittest.main()
