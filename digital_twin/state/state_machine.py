"""
NEXUS Cyber-Physical State Machine
Defines permitted operational state transitions, transition timing bounds, and transition validation.
"""

from typing import Dict, Set, Optional, Tuple
from enum import Enum


class ProcessPhase(str, Enum):
    OFFLINE = "OFFLINE"
    STARTING = "STARTING"
    OPERATIONAL = "OPERATIONAL"
    THROTTLED = "THROTTLED"
    ALERT = "ALERT"
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"
    MAINTENANCE = "MAINTENANCE"


# Permitted directed transitions in the normal physical lifecycle
PERMITTED_TRANSITIONS: Dict[ProcessPhase, Set[ProcessPhase]] = {
    ProcessPhase.OFFLINE: {ProcessPhase.STARTING, ProcessPhase.MAINTENANCE},
    ProcessPhase.STARTING: {ProcessPhase.OPERATIONAL, ProcessPhase.OFFLINE, ProcessPhase.ALERT},
    ProcessPhase.OPERATIONAL: {ProcessPhase.THROTTLED, ProcessPhase.ALERT, ProcessPhase.MAINTENANCE, ProcessPhase.OFFLINE},
    ProcessPhase.THROTTLED: {ProcessPhase.OPERATIONAL, ProcessPhase.ALERT, ProcessPhase.OFFLINE},
    ProcessPhase.ALERT: {ProcessPhase.THROTTLED, ProcessPhase.EMERGENCY_SHUTDOWN, ProcessPhase.OPERATIONAL},
    ProcessPhase.EMERGENCY_SHUTDOWN: {ProcessPhase.MAINTENANCE, ProcessPhase.OFFLINE},
    ProcessPhase.MAINTENANCE: {ProcessPhase.OFFLINE, ProcessPhase.STARTING},
}


class NodeStateMachine:
    def __init__(self, initial_phase: ProcessPhase = ProcessPhase.OPERATIONAL):
        self.current_phase: ProcessPhase = initial_phase
        self.history: list[Tuple[ProcessPhase, float]] = []

    def can_transition(self, to_phase: ProcessPhase) -> bool:
        allowed = PERMITTED_TRANSITIONS.get(self.current_phase, set())
        return to_phase in allowed

    def transition(self, to_phase: ProcessPhase, timestamp: float) -> Tuple[bool, Optional[str]]:
        """
        Executes transition if valid. If invalid/skipped, flags missing intermediate transition.
        Returns: (is_permitted, missing_intermediate_hint)
        """
        if to_phase == self.current_phase:
            return True, None

        if self.can_transition(to_phase):
            self.history.append((self.current_phase, timestamp))
            self.current_phase = to_phase
            return True, None
        else:
            # Detect candidate missing intermediate transition (Dark Process)
            missing_hint = self._infer_missing_step(self.current_phase, to_phase)
            self.history.append((self.current_phase, timestamp))
            self.current_phase = to_phase
            return False, missing_hint

    def _infer_missing_step(self, current: ProcessPhase, target: ProcessPhase) -> str:
        if current == ProcessPhase.OPERATIONAL and target == ProcessPhase.EMERGENCY_SHUTDOWN:
            return "ALERT (Telemetry gap: missing critical threshold alert event)"
        if current == ProcessPhase.OFFLINE and target == ProcessPhase.OPERATIONAL:
            return "STARTING (Telemetry gap: missing priming/startup verification)"
        return f"Unknown intermediate step between {current.value} and {target.value}"
