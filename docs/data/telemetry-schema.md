# Data Specification: Telemetry Schema

The NEXUS telemetry schema defines the exact wire contract for physical measurements streamed from cyber-physical devices to the Secure Gateway.

---

## Telemetry Fields Specification

| Field Name | Type | Unit / Format | Valid Range | Required | Description |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `device_id` | `string` | Alphanumeric string | 3 to 64 chars | Yes | Unique hardware identifier of reporting asset |
| `timestamp` | `string` | ISO 8601 UTC | Within $\pm 5$ min | Yes | Measurement capture timestamp |
| `sequence_number`| `integer`| Non-negative integer | $\ge 0$ | Yes | Monotonically increasing sequence number |
| `trace_id` | `string` | UUID4 string | 36 chars | Yes | Distributed tracing correlation ID |
| `latitude` | `float` | WGS84 degrees | $[-90.0, 90.0]$ | Yes | Physical geographic latitude |
| `longitude` | `float` | WGS84 degrees | $[-180.0, 180.0]$ | Yes | Physical geographic longitude |
| `pressure_psi` | `float` | PSI | $[0.0, 500.0]$ | Yes | Fluid hydraulic line pressure |
| `flow_rate_gpm` | `float` | Gallons/min | $[0.0, 5000.0]$ | Yes | Volumetric flow rate |
| `temperature_c` | `float` | Celsius | $[-40.0, 150.0]$ | Yes | Operating fluid/motor temperature |
| `vibration_rms` | `float` | mm/s | $[0.0, 50.0]$ | No (0.0) | Mechanical vibration amplitude |
| `power_kw` | `float` | Kilowatts | $[0.0, 1000.0]$ | No (0.0) | Electrical power draw |
| `battery_pct` | `float` | Percentage | $[0.0, 100.0]$ | No (100.0)| Edge instrument battery reserve |
| `schema_version`| `string` | Semantic version | `"1.0"`, `"1.1"` | Yes | Contract version identifier |

---

## Example Ingestion Payload

```json
{
  "device_id": "pump_01",
  "timestamp": "2026-09-21T22:15:00Z",
  "sequence_number": 4201,
  "trace_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
  "latitude": 43.541,
  "longitude": -80.248,
  "pressure_psi": 65.2,
  "flow_rate_gpm": 52.4,
  "temperature_c": 21.0,
  "vibration_rms": 0.42,
  "power_kw": 19.5,
  "battery_pct": 98.5,
  "schema_version": "1.0"
}
```
