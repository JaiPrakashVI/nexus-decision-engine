import React, { useEffect, useState } from 'react';
import { StateReconstructionData, DarkProcessMetrics } from '../types';
import { EyeOff } from 'lucide-react';

interface DataQualityRadarProps {
  reconstruction: StateReconstructionData | null;
}

export const DataQualityRadar: React.FC<DataQualityRadarProps> = ({ reconstruction }) => {
  const [darkMetrics, setDarkMetrics] = useState<DarkProcessMetrics | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/dark-processes')
      .then(res => res.json())
      .then(data => setDarkMetrics(data))
      .catch(err => console.error(err));
  }, []);

  const completeness = reconstruction?.completeness_score ?? 1.0;
  const observability = reconstruction?.observability_score ?? 1.0;

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="text-xs text-slate-400 font-mono mb-1">STREAM COMPLETENESS</div>
          <div className="text-2xl font-bold font-mono text-white">{(completeness * 100).toFixed(1)}%</div>
          <div className="text-[11px] text-slate-400 mt-1">Observed Packet Ratio</div>
        </div>

        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="text-xs text-slate-400 font-mono mb-1">SYSTEM OBSERVABILITY</div>
          <div className="text-2xl font-bold font-mono text-nexus-neon">{(observability * 100).toFixed(1)}%</div>
          <div className="text-[11px] text-slate-400 mt-1">Effective Twin Visibility</div>
        </div>

        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="text-xs text-slate-400 font-mono mb-1">DARK PROCESS INDEX</div>
          <div className="text-2xl font-bold font-mono text-nexus-warn">
            {((darkMetrics?.dark_process_index ?? 0.0) * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Unobserved Transitions</div>
        </div>

        <div className="bg-nexus-850 p-4 rounded-xl border border-nexus-700 shadow-md">
          <div className="text-xs text-slate-400 font-mono mb-1">MISSING TRANSITIONS DETECTED</div>
          <div className="text-2xl font-bold font-mono text-nexus-danger">
            {darkMetrics?.detected_missing_transitions ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Skipped Lifecycle Steps</div>
        </div>
      </div>

      {/* Dark Processes & Missing Transition Feed */}
      <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 text-sm font-mono font-bold text-white">
          <EyeOff className="w-4 h-4 text-nexus-warn" />
          <span>DETECTED DARK PROCESSES & MISSING EVENT LOGS</span>
        </div>

        <p className="text-xs text-slate-400 font-mono">
          Identifies unlogged physical transitions where intermediate events were omitted due to packet loss, sensor failure, or unlogged external interventions.
        </p>

        <div className="overflow-x-auto rounded-lg border border-nexus-700 bg-nexus-900 font-mono text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-nexus-700 text-slate-400 text-[11px] bg-nexus-850/60">
                <th className="p-3">TIMESTAMP</th>
                <th className="p-3">ASSET ID</th>
                <th className="p-3">OBSERVED TRANSITION</th>
                <th className="p-3">INFERRED MISSING EVENT</th>
                <th className="p-3">CONFIDENCE</th>
                <th className="p-3">DIAGNOSTIC HYPOTHESIS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nexus-800">
              {(!darkMetrics?.recent_missing_events || darkMetrics.recent_missing_events.length === 0) ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">
                    No dark processes detected. System transition sequence is continuous.
                  </td>
                </tr>
              ) : (
                darkMetrics.recent_missing_events.map((item, idx) => (
                  <tr key={idx} className="hover:bg-nexus-800/40">
                    <td className="p-3 text-slate-400 text-[10px]">{new Date(item.timestamp).toLocaleTimeString()}</td>
                    <td className="p-3 font-bold text-white">{item.device_id}</td>
                    <td className="p-3 text-nexus-danger font-mono">{item.observed}</td>
                    <td className="p-3 text-nexus-accent font-mono">{item.expected}</td>
                    <td className="p-3 text-nexus-neon">{(item.confidence * 100).toFixed(0)}%</td>
                    <td className="p-3 text-slate-300">{item.hypothesis}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
