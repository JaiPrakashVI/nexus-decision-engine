import React, { useState } from 'react';
import { Flame, Play } from 'lucide-react';
import { TopologyData } from '../types';

interface IncidentSimulatorProps {
  topology: TopologyData | null;
}

export const IncidentSimulator: React.FC<IncidentSimulatorProps> = ({ topology }) => {
  const [selectedNode, setSelectedNode] = useState('pump_01');
  const [disruptionType, setDisruptionType] = useState('NODE_FAILURE');
  const [simReport, setSimReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const resp = await fetch('http://localhost:8000/api/v1/simulations/cascade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: selectedNode,
          disruption_type: disruptionType,
          max_steps: 10,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setSimReport(data);
      }
    } catch (e) {
      console.error("Simulation failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Simulation Controls */}
      <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl space-y-5">
        <div className="flex items-center space-x-2 text-sm font-mono font-bold text-nexus-danger">
          <Flame className="w-4 h-4" />
          <span>CASCADING DISRUPTION SIMULATOR</span>
        </div>

        <p className="text-xs text-slate-400 font-mono">
          Inject controlled physical disruptions into an isolated digital twin sandbox to measure cascading blast radius and downstream dependency failures.
        </p>

        {/* Node Target Selector */}
        <div>
          <label className="block text-xs font-mono text-slate-300 mb-2">Target Asset for Failure:</label>
          <select
            value={selectedNode}
            onChange={(e) => setSelectedNode(e.target.value)}
            className="w-full bg-nexus-900 border border-nexus-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-nexus-accent"
          >
            {topology?.nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.name} ({n.id} - {n.type})
              </option>
            ))}
          </select>
        </div>

        {/* Disruption Type */}
        <div>
          <label className="block text-xs font-mono text-slate-300 mb-2">Disruption Type:</label>
          <select
            value={disruptionType}
            onChange={(e) => setDisruptionType(e.target.value)}
            className="w-full bg-nexus-900 border border-nexus-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-nexus-accent"
          >
            <option value="NODE_FAILURE">Mechanical Failure / Impeller Seizure</option>
            <option value="PIPE_BURST">Catastrophic Pipe Rupture & Pressure Drop</option>
            <option value="POWER_OUTAGE">Substation Bus Trip / Complete Loss of Power</option>
            <option value="VALVE_JAM">Valve Actuator Sticking / Flow Blockage</option>
          </select>
        </div>

        {/* Action Button */}
        <button
          onClick={handleSimulate}
          disabled={loading}
          className="w-full py-2.5 bg-gradient-to-r from-nexus-danger to-orange-600 text-white font-bold font-mono text-xs rounded-lg hover:opacity-90 transition-opacity shadow-lg shadow-rose-500/20 flex items-center justify-center space-x-2"
        >
          <Play className="w-3.5 h-3.5" />
          <span>{loading ? 'SIMULATING CASCADES...' : 'EXECUTE FAILURE SIMULATION'}</span>
        </button>
      </div>

      {/* Simulation Results & Cascading Propagation Timeline */}
      <div className="lg:col-span-2 bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl">
        <h3 className="text-sm font-mono font-bold text-white mb-4">CASCADING FAILURE PROPAGATION TIMELINE</h3>

        {simReport ? (
          <div className="space-y-4 font-mono text-xs">
            {/* KPI Summary */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-nexus-900 rounded-lg border border-nexus-700">
                <div className="text-[10px] text-slate-400">BLAST RADIUS</div>
                <div className="text-xl font-bold text-nexus-danger mt-1">
                  {simReport.cascaded_nodes.length + 1} Assets
                </div>
              </div>

              <div className="p-3 bg-nexus-900 rounded-lg border border-nexus-700">
                <div className="text-[10px] text-slate-400">UNSERVED DEMAND</div>
                <div className="text-xl font-bold text-nexus-warn mt-1">
                  {simReport.estimated_unserved_demand} GPM
                </div>
              </div>

              <div className="p-3 bg-nexus-900 rounded-lg border border-nexus-700">
                <div className="text-[10px] text-slate-400">TIME TO EQUILIBRIUM</div>
                <div className="text-xl font-bold text-cyan-400 mt-1">
                  {simReport.time_to_stabilize_sec}s
                </div>
              </div>
            </div>

            {/* Step-by-step Timeline */}
            <div className="space-y-2 mt-4 max-h-[380px] overflow-y-auto pr-2">
              {simReport.timeline.map((step: any) => (
                <div key={step.step} className="p-3 bg-nexus-900/80 rounded-lg border border-nexus-700/60 flex items-start space-x-3">
                  <div className="px-2 py-0.5 rounded bg-nexus-700 text-nexus-accent font-bold text-[10px]">
                    T+{step.step}
                  </div>
                  <div className="flex-1">
                    <div className="text-white font-bold">{step.description}</div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      System Loss: <span className="text-nexus-danger font-bold">{step.system_loss_percentage}%</span>
                      {step.newly_failed_nodes.length > 0 && (
                        <span> &bull; Failed Nodes: {step.newly_failed_nodes.join(', ')}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-24 text-slate-500 font-mono text-xs">
            Select a cyber-physical asset on the left and run the simulation to observe deterministic failure propagation.
          </div>
        )}
      </div>
    </div>
  );
};
