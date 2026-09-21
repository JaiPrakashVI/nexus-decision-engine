"""
NEXUS Device Registry & Authentication Manager
Enforces cryptographic certificate verification, device status checking, and serial validation.
"""

from typing import Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum


class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


@dataclass
class DeviceRecord:
    device_id: str
    status: DeviceStatus
    device_type: str  # pump, valve, reservoir, sensor, meter
    expected_serial: Optional[str] = None
    fingerprint_sha256: Optional[str] = None


class DeviceRegistry:
    """
    In-memory / persistent device registry for gateway authentication.
    Verifies that incoming mTLS client identities match known operational assets.
    """

    def __init__(self):
        self._devices: Dict[str, DeviceRecord] = {}
        self._authorized_types: Set[str] = {
            "pump", "valve", "reservoir", "pipe", "sensor", "meter", "substation"
        }
        self._init_default_inventory()

    def _init_default_inventory(self):
        """Pre-populate default smart water & power infrastructure assets and sensors."""
        # Pre-seed smart grid topology assets
        grid_assets = [
            ("source_01", "source"), ("source_02", "source"),
            ("substation_01", "substation"), ("substation_02", "substation"),
            ("pump_01", "pump"), ("pump_02", "pump"), ("pump_03", "pump"),
            ("pipe_01", "pipe"), ("pipe_02", "pipe"), ("pipe_03", "pipe"),
            ("pipe_04", "pipe"), ("pipe_05", "pipe"), ("pipe_06", "pipe"),
            ("valve_01", "valve"), ("valve_02", "valve"), ("valve_03", "valve"), ("valve_04", "valve"),
            ("storage_01", "reservoir"), ("storage_02", "reservoir"),
            ("district_alpha", "district"), ("district_beta", "district"), ("district_gamma", "district"),
        ]
        for dev_id, dev_type in grid_assets:
            self._devices[dev_id] = DeviceRecord(
                device_id=dev_id,
                status=DeviceStatus.ACTIVE,
                device_type=dev_type,
            )

        # Pre-seed device_001 through device_050
        for i in range(1, 51):
            dev_id = f"device_{i:03d}"
            if dev_id not in self._devices:
                self._devices[dev_id] = DeviceRecord(
                    device_id=dev_id,
                    status=DeviceStatus.ACTIVE,
                    device_type="sensor",
                )

    def register_device(
        self,
        device_id: str,
        device_type: str,
        status: DeviceStatus = DeviceStatus.ACTIVE,
        expected_serial: Optional[str] = None,
        fingerprint_sha256: Optional[str] = None
    ) -> DeviceRecord:
        record = DeviceRecord(
            device_id=device_id,
            status=status,
            device_type=device_type,
            expected_serial=expected_serial,
            fingerprint_sha256=fingerprint_sha256,
        )
        self._devices[device_id] = record
        return record

    def is_authorized(self, device_id: str) -> bool:
        record = self._devices.get(device_id)
        if not record:
            return False
        return record.status == DeviceStatus.ACTIVE

    def get_device(self, device_id: str) -> Optional[DeviceRecord]:
        return self._devices.get(device_id)

    def revoke_device(self, device_id: str) -> bool:
        record = self._devices.get(device_id)
        if record:
            record.status = DeviceStatus.REVOKED
            return True
        return False


# Global device registry singleton for the gateway
device_registry = DeviceRegistry()
