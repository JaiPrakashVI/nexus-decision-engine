"""
NEXUS Missing-Event & Dark Process Detection Engine
Detects unobserved transitions, skipped lifecycle phases, unexplained latencies, and unlogged interventions.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

from digital_twin.state.state_machine import ProcessPhase, NodeStateMachine
from database.queries.telemetry_repo import telemetry_repo

logger = logging.getLogger("nexus.dark_process")


@dataclass
class MissingEvent:
    device_id: str
    timestamp: datetime
    expected_transition: str
    observed_transition: str
    unexplained_latency_ms: float
    confidence: float
    root_cause_hypothesis: str
    details: Dict[str, Any] = field(default_factory=dict)


class DarkProcessDetector:
    def __init__(self):
        self._state_machines: Dict[str, NodeStateMachine] = {}
        self._missing_events: List[MissingEvent] = []
        self._total_transitions = 0
        self._skipped_transitions = 0

    def get_or_create_fsm(self, device_id: str) -> NodeStateMachine:
        if device_id not in self._state_machines:
            self._state_machines[device_id] = NodeStateMachine(ProcessPhase.OPERATIONAL)
        return self._state_machines[device_id]

    async def check_transition(
        self,
        device_id: str,
        target_phase: ProcessPhase,
        timestamp: Optional[datetime] = None,
        observed_latency_ms: float = 0.0
    ) -> Optional[MissingEvent]:
        now = timestamp or datetime.now(timezone.utc)
        fsm = self.get_or_create_fsm(device_id)
        current = fsm.current_phase
        self._total_transitions += 1

        is_permitted, missing_hint = fsm.transition(target_phase, now.timestamp())

        if not is_permitted:
            self._skipped_transitions += 1
            event = MissingEvent(
                device_id=device_id,
                timestamp=now,
                expected_transition=missing_hint or f"{current.value} -> intermediate -> {target_phase.value}",
                observed_transition=f"{current.value} -> {target_phase.value}",
                unexplained_latency_ms=observed_latency_ms,
                confidence=0.85,
                root_cause_hypothesis="Telemetry packet loss or unlogged physical emergency trip",
                details={
                    "prior_phase": current.value,
                    "target_phase": target_phase.value,
                }
            )
            self._missing_events.append(event)
            if len(self._missing_events) > 500:
                self._missing_events.pop(0)

            # Record in database asynchronously
            await telemetry_repo.record_missing_event(
                device_id=device_id,
                expected=event.expected_transition,
                observed=event.observed_transition,
                unexplained_latency_ms=observed_latency_ms,
                confidence=event.confidence,
                details=event.details,
                timestamp=now,
            )
            logger.warning(f"Dark Process Detected on '{device_id}': {event.observed_transition} [Expected: {event.expected_transition}]")
            return event

        return None

    def get_metrics(self) -> Dict[str, Any]:
        total = max(1, self._total_transitions)
        return {
            "total_transitions_evaluated": self._total_transitions,
            "detected_missing_transitions": self._skipped_transitions,
            "process_completeness_rate": round(1.0 - (self._skipped_transitions / total), 4),
            "dark_process_index": round(self._skipped_transitions / total, 4),
            "recent_missing_events": [
                {
                    "device_id": e.device_id,
                    "timestamp": e.timestamp.isoformat(),
                    "expected": e.expected_transition,
                    "observed": e.observed_transition,
                    "confidence": e.confidence,
                    "hypothesis": e.root_cause_hypothesis,
                }
                for e in self._missing_events[-10:]
            ]
        }


dark_process_detector = DarkProcessDetector()
