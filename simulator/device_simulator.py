"""
NEXUS Cyber-Physical Sensor Fleet Simulator
Simulates fleets of smart municipal assets producing realistic time-series telemetry with diurnal curves.
"""

from typing import List, Dict, Optional, AsyncGenerator
import time
import math
import uuid
from datetime import datetime, timezone
import asyncio
import httpx
import logging

from gateway.schemas.telemetry import TelemetryPayload
from simulator.fault_injection import FaultInjector, FaultInjectionConfig
from digital_twin.graph.topology import topology

logger = logging.getLogger("nexus.simulator")


class SimulatedDevice:
    def __init__(self, device_id: str, device_type: str, lat: float, lon: float, seed: int = 42):
        self.device_id = device_id
        self.device_type = device_type
        self.lat = lat
        self.lon = lon
        self.seq_no = 0
        self.battery = 100.0
        self.seed = seed

        # Baseline physical setpoints
        self.base_pressure = 65.0 if device_type != "reservoir" else 45.0
        self.base_flow = 55.0 if device_type not in {"valve", "reservoir"} else 40.0
        self.base_temp = 21.0
        self.base_vibration = 0.4 if device_type == "pump" else 0.1

    def generate_reading(self, timestamp: Optional[datetime] = None) -> TelemetryPayload:
        now = timestamp or datetime.now(timezone.utc)
        self.seq_no += 1
        self.battery = max(0.0, self.battery - 0.0005)  # slow discharge

        # Diurnal diurnal demand wave (24h period)
        sec_of_day = (now.hour * 3600) + (now.minute * 60) + now.second
        diurnal_factor = 1.0 + 0.15 * math.sin(2 * math.pi * sec_of_day / 86400)

        # Micro-fluctuations
        p = round(self.base_pressure * diurnal_factor + math.sin(self.seq_no * 0.1) * 2.0, 2)
        q = round(self.base_flow * diurnal_factor + math.cos(self.seq_no * 0.1) * 3.0, 2)
        t = round(self.base_temp + math.sin(self.seq_no * 0.05) * 1.5, 2)
        v = round(max(0.0, self.base_vibration + math.sin(self.seq_no * 0.2) * 0.1), 2)
        kw = round(0.35 * q + 2.0, 2) if self.device_type == "pump" else 0.5

        return TelemetryPayload(
            device_id=self.device_id,
            timestamp=now,
            sequence_number=self.seq_no,
            trace_id=str(uuid.uuid4()),
            latitude=self.lat,
            longitude=self.lon,
            pressure_psi=p,
            flow_rate_gpm=q,
            temperature_c=t,
            vibration_rms=v,
            power_kw=kw,
            battery_pct=round(self.battery, 1),
            schema_version="1.0"
        )


class SensorFleetSimulator:
    def __init__(
        self,
        num_devices: int = 50,
        fault_config: Optional[FaultInjectionConfig] = None
    ):
        self.num_devices = num_devices
        self.fault_injector = FaultInjector(fault_config or FaultInjectionConfig())
        self.devices: List[SimulatedDevice] = []
        self._init_fleet()

    def _init_fleet(self):
        self.devices.clear()
        nodes = topology.get_all_nodes()
        i = 0
        for node_id, node in nodes.items():
            self.devices.append(
                SimulatedDevice(
                    device_id=node_id,
                    device_type=node.node_type,
                    lat=node.latitude,
                    lon=node.longitude,
                    seed=42 + i,
                )
            )
            i += 1
            if len(self.devices) >= self.num_devices:
                break

        # If more devices requested than graph nodes, generate synthetic expansion
        while len(self.devices) < self.num_devices:
            dev_id = f"sensor_{len(self.devices) + 1:03d}"
            self.devices.append(
                SimulatedDevice(
                    device_id=dev_id,
                    device_type="sensor",
                    lat=43.54 + (len(self.devices) * 0.001),
                    lon=-80.25 + (len(self.devices) * 0.001),
                    seed=42 + len(self.devices),
                )
            )

    def generate_tick(self, timestamp: Optional[datetime] = None) -> List[TelemetryPayload]:
        """
        Generates one tick of telemetry across the fleet, processed through fault injection.
        """
        now = timestamp or datetime.now(timezone.utc)
        emitted: List[TelemetryPayload] = []

        for dev in self.devices:
            raw_reading = dev.generate_reading(now)
            packets = self.fault_injector.process_packet(raw_reading)
            for p in packets:
                if p is not None:
                    emitted.append(p)

        if self.fault_injector.config.out_of_order and len(emitted) > 2:
            # Shuffle adjacent packets to test out-of-order handling
            idx = random.randint(0, len(emitted) - 2)
            emitted[idx], emitted[idx + 1] = emitted[idx + 1], emitted[idx]

        return emitted

    async def stream_to_gateway(
        self,
        gateway_url: str = "http://localhost:8443/api/v1/telemetry",
        frequency_hz: float = 1.0,
        max_ticks: Optional[int] = None
    ):
        """
        Continuously streams telemetry HTTP requests to the Secure Gateway.
        """
        interval = 1.0 / frequency_hz
        tick_count = 0
        logger.info(f"Streaming telemetry from {len(self.devices)} devices to {gateway_url} at {frequency_hz} Hz...")

        async with httpx.AsyncClient(timeout=10.0) as client:
            while max_ticks is None or tick_count < max_ticks:
                t0 = time.monotonic()
                readings = self.generate_tick()
                tasks = [
                    client.post(gateway_url, json=r.model_dump(mode="json"))
                    for r in readings
                ]
                # Send concurrently
                await asyncio.gather(*tasks, return_exceptions=True)
                tick_count += 1

                elapsed = time.monotonic() - t0
                sleep_time = max(0.0, interval - elapsed)
                await asyncio.sleep(sleep_time)


fleet_simulator = SensorFleetSimulator(num_devices=50)
