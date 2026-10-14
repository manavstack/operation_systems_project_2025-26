"""
D-RTOS: Process Synchronization
Implements Mutex, Counting Semaphore, and Radar Data Buffer protection.
Also demonstrates a controlled Race Condition scenario.

Note: This is NOT IPC. Synchronization is within the OS simulation
using shared simulated objects. No pipes, sockets, or message queues.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
import threading
import time
import random


# ============================================================
# Mutex
# ============================================================

class SimulatedMutex:
    """
    Binary mutex (mutual exclusion lock) for simulated OS synchronization.
    Simulates process-level mutual exclusion without real IPC.
    """

    def __init__(self, name: str):
        self.name = name
        self.owner: Optional[str] = None          # PID of holding process
        self.waiting_queue: List[str] = []        # PIDs waiting to acquire
        self.lock_count: int = 0
        self.acquisition_log: List[Dict[str, Any]] = []
        self._change_hooks: List[Callable] = []

    @property
    def is_locked(self) -> bool:
        return self.owner is not None

    def acquire(self, pid: str) -> bool:
        """
        Attempt to acquire the mutex.
        Returns True if acquired immediately, False if process must wait.
        """
        if not self.is_locked:
            self.owner = pid
            self.lock_count += 1
            self._log("ACQUIRED", pid)
            self._notify()
            return True
        else:
            if pid not in self.waiting_queue:
                self.waiting_queue.append(pid)
            self._log("WAITING", pid)
            self._notify()
            return False

    def release(self, pid: str) -> Optional[str]:
        """
        Release the mutex.
        Returns the PID of the next waiting process (or None).
        """
        if self.owner != pid:
            return None
        self._log("RELEASED", pid)
        self.owner = None

        next_pid = None
        if self.waiting_queue:
            next_pid = self.waiting_queue.pop(0)
            self.owner = next_pid
            self._log("ACQUIRED", next_pid, note="From wait queue")

        self._notify()
        return next_pid

    def force_release(self):
        """Force release (OS kills holder)."""
        if self.owner:
            self._log("FORCE_RELEASED", self.owner)
        self.owner = None
        self.waiting_queue.clear()
        self._notify()

    def _log(self, action: str, pid: str, note: str = ""):
        self.acquisition_log.append({
            "action": action,
            "pid": pid,
            "timestamp": time.time(),
            "owner_after": self.owner,
            "waiting": list(self.waiting_queue),
            "note": note,
        })

    def on_change(self, hook: Callable):
        self._change_hooks.append(hook)

    def _notify(self):
        for h in self._change_hooks:
            try:
                h(self)
            except Exception:
                pass

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "locked": self.is_locked,
            "owner": self.owner,
            "waiting": list(self.waiting_queue),
            "lock_count": self.lock_count,
        }

    def reset(self):
        self.owner = None
        self.waiting_queue.clear()
        self.lock_count = 0
        self.acquisition_log.clear()


# ============================================================
# Counting Semaphore
# ============================================================

class SimulatedSemaphore:
    """
    Counting semaphore for simulated OS synchronization.
    Controls access to N instances of a shared resource.
    """

    def __init__(self, name: str, initial_count: int = 1):
        self.name = name
        self.count: int = initial_count
        self.max_count: int = initial_count
        self.waiting_queue: List[str] = []
        self.holders: List[str] = []
        self.operation_log: List[Dict[str, Any]] = []
        self._change_hooks: List[Callable] = []

    @property
    def is_available(self) -> bool:
        return self.count > 0

    def wait(self, pid: str) -> bool:
        """
        P() / wait() operation.
        Decrements count; process blocks if count becomes < 0.
        Returns True if acquired, False if blocked.
        """
        if self.count > 0:
            self.count -= 1
            self.holders.append(pid)
            self._log("WAIT_SUCCESS", pid)
            self._notify()
            return True
        else:
            self.waiting_queue.append(pid)
            self._log("WAIT_BLOCKED", pid)
            self._notify()
            return False

    def signal(self, pid: str) -> Optional[str]:
        """
        V() / signal() operation.
        Increments count; wakes up one waiting process if any.
        Returns next unblocked PID or None.
        """
        if pid in self.holders:
            self.holders.remove(pid)
        self._log("SIGNAL", pid)

        if self.waiting_queue:
            next_pid = self.waiting_queue.pop(0)
            self.holders.append(next_pid)
            self._log("UNBLOCKED", next_pid)
            self._notify()
            return next_pid
        else:
            self.count = min(self.max_count, self.count + 1)
            self._notify()
            return None

    def _log(self, action: str, pid: str):
        self.operation_log.append({
            "action": action,
            "pid": pid,
            "count_after": self.count,
            "holders": list(self.holders),
            "waiting": list(self.waiting_queue),
            "timestamp": time.time(),
        })

    def on_change(self, hook: Callable):
        self._change_hooks.append(hook)

    def _notify(self):
        for h in self._change_hooks:
            try:
                h(self)
            except Exception:
                pass

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "max_count": self.max_count,
            "holders": list(self.holders),
            "waiting": list(self.waiting_queue),
        }

    def reset(self):
        self.count = self.max_count
        self.waiting_queue.clear()
        self.holders.clear()
        self.operation_log.clear()


# ============================================================
# Radar Data Buffer (Shared Resource)
# ============================================================

class RadarDataBuffer:
    """
    Shared simulated resource: RADAR DATA BUFFER.
    Protected by either a Mutex or Semaphore.
    Demonstrates mutual exclusion and race conditions.
    """

    def __init__(self):
        self.buffer_data: str = "[EMPTY]"
        self.write_count: int = 0
        self.read_count: int = 0
        self.corruption_events: List[Dict[str, Any]] = []
        self.access_log: List[Dict[str, Any]] = []

        # Protection mechanisms
        self.mutex = SimulatedMutex("RADAR_BUFFER_MUTEX")
        self.semaphore = SimulatedSemaphore("RADAR_BUFFER_SEM", initial_count=1)
        self.sync_enabled: bool = True
        self.sync_type: str = "MUTEX"   # "MUTEX" | "SEMAPHORE" | "NONE"
        self._change_hooks: List[Callable] = []

    def acquire_access(self, pid: str) -> bool:
        """
        Process attempts to access the buffer.
        Returns True if access granted, False if must wait.
        """
        if self.sync_type == "NONE" or not self.sync_enabled:
            self._log_access("UNPROTECTED_ACCESS", pid)
            return True
        elif self.sync_type == "MUTEX":
            return self.mutex.acquire(pid)
        else:  # SEMAPHORE
            return self.semaphore.wait(pid)

    def release_access(self, pid: str) -> Optional[str]:
        """Release buffer access. Returns next unblocked PID."""
        if self.sync_type == "MUTEX":
            return self.mutex.release(pid)
        elif self.sync_type == "SEMAPHORE":
            return self.semaphore.signal(pid)
        return None

    def write(self, pid: str, data: str, protected: bool = True) -> Dict[str, Any]:
        """Simulate writing to the radar buffer."""
        if protected and not self._can_access(pid):
            return {"success": False, "reason": "Access denied — mutex/semaphore locked"}

        # Simulate write
        old_data = self.buffer_data
        # Introduce artificial race condition when unprotected
        if not protected or self.sync_type == "NONE":
            time.sleep(0.001)   # Non-atomic window
            if random.random() < 0.3:
                self.buffer_data = f"CORRUPTED[{pid}+CONCURRENT]"
                corruption = {
                    "pid": pid,
                    "intended": data,
                    "actual": self.buffer_data,
                    "timestamp": time.time(),
                    "type": "RACE_CONDITION",
                }
                self.corruption_events.append(corruption)
                self._notify()
                return {"success": False, "corrupted": True, "data": self.buffer_data}
            else:
                self.buffer_data = data
        else:
            self.buffer_data = data

        self.write_count += 1
        self._log_access("WRITE", pid, old_data, data)
        self._notify()
        return {"success": True, "data": data}

    def read(self, pid: str) -> str:
        self.read_count += 1
        self._log_access("READ", pid, self.buffer_data)
        return self.buffer_data

    def _can_access(self, pid: str) -> bool:
        if self.sync_type == "MUTEX":
            return self.mutex.owner == pid
        elif self.sync_type == "SEMAPHORE":
            return pid in self.semaphore.holders
        return True

    def _log_access(self, action: str, pid: str, old_data: str = "", new_data: str = ""):
        self.access_log.append({
            "action": action,
            "pid": pid,
            "old_data": old_data,
            "new_data": new_data,
            "timestamp": time.time(),
            "sync_type": self.sync_type,
        })

    def on_change(self, hook: Callable):
        self._change_hooks.append(hook)
        self.mutex.on_change(lambda m: hook(self))
        self.semaphore.on_change(lambda s: hook(self))

    def _notify(self):
        for h in self._change_hooks:
            try:
                h(self)
            except Exception:
                pass

    def get_state(self) -> Dict[str, Any]:
        if self.sync_type == "MUTEX":
            lock_state = self.mutex.get_state()
        else:
            lock_state = self.semaphore.get_state()

        return {
            "buffer_data": self.buffer_data,
            "sync_type": self.sync_type,
            "sync_enabled": self.sync_enabled,
            "write_count": self.write_count,
            "read_count": self.read_count,
            "corruption_events": len(self.corruption_events),
            "lock_state": lock_state,
        }

    def reset(self):
        self.buffer_data = "[EMPTY]"
        self.write_count = 0
        self.read_count = 0
        self.corruption_events.clear()
        self.access_log.clear()
        self.mutex.reset()
        self.semaphore.reset()


# ============================================================
# Synchronization Manager (Facade)
# ============================================================

class SynchronizationManager:
    """
    Facade for all synchronization primitives.
    Manages the Radar Data Buffer and supports multi-process simulation.
    """

    def __init__(self):
        self.radar_buffer = RadarDataBuffer()
        self.named_mutexes: Dict[str, SimulatedMutex] = {}
        self.named_semaphores: Dict[str, SimulatedSemaphore] = {}
        self.event_log: List[Dict[str, Any]] = []

    def create_mutex(self, name: str) -> SimulatedMutex:
        m = SimulatedMutex(name)
        self.named_mutexes[name] = m
        return m

    def create_semaphore(self, name: str, count: int) -> SimulatedSemaphore:
        s = SimulatedSemaphore(name, count)
        self.named_semaphores[name] = s
        return s

    def simulate_competition(self, pids: List[str], sync_type: str = "MUTEX") -> List[Dict]:
        """
        Simulate multiple processes competing for the Radar Buffer.
        Returns sequence of events.
        """
        self.radar_buffer.reset()
        self.radar_buffer.sync_type = sync_type
        self.radar_buffer.sync_enabled = (sync_type != "NONE")
        events: List[Dict] = []

        for pid in pids:
            granted = self.radar_buffer.acquire_access(pid)
            events.append({
                "pid": pid,
                "action": "ACQUIRE",
                "granted": granted,
                "buffer_state": self.radar_buffer.get_state(),
            })

        # Simulate first holder writing
        if pids:
            holder = pids[0]
            result = self.radar_buffer.write(holder, f"RADAR_DATA_FROM_{holder}",
                                              protected=(sync_type != "NONE"))
            events.append({"pid": holder, "action": "WRITE", "result": result})

            next_pid = self.radar_buffer.release_access(holder)
            events.append({"pid": holder, "action": "RELEASE", "next": next_pid})

            # Second process (if waiting) now writes
            if next_pid and sync_type != "NONE":
                result2 = self.radar_buffer.write(next_pid, f"RADAR_DATA_FROM_{next_pid}", protected=True)
                events.append({"pid": next_pid, "action": "WRITE", "result": result2})
                self.radar_buffer.release_access(next_pid)

        return events

    def reset(self):
        self.radar_buffer.reset()
        for m in self.named_mutexes.values():
            m.reset()
        for s in self.named_semaphores.values():
            s.reset()
        self.event_log.clear()
