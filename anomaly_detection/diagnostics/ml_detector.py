"""
NEXUS Multi-Variate ML Anomaly Detector
Uses Isolation Forest to detect coupled cyber-physical anomalies (e.g., high motor power with zero flow).
"""

from typing import Tuple, Optional, List
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime, timezone
import logging

logger = logging.getLogger("nexus.anomaly.ml")


class MultivariateMLDetector:
    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            warm_start=False
        )
        self._is_fitted = False
        self._training_buffer: List[List[float]] = []
        self._init_baseline_model()

    def _init_baseline_model(self):
        """Initializes with nominal synthetic multi-variate operating envelopes."""
        np.random.seed(42)
        # 500 normal samples: [pressure (50-80), flow (40-70), temp (15-25), vibration (0.2-1.5), power (10-30)]
        pressures = np.random.normal(65.0, 5.0, 500)
        flows = np.random.normal(55.0, 6.0, 500)
        temps = np.random.normal(20.0, 2.0, 500)
        vibrations = np.random.exponential(0.5, 500)
        powers = 0.35 * flows + np.random.normal(5.0, 1.0, 500)  # Power correlates with flow

        X_train = np.column_stack([pressures, flows, temps, vibrations, powers])
        self.model.fit(X_train)
        self._is_fitted = True

    def evaluate_vector(
        self,
        pressure: float,
        flow: float,
        temp: float,
        vibration: float,
        power: float
    ) -> Tuple[bool, float, str]:
        """
        Evaluates 5-dimensional telemetry vector.
        Returns: (is_anomaly, anomaly_score, severity)
        """
        if not self._is_fitted:
            return False, 0.0, "NONE"

        X = np.array([[pressure, flow, temp, vibration, power]])
        pred = self.model.predict(X)[0]  # -1 = anomaly, 1 = normal
        score = -self.model.score_samples(X)[0]  # Higher score = more anomalous

        is_anomaly = (pred == -1)
        if is_anomaly:
            severity = "CRITICAL" if score > 0.7 else ("HIGH" if score > 0.6 else "MEDIUM")
            return True, round(float(score), 3), severity

        return False, round(float(score), 3), "NONE"


ml_detector = MultivariateMLDetector()
