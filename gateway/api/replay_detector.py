"""
NEXUS Replay & Duplicate Event Detector
Prevents replay attacks and duplicate transmissions by tracking sequence numbers and trace IDs.
Also verifies timestamp sanity against extreme clock drifts.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Set
from collections import deque
import threading


class ReplayDetector:
    def __init__(self, max_drift_past_sec: int = 300, max_drift_future_sec: int = 60, window_size: int = 1000):
        self.max_drift_past = timedelta(seconds=max_drift_past_sec)
        self.max_drift_future = timedelta(seconds=max_drift_future_sec)
        self.window_size = window_size
        self._lock = threading.Lock()
        
        # device_id -> highest sequence number seen
        self._highest_seq: Dict[str, int] = {}
        # Set of recent trace_ids for fast duplicate lookup
        self._seen_trace_ids: Set[str] = set()
        self._trace_id_queue: deque = deque()

    def check_and_record(self, device_id: str, seq_no: int, trace_id: str, timestamp: datetime) -> tuple[bool, str]:
        """
        Validates the event against replays, duplicates, and timestamp sanity.
        Returns: (is_valid, reason)
        """
        with self._lock:
            # 1. Trace ID uniqueness check
            if trace_id in self._seen_trace_ids:
                return False, f"Duplicate event: trace_id '{trace_id}' has already been processed"

            # 2. Timestamp sanity check
            now = datetime.now(timezone.utc)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            if now - timestamp > self.max_drift_past:
                return False, f"Event rejected: timestamp {timestamp.isoformat()} is too old (exceeds {self.max_drift_past.total_seconds()}s drift)"

            if timestamp - now > self.max_drift_future:
                return False, f"Event rejected: timestamp {timestamp.isoformat()} is too far in future (exceeds {self.max_drift_future.total_seconds()}s drift)"

            # 3. Record trace ID with bounded memory
            self._seen_trace_ids.add(trace_id)
            self._trace_id_queue.append(trace_id)
            if len(self._trace_id_queue) > self.window_size:
                old_id = self._trace_id_queue.popleft()
                self._seen_trace_ids.discard(old_id)

            # 4. Track highest sequence number (out-of-order warning or duplicate seq)
            current_max = self._highest_seq.get(device_id, -1)
            if seq_no > current_max:
                self._highest_seq[device_id] = seq_no

            return True, "Valid"

    def is_out_of_order(self, device_id: str, seq_no: int) -> bool:
        """Returns True if this sequence number is lower than the highest seen for this device."""
        with self._lock:
            highest = self._highest_seq.get(device_id)
            if highest is not None and seq_no < highest:
                return True
            return False


replay_detector = ReplayDetector()
