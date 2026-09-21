"""
NEXUS Digital Twin API & Command Center Service
Exposes REST and WebSocket endpoints for topology, state reconstruction, simulation, AI decisions, and telemetry.
"""

from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from configs.settings import settings
from digital_twin.graph.topology import topology
from digital_twin.reconstruction.estimator import reconstructor
from digital_twin.synchronization.sync_manager import twin_sync_manager
from anomaly_detection.missing_events.detector import dark_process_detector
from anomaly_detection.diagnostics.evaluator import evaluate_detector_performance
from simulation.cascading_failures.engine import simulation_engine
from agents.decision_support.engine import deterministic_engine
from agents.evaluation.multi_agent_workflow import multi_agent_orchestrator
from simulator.device_simulator import fleet_simulator
from simulator.fault_injection import FaultInjectionConfig
from database.connection import init_db

logger = logging.getLogger("nexus.twin.api")


# Connection Manager for real-time WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


# Register twin listener to forward telemetry updates into WebSockets
def on_twin_update(node_id: str, data: dict):
    # Asynchronously dispatch to active WebSockets
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast({"type": "TWIN_UPDATE", "data": data}))
    except RuntimeError:
        pass


twin_sync_manager.register_listener(on_twin_update)


# Background simulator runner task
_sim_task: Optional[asyncio.Task] = None


async def _background_simulator_loop():
    logger.info("Starting in-process background telemetry simulator loop...")
    while True:
        try:
            readings = fleet_simulator.generate_tick()
            for r in readings:
                # Apply reading directly to twin
                await twin_sync_manager.process_incoming_telemetry(r)

            # Broadcast batch tick summary
            await ws_manager.broadcast({
                "type": "SIM_TICK",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "count": len(readings),
                "completeness": round(len(readings) / max(1, len(fleet_simulator.devices)), 3),
            })
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Simulator loop error: {e}")
            await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NEXUS Digital Twin API Service...")
    await init_db()
    global _sim_task
    _sim_task = asyncio.create_task(_background_simulator_loop())
    yield
    logger.info("Shutting down NEXUS Digital Twin API Service...")
    if _sim_task:
        _sim_task.cancel()


app = FastAPI(
    title="NEXUS Digital Twin & Decision Service",
    description="Cyber-physical digital twin engine with state reconstruction and agentic decision support.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Schemas
class DisruptionRequest(BaseModel):
    node_id: str
    disruption_type: str = "NODE_FAILURE"
    max_steps: int = 10


class InterventionRequest(BaseModel):
    incident_id: str
    root_cause_node: str
    severity: str = "HIGH"
    use_agentic_ai: bool = True


class SimulatorConfigRequest(BaseModel):
    loss_rate: float = 0.0
    delay_ms: int = 0
    noise_level: str = "none"
    out_of_order: bool = False
    duplicates: bool = False


# Endpoints
@app.get("/api/v1/topology", summary="Get complete digital twin topology")
async def get_topology():
    return topology.to_dict()


@app.get("/api/v1/state/reconstruction", summary="Evaluate state reconstruction and uncertainty")
async def get_state_reconstruction():
    return reconstructor.update_all_nodes()


@app.get("/api/v1/dark-processes", summary="Get detected dark processes and missing transitions")
async def get_dark_processes():
    return dark_process_detector.get_metrics()


@app.get("/api/v1/anomalies/benchmark", summary="Benchmark statistical vs ML anomaly detectors")
async def benchmark_detectors(samples: int = 500):
    return evaluate_detector_performance(num_samples=samples)


@app.post("/api/v1/simulations/cascade", summary="Run cascading failure simulation")
async def run_cascade_simulation(req: DisruptionRequest):
    try:
        report = simulation_engine.simulate_failure(
            trigger_node_id=req.node_id,
            disruption_type=req.disruption_type,
            max_steps=req.max_steps,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/api/v1/interventions/evaluate", summary="Synthesize and evaluate intervention plan")
async def evaluate_intervention(req: InterventionRequest):
    # Run deterministic decision plan
    det_plan = deterministic_engine.evaluate_incident(
        incident_id=req.incident_id,
        root_cause_node=req.root_cause_node,
        severity=req.severity,
    )

    result = {
        "incident_id": req.incident_id,
        "root_cause_node": req.root_cause_node,
        "severity": req.severity,
        "deterministic_plan": det_plan,
        "agentic_ai": None,
    }

    if req.use_agentic_ai:
        agent_res = await multi_agent_orchestrator.execute_workflow(
            incident_id=req.incident_id,
            root_cause_node=req.root_cause_node,
            severity=req.severity,
        )
        result["agentic_ai"] = agent_res

    return result


@app.post("/api/v1/simulator/control", summary="Configure live sensor degradation parameters")
async def configure_simulator(req: SimulatorConfigRequest):
    cfg = FaultInjectionConfig(
        loss_rate=req.loss_rate,
        delay_ms=req.delay_ms,
        noise_level=req.noise_level,
        out_of_order=req.out_of_order,
        duplicates=req.duplicates,
    )
    fleet_simulator.fault_injector.set_config(cfg)
    return {
        "status": "updated",
        "current_config": {
            "loss_rate": req.loss_rate,
            "delay_ms": req.delay_ms,
            "noise_level": req.noise_level,
            "out_of_order": req.out_of_order,
            "duplicates": req.duplicates,
        }
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Initial greeting with graph state
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "topology": topology.to_dict(),
            "reconstruction": reconstructor.update_all_nodes(),
        })
        while True:
            # Keep-alive loop listening for client actions
            data = await websocket.receive_text()
            # Echo or process client ping
            await websocket.send_json({"type": "PONG", "timestamp": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("digital_twin.api:app", host="0.0.0.0", port=settings.twin_api_port, reload=False)
