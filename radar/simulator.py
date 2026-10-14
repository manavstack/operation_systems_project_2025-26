"""
D-RTOS: Radar Simulator
Generates simulated radar events (auto, manual, random, scenario-based).
All objects and values are fictional — no real-world defense significance.
"""

from __future__ import annotations
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable

from radar.classifier import ThreatClassifier
from core.process import ThreatLevel

OBJECT_TYPES = [
    "Friendly Aircraft",
    "Unknown Aircraft",
    "Drone",
    "Weather Object",
    "Unidentified Object",
    "Potential Threat",
    "Critical Threat",
]

DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
IFF_CODES  = ["FRIENDLY", "UNKNOWN", "HOSTILE", "NEUTRAL"]


@dataclass
class RadarObject:
    """A simulated radar detection. All values are fictional."""
    object_id: str
    object_type: str
    distance_km: float
    velocity_kmh: float
    direction: str
    iff_code: str
    threat_level: ThreatLevel
    detection_timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())

    @property
    def classification(self) -> str:
        return self.threat_level.name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "classification": self.classification,
            "threat_level": self.threat_level.name,
            "distance_km": round(self.distance_km, 1),
            "velocity_kmh": round(self.velocity_kmh, 1),
            "direction": self.direction,
            "iff_code": self.iff_code,
            "detection_timestamp": self.detection_timestamp,
        }

    def __str__(self) -> str:
        return (f"[{self.object_id}] {self.object_type} | "
                f"Dist={self.distance_km:.0f}km | Vel={self.velocity_kmh:.0f}km/h | "
                f"Dir={self.direction} | Threat={self.threat_level.name}")


