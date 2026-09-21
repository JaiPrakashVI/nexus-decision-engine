import React, { useState } from 'react';
import { Activity, ShieldCheck, Database, Zap, RefreshCw, Sliders } from 'lucide-react';
import { TopologyData, StateReconstructionData, TelemetryReadingEvent } from '../types';

interface OverviewTabProps {
  topology: TopologyData | null;
  reconstruction: StateReconstructionData | null;
  recentEvents: TelemetryReadingEvent[];
  onConfigChange: (loss: number, delay: number, noise: string) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  topology,
  reconstruction,
  recentEvents,
  onConfigChange,
}) => {
  const [lossRate, setLossRate] = useState(0.0);
  const [delayMs, setDelayMs] = useState(0);
  const [noiseLevel, setNoiseLevel] = useState('none');

  const handleApplyDegradation = () => {
    onConfigChange(lossRate, delayMs, noiseLevel);
  };

  const totalNodes = topology?.node_count || 25;
  const observedCount = reconstruction?.observed_nodes || 25;
  const inferredCount = reconstruction?.inferred_nodes || 0;
  const completeness = reconstruction?.completeness_score ?? 1.0;
  const observability = reconstruction?.observability_score ?? 1.0;

  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>TOTAL ASSETS</span>
            <Database className="w-4 h-4 text-nexus-accent" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{totalNodes}</div>
          <div className="text-[11px] text-slate-400 mt-1">Smart Grid Nodes</div>
        </div>

        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>DIRECT OBSERVED</span>
            <Activity className="w-4 h-4 text-nexus-neon" />
          </div>
          <div className="text-2xl font-bold font-mono text-nexus-neon">{observedCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">Direct Telemetry Fresh</div>
        </div>

        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>INFERRED (TWIN)</span>
            <RefreshCw className="w-4 h-4 text-nexus-accent" />
          </div>
          <div className="text-2xl font-bold font-mono text-nexus-accent">{inferredCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">Reconstructed via Physics</div>
        </div>

        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>COMPLETENESS</span>
            <Zap className="w-4 h-4 text-nexus-warn" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{(completeness * 100).toFixed(1)}%</div>
          <div className="w-full bg-nexus-900 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full ${completeness < 0.7 ? 'bg-nexus-warn' : 'bg-nexus-neon'}`}
              style={{ width: `${completeness * 100}%` }}
            />
          </div>
        </div>

        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>OBSERVABILITY</span>
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-400">{(observability * 100).toFixed(1)}%</div>
          <div className="text-[11px] text-slate-400 mt-1">Observed + Weight(Inferred)</div>
        </div>
      </div>

      {/* Fault Injection Controller Panel */}
      <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700">
        <div className="flex items-center space-x-2 text-sm font-mono text-nexus-accent mb-4">
          <Sliders className="w-4 h-4" />
          <span className="font-bold">IMPERFECT TELEMETRY & FAULT DEGRADATION CONTROLLER</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
          {/* Packet Loss Slider (0% to 40%) */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-slate-300">Packet Loss Rate:</span>
              <span className="font-bold text-nexus-danger">{(lossRate * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="0.40"
              step="0.05"
              value={lossRate}
              onChange={(e) => setLossRate(parseFloat(e.target.value))}
              className="w-full accent-nexus-danger cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
              <span>0% (Clean)</span>
              <span>20%</span>
              <span>40% (Extreme Stress)</span>
            </div>
          </div>

          {/* Latency Delay Slider (0 to 1000ms) */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-slate-300">Transmission Latency:</span>
              <span className="font-bold text-nexus-warn">{delayMs} ms</span>
            </div>
            <input
              type="range"
              min="0"
              max="1000"
              step="50"
              value={delayMs}
              onChange={(e) => setDelayMs(parseInt(e.target.value))}
              className="w-full accent-nexus-warn cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
              <span>0ms</span>
              <span>500ms</span>
              <span>1000ms</span>
            </div>
          </div>

          {/* Noise Selector */}
          <div>
            <label className="block text-xs font-mono text-slate-300 mb-2">Sensor Noise Level:</label>
            <select
              value={noiseLevel}
              onChange={(e) => setNoiseLevel(e.target.value)}
              className="w-full bg-nexus-900 border border-nexus-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-nexus-accent"
            >
              <option value="none">None (Ideal Sensors)</option>
              <option value="low">Low (σ = 2%)</option>
              <option value="medium">Medium (σ = 8%)</option>
              <option value="high">High (σ = 20% Extreme Noise)</option>
            </select>
          </div>

          {/* Apply Button */}
          <button
            onClick={handleApplyDegradation}
            className="w-full py-2 bg-gradient-to-r from-nexus-accent to-blue-600 text-black font-bold font-mono text-xs rounded-lg hover:opacity-90 transition-opacity shadow-lg shadow-cyan-500/20"
          >
            APPLY DEGRADATION
          </button>
        </div>
      </div>

      {/* Real-Time Telemetry Feed Preview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Node Health Breakdown */}
        <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700">
          <h3 className="text-sm font-mono font-bold text-white mb-4">CYBER-PHYSICAL STATE DISTRIBUTION</h3>
          <div className="space-y-3">
            {topology?.nodes.slice(0, 7).map((n) => (
              <div key={n.id} className="flex items-center justify-between p-2.5 bg-nexus-900/60 rounded-lg border border-nexus-700/50 text-xs font-mono">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    n.state === 'OPERATIONAL' ? 'bg-nexus-neon' :
                    n.state === 'DEGRADED' ? 'bg-nexus-warn' : 'bg-nexus-danger'
                  }`} />
                  <span className="font-bold text-white">{n.name}</span>
                  <span className="text-[10px] text-slate-400">({n.type})</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-slate-300">{n.pressure.toFixed(1)} PSI</span>
                  <span className="text-slate-300">{n.flow.toFixed(1)} GPM</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] ${
                    n.source === 'OBSERVED' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                    'bg-cyan-950 text-cyan-400 border border-cyan-800'
                  }`}>
                    {n.source} ({Math.round(n.confidence * 100)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Event Stream */}
        <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700">
          <h3 className="text-sm font-mono font-bold text-white mb-4">LIVE EVENT FEED</h3>
          <div className="space-y-2 max-h-[340px] overflow-y-auto pr-2">
            {recentEvents.length === 0 ? (
              <div className="text-center py-12 text-slate-500 font-mono text-xs">Waiting for telemetry stream...</div>
            ) : (
              recentEvents.map((evt, idx) => (
                <div key={idx} className="p-2.5 bg-nexus-900 rounded border border-nexus-700 text-xs font-mono flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-nexus-accent">[{evt.node_id}]</span>
                    <span className="text-slate-200">{evt.pressure.toFixed(1)} PSI</span>
                    <span className="text-slate-400">|</span>
                    <span className="text-slate-200">{evt.flow.toFixed(1)} GPM</span>
                  </div>
                  <div className="flex items-center space-x-2 text-[10px]">
                    <span className={evt.source === 'OBSERVED' ? 'text-nexus-neon' : 'text-nexus-accent'}>
                      {evt.source}
                    </span>
                    <span className="text-slate-500">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
