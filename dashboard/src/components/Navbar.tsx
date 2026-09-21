import React from 'react';
import { Activity, ShieldCheck, Cpu, Wifi, AlertTriangle, GitPullRequest, BarChart3 } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isConnected: boolean;
  completeness: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, isConnected, completeness }) => {
  const tabs = [
    { id: 'overview', label: 'Command Overview', icon: Activity },
    { id: 'twin', label: 'Digital Twin Graph', icon: Cpu },
    { id: 'telemetry', label: 'Live Telemetry', icon: Wifi },
    { id: 'simulator', label: 'Incident Sandbox', icon: AlertTriangle },
    { id: 'decision', label: 'Decision Engine & AI', icon: ShieldCheck },
    { id: 'quality', label: 'Data Quality & Dark Processes', icon: GitPullRequest },
    { id: 'experiments', label: 'Research Experiments', icon: BarChart3 },
  ];

  return (
    <header className="border-b border-nexus-700 bg-nexus-850/80 backdrop-blur-md sticky top-0 z-50 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-nexus-accent to-blue-600 flex items-center justify-center font-mono font-bold text-black text-xl shadow-lg shadow-cyan-500/20">
            N
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-wider text-white">NEXUS</span>
              <span className="text-xs px-2 py-0.5 rounded bg-nexus-700 text-nexus-accent font-mono">v1.0-RESEARCH</span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">Real-Time Adaptive Digital Twin & Decision Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 bg-nexus-900/90 p-1 rounded-lg border border-nexus-700">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-nexus-700 text-nexus-accent shadow-sm border border-nexus-accent/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-nexus-800'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-nexus-accent' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Live Status Indicators */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-nexus-900 px-3 py-1.5 rounded border border-nexus-700 text-xs">
            <span className="text-slate-400">Stream Completeness:</span>
            <span className={`font-mono font-bold ${completeness < 0.7 ? 'text-nexus-warn' : 'text-nexus-neon'}`}>
              {(completeness * 100).toFixed(1)}%
            </span>
          </div>

          <div className="flex items-center space-x-2 bg-nexus-900 px-3 py-1.5 rounded border border-nexus-700 text-xs">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-nexus-neon animate-pulse' : 'bg-nexus-danger'}`} />
            <span className="font-mono text-slate-300">{isConnected ? 'WS CONNECTED' : 'OFFLINE'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
