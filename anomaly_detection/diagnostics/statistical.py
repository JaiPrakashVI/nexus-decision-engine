"""
NEXUS Statistical Anomaly Detection
Interpretable streaming anomaly detection using Z-Score, Sliding Window EWMA, and Flatline Freeze Detection.
"""

from collections import deque
import math
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timezone
import logging

from database.queries.telemetry_repo import telemetry_repo

logger = logging.getLogger("nexus.anomaly.stats")


class StreamingStatisticalDetector:
    def __init__(self, window_size: int = 50, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        # device_id -> deque of recent metric values
        self._windows: Dict[str, Dict[str, deque]] = {}
        # Tracks flatline: device_id -> (last_value, repeat_count)
        self._flatlines: Dict[str, Dict[str, Tuple[float, int]]] = {}

    def _get_window(self, device_id: str, metric: str) -> deque:
        if device_id not in self._windows:
            self._windows[device_id] = {}
        if metric not in self._windows[device_id]:
            self._windows[device_id][metric] = deque(maxlen=self.window_size)
        return self._windows[device_id][metric]

    def check_reading(
        self,
        device_id: str,
        metric: str,
        value: float,
        timestamp: Optional[datetime] = None
    ) -> Tuple[bool, str, float, str]:
        """
        Evaluates a metric reading.
        Returns: (is_anomaly, anomaly_type, anomaly_score, severity)
        """
        now = timestamp or datetime.now(timezone.utc)
        win = self._get_window(device_id, metric)

        # 1. Flatline / Freeze Check
        if device_id not in self._flatlines:
            self._flatlines[device_id] = {}
        last_val, count = self._flatlines[device_id].get(metric, (value, 0))
        if abs(value - last_val) < 1e-5:
            count += 1
        else:
            count = 1
        self._flatlines[device_id][metric] = (value, count)

        if count >= 15:  # 15 identical consecutive floats indicates sensor freeze
            return True, "SENSOR_FLATLINE", 1.0, "HIGH"

        # 2. Need minimum samples for statistical validity
        if len(win) < 10:
            win.append(value)
            return False, "NORMAL", 0.0, "NONE"

        # Compute rolling mean and std
        n = len(win)
        mean = sum(win) / n
        variance = sum((x - mean) ** 2 for x in win) / n
        std = math.sqrt(variance) if variance > 1e-6 else 1e-4

        z_score = abs(value - mean) / std
        win.append(value)

        if z_score > self.z_threshold:
            severity = "CRITICAL" if z_score > 5.0 else ("HIGH" if z_score > 4.0 else "MEDIUM")
            anomaly_type = "SPIKE_HIGH" if value > mean else "DROP_LOW"
            return True, anomaly_type, round(z_score, 2), severity

        return False, "NORMAL", round(z_score, 2), "NONE"


statistical_detector = StreamingStatisticalDetector()
