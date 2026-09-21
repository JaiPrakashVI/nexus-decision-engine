"""
NEXUS Fault Injection & Data Degradation Engine
Applies configurable telemetry packet loss (0-40%), transmission delays, sensor noise,
duplicate events, out-of-order sequencing, and malformed corruption.
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass
import random
import numpy as np
import copy
from datetime import datetime, timezone, timedelta

from gateway.schemas.telemetry import TelemetryPayload


@dataclass
class FaultInjectionConfig:
    loss_rate: float = 0.0          # 0.0 to 0.40 (0% to 40% packet drops)
    delay_ms: int = 0               # Latency in ms (0, 50, 100, 500, 1000)
    noise_level: str = "none"       # none, low, medium, high
    out_of_order: bool = False      # Shuffle transmission ordering
    duplicates: bool = False        # Duplicate transmission
    corruption: bool = False        # Malformed packet corruption
    seed: int = 42


class FaultInjector:
    def __init__(self, config: Optional[FaultInjectionConfig] = None):
        self.config = config or FaultInjectionConfig()
        self.rng = random.Random(self.config.seed)
        self.np_rng = np.random.default_rng(self.config.seed)
        self._delay_queue: List[Tuple[float, TelemetryPayload]] = []

    def set_config(self, config: FaultInjectionConfig):
        self.config = config
        self.rng = random.Random(config.seed)
        self.np_rng = np.random.default_rng(config.seed)

    def process_packet(self, payload: TelemetryPayload) -> List[Optional[TelemetryPayload]]:
        """
        Processes a single telemetry packet through the degradation pipeline.
        Returns a list of payloads to emit (empty if dropped, 2 if duplicated, 1 if normal/modified).
        """
        # 1. Packet Loss Check (0% to 40%)
        if self.config.loss_rate > 0.0:
            if self.rng.random() < self.config.loss_rate:
                # Dropped
                return []

        modified = copy.deepcopy(payload)

        # 2. Measurement Noise Injection
        noise_std_map = {
            "none": 0.0,
            "low": 0.02,       # 2% relative standard deviation
            "medium": 0.08,    # 8% relative std
            "high": 0.20,      # 20% relative std
        }
        rel_std = noise_std_map.get(self.config.noise_level.lower(), 0.0)
        if rel_std > 0.0:
            noise_p = float(self.np_rng.normal(0.0, modified.pressure_psi * rel_std))
            noise_q = float(self.np_rng.normal(0.0, modified.flow_rate_gpm * rel_std))
            noise_t = float(self.np_rng.normal(0.0, 2.0 * rel_std))
            noise_v = float(abs(self.np_rng.normal(0.0, 0.5 * rel_std)))

            modified.pressure_psi = max(0.0, round(modified.pressure_psi + noise_p, 2))
            modified.flow_rate_gpm = max(0.0, round(modified.flow_rate_gpm + noise_q, 2))
            modified.temperature_c = round(modified.temperature_c + noise_t, 2)
            modified.vibration_rms = max(0.0, round(modified.vibration_rms + noise_v, 2))

        # 3. Delay Injection (applied as timestamp offset or delivery scheduling)
        if self.config.delay_ms > 0:
            jitter = self.rng.randint(-int(self.config.delay_ms * 0.2), int(self.config.delay_ms * 0.2))
            actual_delay = max(0, self.config.delay_ms + jitter)
            # Timestamp reflects when captured, arrival reflects delay
            modified.metadata_delay_ms = actual_delay if hasattr(modified, "metadata_delay_ms") else actual_delay

        # 4. Corruption Injection
        if self.config.corruption and self.rng.random() < 0.05:
            # Inject extreme physically impossible value to test gateway rejection
            modified.pressure_psi = 9999.0

        # 5. Duplicate Check
        if self.config.duplicates and self.rng.random() < 0.10:
            dup = copy.deepcopy(modified)
            return [modified, dup]

        return [modified]
