import React, { useState } from 'react';
import { TwinNode, TopologyData } from '../types';
import { Info, Gauge, Zap, Battery, Activity } from 'lucide-react';

interface DigitalTwinGraphProps {
  topology: TopologyData | null;
}

export const DigitalTwinGraph: React.FC<DigitalTwinGraphProps> = ({ topology }) => {
  const [selectedNode, setSelectedNode] = useState<TwinNode | null>(null);

  if (!topology || topology.nodes.length === 0) {
    return <div className="p-8 text-center text-slate-500 font-mono">Loading digital twin topology...</div>;
  }

  // Map nodes to 2D SVG canvas coordinates based on their lat/lon or topology layer
  const nodes = topology.nodes;
  const minLat = Math.min(...nodes.map(n => n.lat));
  const maxLat = Math.max(...nodes.map(n => n.lat));
  const minLon = Math.min(...nodes.map(n => n.lon));
  const maxLon = Math.max(...nodes.map(n => n.lon));

  const mapX = (lon: number) => {
    if (maxLon === minLon) return 400;
    return 80 + ((lon - minLon) / (maxLon - minLon)) * 720;
  };

  const mapY = (lat: number) => {
    if (maxLat === minLat) return 250;
    return 440 - ((lat - minLat) / (maxLat - minLat)) * 360;
  };

  const getNodeColor = (state: string) => {
    switch (state) {
      case 'OPERATIONAL': return '#00ff88';
      case 'DEGRADED': return '#ffaa00';
      case 'CRITICAL':
      case 'FAILED': return '#ff3366';
      default: return '#64748b';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Graph Canvas */}
      <div className="lg:col-span-3 bg-nexus-850 p-4 rounded-xl border border-nexus-700 relative overflow-hidden shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-mono font-bold text-white">TOPOLOGICAL DEPENDENCY GRAPH</span>
            <span className="text-xs px-2 py-0.5 rounded bg-nexus-700 font-mono text-cyan-300">
              {topology.node_count} Nodes | {topology.edge_count} Directed Edges
            </span>
          </div>

          <div className="flex items-center space-x-4 text-[11px] font-mono text-slate-400">
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-nexus-neon inline-block" />
              <span>Operational</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-nexus-warn inline-block" />
              <span>Degraded</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-nexus-danger inline-block" />
              <span>Failed</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full border border-dashed border-nexus-accent inline-block" />
              <span>Inferred</span>
            </div>
          </div>
        </div>

        {/* SVG Render Area */}
        <div className="w-full h-[520px] bg-nexus-900/90 rounded-lg border border-nexus-700/60 flex items-center justify-center">
          <svg viewBox="0 0 880 500" className="w-full h-full select-none">
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="14"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#1b2a4e" />
              </marker>
            </defs>

            {/* Render Edges */}
            {topology.edges.map((edge, idx) => {
              const u = nodes.find(n => n.id === edge.source);
              const v = nodes.find(n => n.id === edge.target);
              if (!u || !v) return null;

              const x1 = mapX(u.lon);
              const y1 = mapY(u.lat);
              const x2 = mapX(v.lon);
              const y2 = mapY(v.lat);

              return (
                <line
                  key={idx}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="#1b2a4e"
                  strokeWidth="2"
                  strokeDasharray={edge.relation === 'powers' ? '3,3' : 'none'}
                  markerEnd="url(#arrowhead)"
                />
              );
            })}

            {/* Render Nodes */}
            {nodes.map((node) => {
              const cx = mapX(node.lon);
              const cy = mapY(node.lat);
              const isSelected = selectedNode?.id === node.id;
              const color = getNodeColor(node.state);
              const isInferred = node.source === 'INFERRED';

              return (
                <g
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className="cursor-pointer transition-transform duration-150 hover:scale-110"
                >
                  {/* Halo when selected */}
                  {isSelected && (
                    <circle cx={cx} cy={cy} r="20" fill="none" stroke="#00f0ff" strokeWidth="2" opacity="0.6" />
                  )}

                  {/* Node Circle */}
                  <circle
                    cx={cx}
                    cy={cy}
                    r="12"
                    fill="#0c1222"
                    stroke={color}
                    strokeWidth={isInferred ? "2" : "3"}
                    strokeDasharray={isInferred ? "3,2" : "none"}
                  />

                  {/* Center Dot */}
                  <circle cx={cx} cy={cy} r="4" fill={color} />

                  {/* Node Label */}
                  <text
                    x={cx}
                    y={cy + 22}
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize="9"
                    fontFamily="monospace"
                  >
                    {node.id}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Node Inspector Drawer */}
      <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl">
        <div className="flex items-center space-x-2 text-sm font-mono font-bold text-white mb-4">
          <Info className="w-4 h-4 text-nexus-accent" />
          <span>ASSET TELEMETRY & TWIN STATE</span>
        </div>

        {selectedNode ? (
          <div className="space-y-4">
            <div className="p-3 bg-nexus-900 rounded-lg border border-nexus-700">
              <div className="text-xs text-slate-400 font-mono">ASSET ID / NAME</div>
              <div className="text-sm font-bold text-white font-mono mt-0.5">{selectedNode.name}</div>
              <div className="text-[11px] text-cyan-400 font-mono">{selectedNode.id} &bull; {selectedNode.type}</div>
            </div>

            {/* Operational State & Source */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 bg-nexus-900 rounded-lg border border-nexus-700">
                <div className="text-[10px] text-slate-400 font-mono">STATE</div>
                <div className={`text-xs font-bold font-mono mt-1 ${
                  selectedNode.state === 'OPERATIONAL' ? 'text-nexus-neon' :
                  selectedNode.state === 'DEGRADED' ? 'text-nexus-warn' : 'text-nexus-danger'
                }`}>
                  {selectedNode.state}
                </div>
              </div>

              <div className="p-2.5 bg-nexus-900 rounded-lg border border-nexus-700">
                <div className="text-[10px] text-slate-400 font-mono">TELEMETRY SOURCE</div>
                <div className="text-xs font-bold font-mono mt-1 text-nexus-accent">
                  {selectedNode.source}
                </div>
              </div>
            </div>

            {/* Physical Telemetry Gauges */}
            <div className="space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between p-2 bg-nexus-900 rounded">
                <span className="text-slate-400 flex items-center space-x-1.5">
                  <Gauge className="w-3.5 h-3.5 text-blue-400" />
                  <span>Pressure:</span>
                </span>
                <span className="text-white font-bold">{selectedNode.pressure.toFixed(1)} PSI</span>
              </div>

              <div className="flex items-center justify-between p-2 bg-nexus-900 rounded">
                <span className="text-slate-400 flex items-center space-x-1.5">
                  <Activity className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Flow Rate:</span>
                </span>
                <span className="text-white font-bold">{selectedNode.flow.toFixed(1)} GPM</span>
              </div>

              <div className="flex items-center justify-between p-2 bg-nexus-900 rounded">
                <span className="text-slate-400 flex items-center space-x-1.5">
                  <Zap className="w-3.5 h-3.5 text-yellow-400" />
                  <span>Power Draw:</span>
                </span>
                <span className="text-white font-bold">{selectedNode.power.toFixed(1)} kW</span>
              </div>

              <div className="flex items-center justify-between p-2 bg-nexus-900 rounded">
                <span className="text-slate-400 flex items-center space-x-1.5">
                  <Battery className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Battery:</span>
                </span>
                <span className="text-white font-bold">{selectedNode.battery.toFixed(1)}%</span>
              </div>
            </div>

            {/* Bayesian Confidence */}
            <div className="p-3 bg-nexus-900 rounded-lg border border-nexus-700">
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-slate-400">Reconstruction Confidence:</span>
                <span className="font-bold text-nexus-accent">{(selectedNode.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-nexus-800 h-2 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-nexus-accent to-emerald-400"
                  style={{ width: `${selectedNode.confidence * 100}%` }}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-20 text-slate-500 font-mono text-xs">
            Click any node on the graph to inspect physical telemetry, upstream dependencies, and reconstructed states.
          </div>
        )}
      </div>
    </div>
  );
};
