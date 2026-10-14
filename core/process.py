"""
D-RTOS: Process & PCB Core Definitions
Defines ProcessState, ThreatLevel, ProcessType enums and the base Process class.
"""

from __future__ import annotations
import time
import uuid
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import List, Optional, Dict


class ProcessState(Enum):
    """All possible OS process states."""
    NEW        = "NEW"
    READY      = "READY"
    RUNNING    = "RUNNING"
    WAITING    = "WAITING"
    TERMINATED = "TERMINATED"


class ThreatLevel(IntEnum):
    """Threat classification levels; lower value = higher urgency."""
    CRITICAL = 1
    HIGH     = 2
    MEDIUM   = 3
    LOW      = 4

    @property
    def label(self) -> str:
        return self.name

    @classmethod
    def from_string(cls, s: str) -> "ThreatLevel":
        return cls[s.upper()]


class ProcessType(Enum):
    """Types of OS processes generated from radar events."""
    CRITICAL_THREAT_ANALYSIS  = "Critical Threat Analysis"
    THREAT_ANALYSIS           = "Threat Analysis"
    OBJECT_TRACKING           = "Object Tracking"
    RADAR_SCAN                = "Radar Scan"
    COMMUNICATION             = "Communication"
    ROUTINE_PROCESSING        = "Routine Processing"
    LOGGING                   = "Logging"
    DRONE_TRACKING            = "Drone Tracking"
    WEATHER_MONITORING        = "Weather Monitoring"
    IDENTIFICATION            = "Identification"


# Mapping from ThreatLevel to process type, priority, default burst/deadline
THREAT_PROFILE: Dict[ThreatLevel, Dict] = {
    ThreatLevel.CRITICAL: {
        "process_type": ProcessType.CRITICAL_THREAT_ANALYSIS,
        "priority": 1,
        "burst_range": (4, 8),
        "deadline_range": (6, 12),
        "memory_range": (150, 300),
    },
    ThreatLevel.HIGH: {
        "process_type": ProcessType.THREAT_ANALYSIS,
        "priority": 2,
        "burst_range": (5, 10),
        "deadline_range": (10, 18),
        "memory_range": (100, 200),
    },
    ThreatLevel.MEDIUM: {
        "process_type": ProcessType.OBJECT_TRACKING,
        "priority": 3,
        "burst_range": (6, 12),
        "deadline_range": (15, 30),
        "memory_range": (60, 150),
    },
    ThreatLevel.LOW: {
        "process_type": ProcessType.RADAR_SCAN,
        "priority": 4,
        "burst_range": (3, 8),
        "deadline_range": (25, 45),
        "memory_range": (40, 100),
    },
}


_pid_counter = 0

def next_pid() -> str:
    global _pid_counter
    _pid_counter += 1
    return f"P{_pid_counter}"

def reset_pid_counter():
    global _pid_counter
    _pid_counter = 0
