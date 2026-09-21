export interface TwinNode {
  id: string;
  name: string;
  type: string;
  lat: number;
  lon: number;
  state: 'OPERATIONAL' | 'DEGRADED' | 'CRITICAL' | 'FAILED' | 'OFFLINE';
  source: 'OBSERVED' | 'INFERRED' | 'UNKNOWN';
  confidence: number;
  pressure: number;
  flow: number;
  temp: number;
  vibration: number;
  power: number;
  battery: number;
  last_updated: string;
}

export interface TwinEdge {
  source: string;
  target: string;
  relation: string;
}

export interface TopologyData {
  node_count: number;
  edge_count: number;
  nodes: TwinNode[];
  edges: TwinEdge[];
}

export interface StateReconstructionData {
  timestamp: string;
  total_nodes: number;
  observed_nodes: number;
  inferred_nodes: number;
  unknown_nodes: number;
  completeness_score: number;
  observability_score: number;
  nodes: Record<string, {
    state: string;
    source: string;
    confidence: number;
    values: {
      pressure_psi: number;
      flow_rate_gpm: number;
      temperature_c: number;
      vibration_rms: number;
    };
  }>;
}

export interface TelemetryReadingEvent {
  node_id: string;
  state: string;
  source: string;
  pressure: number;
  flow: number;
  temp: number;
  vibration: number;
  confidence: number;
  timestamp: string;
}

export interface DarkProcessMetrics {
  total_transitions_evaluated: number;
  detected_missing_transitions: number;
  process_completeness_rate: number;
  dark_process_index: number;
  recent_missing_events: Array<{
    device_id: string;
    timestamp: string;
    expected: string;
    observed: string;
    confidence: number;
    hypothesis: string;
  }>;
}
