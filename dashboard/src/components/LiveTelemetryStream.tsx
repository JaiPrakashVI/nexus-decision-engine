import React, { useState } from 'react';
import { TelemetryReadingEvent } from '../types';
import { Terminal, Filter } from 'lucide-react';

interface LiveTelemetryStreamProps {
  events: TelemetryReadingEvent[];
}

export const LiveTelemetryStream: React.FC<LiveTelemetryStreamProps> = ({ events }) => {
  const [filterNode, setFilterNode] = useState('');

  const filtered = filterNode
    ? events.filter(e => e.node_id.toLowerCase().includes(filterNode.toLowerCase()))
    : events;

  return (
    <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-nexus-accent" />
          <span className="text-sm font-mono font-bold text-white">STREAMING TELEMETRY INGESTION TERMINAL</span>
          <span className="text-xs px-2 py-0.5 rounded bg-nexus-700 font-mono text-cyan-300">
            {events.length} Buffered Events
          </span>
        </div>

        {/* Filter Input */}
        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Filter by Asset ID..."
            value={filterNode}
            onChange={(e) => setFilterNode(e.target.value)}
            className="bg-nexus-900 border border-nexus-700 rounded-lg px-3 py-1.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-nexus-accent"
          />
        </div>
      </div>

      {/* Terminal Data Table */}
      <div className="overflow-x-auto rounded-lg border border-nexus-700 bg-nexus-900/90 font-mono text-xs">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-nexus-700 text-slate-400 text-[11px] bg-nexus-850/60">
              <th className="p-3">TIMESTAMP</th>
              <th className="p-3">ASSET ID</th>
              <th className="p-3">STATUS</th>
              <th className="p-3">SOURCE</th>
              <th className="p-3">PRESSURE (PSI)</th>
              <th className="p-3">FLOW (GPM)</th>
              <th className="p-3">TEMP (°C)</th>
              <th className="p-3">VIBRATION (RMS)</th>
              <th className="p-3">CONFIDENCE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-nexus-800">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={9} className="p-8 text-center text-slate-500">
                  No telemetry matching filter. Streaming live...
                </td>
              </tr>
            ) : (
              filtered.map((evt, idx) => (
                <tr key={idx} className="hover:bg-nexus-800/50 transition-colors">
                  <td className="p-3 text-slate-400 text-[10px]">
                    {new Date(evt.timestamp).toISOString()}
                  </td>
                  <td className="p-3 font-bold text-nexus-accent">{evt.node_id}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${
                      evt.state === 'OPERATIONAL' ? 'bg-emerald-950 text-emerald-400' :
                      evt.state === 'DEGRADED' ? 'bg-amber-950 text-amber-400' : 'bg-rose-950 text-rose-400'
                    }`}>
                      {evt.state}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`text-[10px] ${evt.source === 'OBSERVED' ? 'text-nexus-neon' : 'text-cyan-400'}`}>
                      {evt.source}
                    </span>
                  </td>
                  <td className="p-3 text-white">{evt.pressure.toFixed(1)}</td>
                  <td className="p-3 text-white">{evt.flow.toFixed(1)}</td>
                  <td className="p-3 text-slate-300">{evt.temp.toFixed(1)}</td>
                  <td className="p-3 text-slate-300">{evt.vibration.toFixed(2)}</td>
                  <td className="p-3 text-emerald-400 font-bold">{(evt.confidence * 100).toFixed(0)}%</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
