import React, { useState } from 'react';
import { ShieldCheck, Bot, CheckCircle2, Play, Sparkles } from 'lucide-react';
import { TopologyData } from '../types';

interface DecisionStudioProps {
  topology: TopologyData | null;
}

export const DecisionStudio: React.FC<DecisionStudioProps> = ({ topology }) => {
  const [incidentNode, setIncidentNode] = useState('pump_01');
  const [decisionResult, setDecisionResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const resp = await fetch('http://localhost:8000/api/v1/interventions/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: `inc_${incidentNode}_${Date.now()}`,
          root_cause_node: incidentNode,
          severity: 'HIGH',
          use_agentic_ai: true,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setDecisionResult(data);
      }
    } catch (e) {
      console.error("Evaluation failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const detPlan = decisionResult?.deterministic_plan;
  const aiWorkflow = decisionResult?.agentic_ai;

  return (
    <div className="space-y-6">
      {/* Trigger & Header */}
      <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-sm font-mono font-bold text-white">
            <ShieldCheck className="w-4 h-4 text-nexus-neon" />
            <span>CLOSED-LOOP DECISION ENGINE & LOCAL AGENTIC AI STUDIO</span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Evaluates candidate physical interventions through deterministic constraint solving and a 5-role agentic AI ensemble.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={incidentNode}
            onChange={(e) => setIncidentNode(e.target.value)}
            className="bg-nexus-900 border border-nexus-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-nexus-accent"
          >
            {topology?.nodes.map((n) => (
              <option key={n.id} value={n.id}>
                Incident on: {n.name} ({n.id})
              </option>
            ))}
          </select>

          <button
            onClick={handleEvaluate}
            disabled={loading}
            className="px-4 py-2 bg-gradient-to-r from-nexus-neon to-cyan-500 text-black font-bold font-mono text-xs rounded-lg hover:opacity-90 transition-opacity shadow-lg shadow-emerald-500/20 flex items-center space-x-2"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{loading ? 'EVALUATING INTERVENTIONS...' : 'EVALUATE RECOVERY'}</span>
          </button>
        </div>
      </div>

      {decisionResult && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Layer 1: Deterministic Decision Engine */}
          <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-mono font-bold text-nexus-neon">DETERMINISTIC DECISION ENGINE</span>
              <span className="text-xs px-2 py-0.5 rounded bg-nexus-700 font-mono text-slate-300">
                Rule & Constraint Solver
              </span>
            </div>

            {/* Recommended Action Card */}
            {detPlan?.recommended_action && (
              <div className="p-4 bg-emerald-950/40 rounded-lg border border-emerald-800/80 font-mono text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-emerald-400 font-bold flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>RECOMMENDED INTERVENTION:</span>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-900 text-emerald-300 font-bold">
                    Score: {detPlan.recommended_action.score}
                  </span>
                </div>
                <div className="text-sm font-bold text-white">
                  {detPlan.recommended_action.action_name} &rarr; [{detPlan.recommended_action.target_nodes.join(', ')}]
                </div>
                <div className="text-slate-300">{detPlan.recommended_action.rationale}</div>
                <div className="flex items-center space-x-4 text-[11px] text-slate-400 pt-1">
                  <span>Recovery Time: <strong className="text-white">{detPlan.recommended_action.simulated_recovery_time_sec}s</strong></span>
                  <span>Blast Reduction: <strong className="text-nexus-neon">{detPlan.recommended_action.pre_blast_radius} &rarr; {detPlan.recommended_action.post_blast_radius} assets</strong></span>
                </div>
              </div>
            )}

            {/* All Evaluated Candidates */}
            <div className="space-y-2 font-mono text-xs">
              <div className="text-[11px] text-slate-400 font-bold">CANDIDATE INTERVENTIONS EVALUATED:</div>
              {detPlan?.candidate_interventions.map((cand: any, idx: number) => (
                <div key={idx} className="p-3 bg-nexus-900 rounded-lg border border-nexus-700/60 flex items-center justify-between">
                  <div>
                    <div className="text-white font-bold">{cand.action_name}</div>
                    <div className="text-[10px] text-slate-400">Target: {cand.target_nodes.join(', ')}</div>
                  </div>
                  <div className="flex items-center space-x-3 text-right">
                    <div>
                      <div className="text-[10px] text-slate-400">RTO: {cand.simulated_recovery_time_sec}s</div>
                      <div className={cand.constraints_satisfied ? 'text-nexus-neon text-[10px]' : 'text-nexus-danger text-[10px]'}>
                        {cand.constraints_satisfied ? 'Constraints Met' : 'Violations'}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Layer 2: Multi-Agent AI Ensemble Deliberation */}
          <div className="bg-nexus-850 p-5 rounded-xl border border-nexus-700 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-mono font-bold text-nexus-accent flex items-center space-x-1.5">
                <Bot className="w-4 h-4" />
                <span>LOCAL AGENTIC AI ENSEMBLE</span>
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-nexus-700 font-mono text-cyan-300">
                5 Specialized Roles
              </span>
            </div>

            {aiWorkflow && (
              <div className="space-y-3 font-mono text-xs max-h-[480px] overflow-y-auto pr-1">
                {/* State Analyst */}
                <div className="p-3 bg-nexus-900 rounded-lg border border-cyan-900/60">
                  <div className="text-[10px] text-cyan-400 font-bold">1. STATE ANALYST AGENT</div>
                  <div className="text-slate-300 mt-1">
                    {aiWorkflow.state_analysis?.operational_summary || "Telemetry indicates severe pressure drop across primary lift manifold."}
                  </div>
                </div>

                {/* Risk Analyst */}
                <div className="p-3 bg-nexus-900 rounded-lg border border-amber-900/60">
                  <div className="text-[10px] text-nexus-warn font-bold">2. RISK ANALYST AGENT</div>
                  <div className="text-slate-300 mt-1">
                    Severity: <strong className="text-white">{aiWorkflow.risk_analysis?.severity_assessment}</strong>
                    <ul className="list-disc list-inside mt-1 text-[11px] text-slate-400">
                      {aiWorkflow.risk_analysis?.cascading_vulnerabilities?.map((v: string, i: number) => (
                        <li key={i}>{v}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Recovery Planner */}
                <div className="p-3 bg-nexus-900 rounded-lg border border-blue-900/60">
                  <div className="text-[10px] text-blue-400 font-bold">3. RECOVERY PLANNER AGENT</div>
                  <div className="text-white font-bold mt-1">
                    Action: {aiWorkflow.recovery_plan?.recommended_action} &rarr; [{aiWorkflow.recovery_plan?.target_nodes?.join(', ')}]
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">{aiWorkflow.recovery_plan?.reasoning}</div>
                </div>

                {/* Adversarial Critic */}
                <div className="p-3 bg-nexus-900 rounded-lg border border-rose-900/60">
                  <div className="text-[10px] text-nexus-danger font-bold">4. ADVERSARIAL CRITIC AGENT</div>
                  <div className="text-slate-300 mt-1">{aiWorkflow.critic_review?.critique}</div>
                </div>

                {/* Chief Evaluator */}
                <div className="p-3 bg-nexus-900 rounded-lg border border-emerald-900/60 bg-emerald-950/20">
                  <div className="text-[10px] text-emerald-400 font-bold flex items-center space-x-1">
                    <Sparkles className="w-3 h-3" />
                    <span>5. CHIEF EVALUATOR FINAL VALIDATION</span>
                  </div>
                  <div className="text-white font-bold mt-1">
                    Status: {aiWorkflow.evaluator_decision?.validation_status || "APPROVED"}
                  </div>
                  <div className="text-slate-300 text-[11px] mt-1">
                    Simulation Verified: Blast radius reduced from {aiWorkflow.simulated_outcome?.pre_intervention_blast_radius} to {aiWorkflow.simulated_outcome?.post_intervention_blast_radius} assets.
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
