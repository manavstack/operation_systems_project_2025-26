"""
D-RTOS: Threat Classifier
Maps radar object attributes to OS threat levels and process profiles.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import random

from core.process import ThreatLevel, THREAT_PROFILE


# Object types and their base threat weights
OBJECT_THREAT_WEIGHTS: Dict[str, Dict[ThreatLevel, float]] = {
    "Friendly Aircraft":   {ThreatLevel.LOW: 0.85, ThreatLevel.MEDIUM: 0.10, ThreatLevel.HIGH: 0.05, ThreatLevel.CRITICAL: 0.00},
    "Unknown Aircraft":    {ThreatLevel.LOW: 0.10, ThreatLevel.MEDIUM: 0.35, ThreatLevel.HIGH: 0.40, ThreatLevel.CRITICAL: 0.15},
    "Drone":               {ThreatLevel.LOW: 0.20, ThreatLevel.MEDIUM: 0.30, ThreatLevel.HIGH: 0.30, ThreatLevel.CRITICAL: 0.20},
    "Weather Object":      {ThreatLevel.LOW: 0.90, ThreatLevel.MEDIUM: 0.09, ThreatLevel.HIGH: 0.01, ThreatLevel.CRITICAL: 0.00},
    "Unidentified Object": {ThreatLevel.LOW: 0.05, ThreatLevel.MEDIUM: 0.25, ThreatLevel.HIGH: 0.45, ThreatLevel.CRITICAL: 0.25},
    "Potential Threat":    {ThreatLevel.LOW: 0.00, ThreatLevel.MEDIUM: 0.15, ThreatLevel.HIGH: 0.50, ThreatLevel.CRITICAL: 0.35},
    "Critical Threat":     {ThreatLevel.LOW: 0.00, ThreatLevel.MEDIUM: 0.00, ThreatLevel.HIGH: 0.20, ThreatLevel.CRITICAL: 0.80},
}


class ThreatClassifier:
    """
    Classifies detected radar objects into OS threat levels.
    Considers object type, velocity, distance, and configurable probability.
    """

    def __init__(self, critical_boost: float = 0.0):
        """
        critical_boost: 0.0–1.0 additional probability shifted toward CRITICAL.
        Used to configure simulated threat environments.
        """
        self.critical_boost = max(0.0, min(1.0, critical_boost))
        self.classification_log: list = []

    def classify(self, object_type: str, distance_km: float,
                 velocity_kmh: float, iff_code: str = "UNKNOWN") -> ThreatLevel:
        """
        Classify a radar object into a ThreatLevel.
        All inputs are simulated values with no real-world significance.
        """
        weights = dict(OBJECT_THREAT_WEIGHTS.get(object_type, OBJECT_THREAT_WEIGHTS["Unidentified Object"]))

        # Velocity modifier: fast + close = more dangerous
        if velocity_kmh > 1000 and distance_km < 50:
            weights[ThreatLevel.CRITICAL] = min(1.0, weights[ThreatLevel.CRITICAL] + 0.20)
            weights[ThreatLevel.HIGH]     = min(1.0, weights[ThreatLevel.HIGH] + 0.10)
        elif velocity_kmh > 600 and distance_km < 100:
            weights[ThreatLevel.HIGH]     = min(1.0, weights[ThreatLevel.HIGH] + 0.10)

        # Distance modifier: very close objects escalate
        if distance_km < 30:
            weights[ThreatLevel.CRITICAL] = min(1.0, weights[ThreatLevel.CRITICAL] + 0.15)
        elif distance_km < 60:
            weights[ThreatLevel.HIGH]     = min(1.0, weights[ThreatLevel.HIGH] + 0.10)

        # IFF modifier
        if iff_code == "HOSTILE":
            weights[ThreatLevel.CRITICAL] = min(1.0, weights[ThreatLevel.CRITICAL] + 0.30)
        elif iff_code == "FRIENDLY":
            weights[ThreatLevel.LOW]      = min(1.0, weights[ThreatLevel.LOW] + 0.30)

        # Critical boost (configurable threat environment)
        if self.critical_boost > 0:
            shift = self.critical_boost * 0.3
            weights[ThreatLevel.CRITICAL] = min(1.0, weights[ThreatLevel.CRITICAL] + shift)

        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        # Weighted random selection
        levels = list(weights.keys())
        probs  = [weights[l] for l in levels]
        threat = random.choices(levels, weights=probs, k=1)[0]

        self.classification_log.append({
            "object_type": object_type,
            "distance_km": distance_km,
            "velocity_kmh": velocity_kmh,
            "iff_code": iff_code,
            "threat_level": threat.name,
        })
        return threat

    def classify_forced(self, threat_str: str) -> ThreatLevel:
        """Force a specific threat level (for manual/demo scenarios)."""
        return ThreatLevel[threat_str.upper()]

    def get_priority(self, threat: ThreatLevel) -> int:
        return THREAT_PROFILE[threat]["priority"]

    def get_process_profile(self, threat: ThreatLevel) -> Dict[str, Any]:
        return dict(THREAT_PROFILE[threat])

    def reset(self):
        self.classification_log.clear()