class RadarSimulator:
    """
    Simulated radar that generates fictional radar detection events.
    Supports automatic, manual, random, and scenario-based generation.
    """

    def __init__(self, classifier: Optional[ThreatClassifier] = None):
        self.classifier = classifier or ThreatClassifier()
        self.detected_objects: List[RadarObject] = []
        self.event_handlers: List[Callable[[RadarObject], None]] = []
        self._object_counter: int = 100
        self.auto_running: bool = False
        self._auto_interval: float = 3.0      # seconds between auto events
        self._auto_thread = None
        self.threat_probability: float = 0.3  # probability of HIGH/CRITICAL

    # ------------------------------------------------------------------ #
    #  Object ID Generator                                                  #
    # ------------------------------------------------------------------ #
    def _next_id(self) -> str:
        self._object_counter += 1
        return f"R-{self._object_counter}"

    # ------------------------------------------------------------------ #
    #  Single Object Generation                                             #
    # ------------------------------------------------------------------ #
    def generate_random_object(self,
                                forced_type: Optional[str] = None,
                                forced_threat: Optional[str] = None) -> RadarObject:
        """Generate a single random radar object."""
        obj_type  = forced_type or random.choice(OBJECT_TYPES)
        distance  = round(random.uniform(10, 300), 1)
        velocity  = round(random.uniform(100, 1800), 1)
        direction = random.choice(DIRECTIONS)
        iff_code  = random.choice(IFF_CODES)

        if forced_threat:
            threat = ThreatLevel[forced_threat.upper()]
        else:
            # Adjust classifier critical boost by threat_probability setting
            self.classifier.critical_boost = max(0.0, self.threat_probability - 0.3)
            threat = self.classifier.classify(obj_type, distance, velocity, iff_code)

        obj = RadarObject(
            object_id=self._next_id(),
            object_type=obj_type,
            distance_km=distance,
            velocity_kmh=velocity,
            direction=direction,
            iff_code=iff_code,
            threat_level=threat,
        )
        self.detected_objects.append(obj)
        self._dispatch(obj)
        return obj

    def generate_manual(self, object_type: str, distance_km: float,
                         velocity_kmh: float, direction: str,
                         iff_code: str = "UNKNOWN",
                         forced_threat: Optional[str] = None) -> RadarObject:
        """Generate a manually specified radar object."""
        threat = (ThreatLevel[forced_threat.upper()] if forced_threat
                  else self.classifier.classify(object_type, distance_km, velocity_kmh, iff_code))
        obj = RadarObject(
            object_id=self._next_id(),
            object_type=object_type,
            distance_km=distance_km,
            velocity_kmh=velocity_kmh,
            direction=direction,
            iff_code=iff_code,
            threat_level=threat,
        )
        self.detected_objects.append(obj)
        self._dispatch(obj)
        return obj

    def generate_batch(self, count: int) -> List[RadarObject]:
        """Generate multiple random radar objects."""
        return [self.generate_random_object() for _ in range(count)]

    # ------------------------------------------------------------------ #
    #  Predefined Academic Scenarios                                        #
    # ------------------------------------------------------------------ #
    def generate_scenario(self, scenario: str) -> List[RadarObject]:
        """Generate a predefined scenario for academic demonstration."""
        scenarios = {
            "A": [  # Normal traffic
                ("Friendly Aircraft", 150, 600, "N", "FRIENDLY", "LOW"),
                ("Weather Object", 200, 50, "NE", "NEUTRAL", "LOW"),
                ("Friendly Aircraft", 100, 800, "E", "FRIENDLY", "LOW"),
            ],
            "B": [  # Multiple threats
                ("Unknown Aircraft", 80, 1200, "SW", "UNKNOWN", "HIGH"),
                ("Unknown Aircraft", 60, 1500, "S", "HOSTILE", "HIGH"),
                ("Critical Threat", 40, 1800, "SE", "HOSTILE", "CRITICAL"),
                ("Potential Threat", 90, 1000, "W", "UNKNOWN", "HIGH"),
            ],
            "C": [  # CPU overload — many processes
                ("Friendly Aircraft", 120, 500, "N", "FRIENDLY", "LOW"),
                ("Drone", 70, 300, "NE", "UNKNOWN", "MEDIUM"),
                ("Unknown Aircraft", 90, 900, "E", "UNKNOWN", "HIGH"),
                ("Unidentified Object", 50, 1200, "SE", "UNKNOWN", "HIGH"),
                ("Critical Threat", 30, 1800, "S", "HOSTILE", "CRITICAL"),
                ("Potential Threat", 80, 1100, "SW", "UNKNOWN", "HIGH"),
                ("Drone", 60, 400, "W", "UNKNOWN", "MEDIUM"),
            ],
            "D": [  # Deadline pressure
                ("Critical Threat", 25, 1800, "S", "HOSTILE", "CRITICAL"),
                ("Potential Threat", 45, 1500, "SE", "HOSTILE", "HIGH"),
                ("Unknown Aircraft", 65, 1200, "SW", "UNKNOWN", "HIGH"),
                ("Unidentified Object", 85, 1000, "W", "UNKNOWN", "MEDIUM"),
            ],
            "E": [  # Memory shortage — high memory processes
                ("Critical Threat", 20, 1800, "S", "HOSTILE", "CRITICAL"),
                ("Critical Threat", 25, 1700, "SE", "HOSTILE", "CRITICAL"),
                ("Potential Threat", 35, 1500, "SW", "HOSTILE", "HIGH"),
                ("Unknown Aircraft", 50, 1300, "W", "UNKNOWN", "HIGH"),
                ("Drone", 40, 600, "NW", "UNKNOWN", "MEDIUM"),
            ],
            "F": [  # Resource contention
                ("Critical Threat", 30, 1800, "S", "HOSTILE", "CRITICAL"),
                ("Potential Threat", 50, 1400, "SE", "HOSTILE", "HIGH"),
                ("Unknown Aircraft", 70, 1100, "E", "UNKNOWN", "HIGH"),
            ],
            "G": [  # Deadlock scenario — handled in deadlock module
                ("Unknown Aircraft", 60, 900, "NE", "UNKNOWN", "MEDIUM"),
                ("Potential Threat", 80, 1100, "E", "UNKNOWN", "HIGH"),
                ("Drone", 50, 500, "SE", "UNKNOWN", "MEDIUM"),
            ],
            "H": [  # Safe Banker's request
                ("Friendly Aircraft", 100, 700, "N", "FRIENDLY", "LOW"),
                ("Drone", 80, 400, "NE", "NEUTRAL", "MEDIUM"),
            ],
            "I": [  # Unsafe Banker's request
                ("Critical Threat", 35, 1700, "S", "HOSTILE", "CRITICAL"),
                ("Potential Threat", 55, 1300, "SW", "HOSTILE", "HIGH"),
                ("Unknown Aircraft", 75, 1000, "W", "UNKNOWN", "HIGH"),
            ],
            "J": [  # Synchronization — buffer competition
                ("Unknown Aircraft", 90, 800, "N", "UNKNOWN", "MEDIUM"),
                ("Drone", 60, 350, "NE", "UNKNOWN", "MEDIUM"),
                ("Unidentified Object", 70, 600, "E", "UNKNOWN", "MEDIUM"),
            ],
            "K": [  # Load imbalance
                ("Friendly Aircraft", 200, 500, "N", "FRIENDLY", "LOW"),
                ("Friendly Aircraft", 180, 550, "NE", "FRIENDLY", "LOW"),
                ("Critical Threat", 30, 1800, "S", "HOSTILE", "CRITICAL"),
                ("Critical Threat", 25, 1900, "SE", "HOSTILE", "CRITICAL"),
                ("Unknown Aircraft", 70, 1000, "SW", "UNKNOWN", "HIGH"),
            ],
        }

        objects = []
        for spec in scenarios.get(scenario.upper(), []):
            obj_type, dist, vel, direction, iff, threat = spec
            obj = self.generate_manual(obj_type, dist, vel, direction, iff, threat)
            objects.append(obj)
        return objects

    def generate_phase(self, phase: int) -> List[RadarObject]:
        """Generate objects for the 8-phase demonstration."""
        phases = {
            1: [("Friendly Aircraft", 150, 600, "N", "FRIENDLY", "LOW")],
            2: [("Unknown Aircraft", 82, 720, "NE", "UNKNOWN", "MEDIUM")],
            3: [("Critical Threat", 35, 1800, "S", "HOSTILE", "CRITICAL")],
            4: [("Friendly Aircraft", 120, 500, "N", "FRIENDLY", "LOW"),
                ("Unknown Aircraft", 95, 900, "E", "UNKNOWN", "HIGH"),
                ("Critical Threat", 40, 1700, "S", "HOSTILE", "CRITICAL"),
                ("Drone", 70, 300, "W", "UNKNOWN", "LOW")],
            5: [("Unknown Aircraft", 80, 850, "NW", "UNKNOWN", "MEDIUM"),
                ("Drone", 55, 400, "SW", "UNKNOWN", "MEDIUM")],
            6: [("Critical Threat", 30, 1900, "SE", "HOSTILE", "CRITICAL")],
            7: [],   # Completion — uses existing processes
            8: [],   # Analytics — no new objects
        }
        objects = []
        for spec in phases.get(phase, []):
            obj_type, dist, vel, direction, iff, threat = spec
            obj = self.generate_manual(obj_type, dist, vel, direction, iff, threat)
            objects.append(obj)
        return objects

    # ------------------------------------------------------------------ #
    #  Auto Generation                                                      #
    # ------------------------------------------------------------------ #
    def start_auto(self, interval: float = 3.0, callback: Optional[Callable] = None):
        """Start automatic radar event generation in a background thread."""
        import threading
        self._auto_interval = interval
        self.auto_running = True

        def _auto_loop():
            while self.auto_running:
                obj = self.generate_random_object()
                if callback:
                    callback(obj)
                time.sleep(self._auto_interval)

        self._auto_thread = threading.Thread(target=_auto_loop, daemon=True)
        self._auto_thread.start()

    def stop_auto(self):
        self.auto_running = False

    # ------------------------------------------------------------------ #
    #  Event Dispatch                                                       #
    # ------------------------------------------------------------------ #
    def on_detection(self, handler: Callable[[RadarObject], None]):
        self.event_handlers.append(handler)

    def _dispatch(self, obj: RadarObject):
        for handler in self.event_handlers:
            try:
                handler(obj)
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    #  Queries & Stats                                                      #
    # ------------------------------------------------------------------ #
    def get_all_objects(self) -> List[RadarObject]:
        return list(self.detected_objects)

    def get_by_threat(self, threat: ThreatLevel) -> List[RadarObject]:
        return [o for o in self.detected_objects if o.threat_level == threat]

    def counts_by_threat(self) -> Dict[str, int]:
        counts = {t.name: 0 for t in ThreatLevel}
        for obj in self.detected_objects:
            counts[obj.threat_level.name] += 1
        return counts

    def total_detected(self) -> int:
        return len(self.detected_objects)

    def reset(self):
        self.stop_auto()
        self.detected_objects.clear()
        self._object_counter = 100
        self.classifier.reset()
