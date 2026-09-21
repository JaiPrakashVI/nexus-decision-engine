import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewTab } from './components/OverviewTab';
import { DigitalTwinGraph } from './components/DigitalTwinGraph';
import { LiveTelemetryStream } from './components/LiveTelemetryStream';
import { IncidentSimulator } from './components/IncidentSimulator';
import { DecisionStudio } from './components/DecisionStudio';
import { DataQualityRadar } from './components/DataQualityRadar';
import { ExperimentRunner } from './components/ExperimentRunner';
import { TopologyData, StateReconstructionData, TelemetryReadingEvent } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isConnected, setIsConnected] = useState(false);
  const [topology, setTopology] = useState<TopologyData | null>(null);
  const [reconstruction, setReconstruction] = useState<StateReconstructionData | null>(null);
  const [recentEvents, setRecentEvents] = useState<TelemetryReadingEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch initial REST data
  const fetchData = async () => {
    try {
      const topResp = await fetch('http://localhost:8000/api/v1/topology');
      if (topResp.ok) setTopology(await topResp.json());

      const recResp = await fetch('http://localhost:8000/api/v1/state/reconstruction');
      if (recResp.ok) setReconstruction(await recResp.json());
    } catch (e) {
      console.warn("Could not reach backend API:", e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, []);

  // Setup WebSocket connection
  useEffect(() => {
    let reconnectTimeout: any;

    const connectWS = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'TWIN_UPDATE') {
              setRecentEvents((prev) => [msg.data, ...prev.slice(0, 99)]);
            } else if (msg.type === 'INITIAL_STATE') {
              if (msg.topology) setTopology(msg.topology);
              if (msg.reconstruction) setReconstruction(msg.reconstruction);
            }
          } catch (err) {
            console.error(err);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connectWS, 3000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connectWS, 3000);
      }
    };

    connectWS();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleConfigChange = async (loss: number, delay: number, noise: string) => {
    try {
      await fetch('http://localhost:8000/api/v1/simulator/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          loss_rate: loss,
          delay_ms: delay,
          noise_level: noise,
        }),
      });
    } catch (e) {
      console.error(e);
    }
  };

  const completeness = reconstruction?.completeness_score ?? 1.0;

  return (
    <div className="min-h-screen bg-nexus-900 text-slate-100 flex flex-col">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isConnected={isConnected}
        completeness={completeness}
      />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'overview' && (
          <OverviewTab
            topology={topology}
            reconstruction={reconstruction}
            recentEvents={recentEvents}
            onConfigChange={handleConfigChange}
          />
        )}

        {activeTab === 'twin' && (
          <DigitalTwinGraph topology={topology} />
        )}

        {activeTab === 'telemetry' && (
          <LiveTelemetryStream events={recentEvents} />
        )}

        {activeTab === 'simulator' && (
          <IncidentSimulator topology={topology} />
        )}

        {activeTab === 'decision' && (
          <DecisionStudio topology={topology} />
        )}

        {activeTab === 'quality' && (
          <DataQualityRadar reconstruction={reconstruction} />
        )}

        {activeTab === 'experiments' && (
          <ExperimentRunner />
        )}
      </main>

      <footer className="border-t border-nexus-700/60 bg-nexus-850/40 py-3 px-6 text-center text-xs font-mono text-slate-500">
        NEXUS &bull; Real-Time Adaptive Digital Twin & Decision Engine &bull; Research-Grade Closed-Loop Resilience System
      </footer>
    </div>
  );
};
