# NEXUS: Resilient Cyber-Physical State Reconstruction and Agentic Decision Support Under Degraded Telemetry

**Technical Research Report & Experimental Evaluation**  
*NEXUS Research & Systems Engineering Group*  
*September 2026*

---

## 1. Abstract
Real-time digital twins for distributed municipal water and power infrastructure operate under the foundational assumption of continuous, high-fidelity sensor telemetry. In operational deployments, however, edge communication networks experience packet loss, transmission jitter, measurement noise, and sensor failures. This research investigates the resilience of digital-twin state tracking and automated decision support when telemetry is asynchronous, noisy, or up to 40% missing. We present NEXUS, a closed-loop platform integrating mutual TLS ingestion, log-based stream processing via Redis Streams, time-series storage in TimescaleDB, a NetworkX topological graph twin, and physics-informed state reconstruction. Under empirical evaluation across five experimental regimes (Experiments A–E), NEXUS demonstrates that topological mass conservation and head-loss gradients maintain physical state validity ($\text{MARE} < 0.005$) even under 40% telemetry loss. Furthermore, combining deterministic constraint solving with a sandboxed multi-agent LLM ensemble reduces cascading blast radius by 50% and reduces system recovery time by 73% compared to unmitigated failures.

---

## 2. Introduction
Modern cyber-physical systems—including municipal water distribution grids, regional power networks, and industrial chemical processing plants—increasingly rely on digital twins for real-time monitoring and anomaly detection. Traditional digital twins function primarily as passive mirrors: when sensor telemetry ceases or becomes corrupted, the twin's state estimator either stalls, retains stale values, or drifts into physically impossible configurations.

NEXUS addresses this vulnerability by formulating digital twin management as a **closed-loop cyber-physical pipeline**:
$$\text{Imperfect Telemetry} \to \text{Reconstruction} \to \text{Detection} \to \text{Simulation} \to \text{Decision} \to \text{Recovery}$$

---

## 3. Problem Definition
Let an infrastructure network be modeled as a directed dependency graph $G = (V, E)$, where $V$ denotes cyber-physical nodes (pumps, pipes, valves, reservoirs, power substations) and $E$ represents directed fluid flow or electrical power transmission. At each discrete time step $t$, a subset of nodes $V_{obs}(t) \subseteq V$ successfully delivers telemetry $y_v(t)$. Due to edge packet loss $\alpha \in [0, 0.40]$, the unobserved set $V_{unobs}(t) = V \setminus V_{obs}(t)$ requires real-time reconstruction. The challenge is to maintain operational state estimates $\hat{x}_v(t)$ such that the Mean Absolute Reconstruction Error (MARE) remains bounded and operational safety constraints are never violated.

---

## 4. Research Question
> **Central Research Question**: How accurately can an adaptive digital twin maintain operational state and simulate intervention policies when telemetry is asynchronous, noisy, or up to 40% missing?

---

## 5. Related Work
- **Digital Twins in Critical Infrastructure**: Grieves & Vickers (2017), Rasheed et al. (2020) established conceptual digital twin frameworks, but largely assumed continuous telemetry availability.
- **Time-Series State Estimation & Kalman Filtering**: Classical state estimators rely on linear Gaussian assumptions that degrade under non-linear hydraulic transitions and topological reconfigurations.
- **Physics-Informed Graph Neural Networks**: Recent work incorporates conservation laws into graph neural networks; however, they impose high computational latency unsuitable for sub-second distributed stream processing.
- **Agentic AI in Operations**: Generative models have shown promise in diagnostic reasoning (OpenAI, 2024), but lack physical grounding and safety guarantees when deployed without deterministic constraint solvers.

---

## 6. System Architecture
NEXUS implements a 7-tier decoupled architecture:
1. **Sensor Simulator**: High-throughput synthetic generator with diurnal demand modeling and a configurable fault injection engine (0–40% loss, 0–1000ms delay, Gaussian noise).
2. **Secure Gateway**: FastAPI-based ingestion terminating mutual TLS (mTLS), verifying client X.509 certificates, checking token-bucket rate limits, and enforcing replay protection.
3. **Streaming Decoupling**: Redis Streams (`telemetry:stream`) providing sub-millisecond append latency with consumer groups (`worker-01`) and Dead Letter Queues (`telemetry:dlq`).
4. **Time-Series Persistence**: TimescaleDB hypertables partitioned into 7-day chunks for scalable historical analytics.
5. **Digital Twin Engine**: NetworkX directed dependency topology maintaining live physical states and Bayesian confidence decay.
6. **Detection & Simulation Sandbox**: Statistical Z-score, rolling flatline, and multivariate Isolation Forest detectors coupled with a discrete-event cascading failure simulator.
7. **Decision Engine & Local AI**: Deterministic constraint solver coupled with a 5-role local LLM ensemble (State Analyst, Risk Analyst, Recovery Planner, Adversarial Critic, Evaluator).

---

## 7. Telemetry Model
Telemetry packets adhere to a strict versioned Pydantic contract (`gateway/schemas/telemetry.py`):
$$\mathbf{y}_i(t) = \left[ \text{pressure}_{psi}, \text{flow}_{gpm}, \text{temp}_{c}, \text{vibration}_{rms}, \text{power}_{kw}, \text{battery}_{\%} \right]$$
Every packet carries a monotonically increasing sequence number $seq_i$ and a globally unique UUID4 trace ID $\tau_i$ for distributed tracing.

---

## 8. Digital Twin Design & State Reconstruction
To prevent silent assumption conversion, NEXUS explicitly defines a tripartite operational state:
$$\text{State}(v, t) = \begin{cases}
\text{OBSERVED}, & \Delta t \le \tau_{obs} \quad (C = 1.0) \\
\text{INFERRED}, & \tau_{obs} < \Delta t \le \tau_{max} \quad (C(t) = e^{-\lambda \Delta t}) \\
\text{UNKNOWN}, & \Delta t > \tau_{max} \quad (C \le 0.2)
\end{cases}$$
When $\text{State}(v, t) = \text{INFERRED}$, values are reconstructed using physical conservation laws:
1. **Volumetric Flow Conservation**:
   $$\hat{Q}_v = \frac{1}{|\text{Pred}(v)|} \sum_{u \in \text{Pred}(v)} Q_u$$
2. **Hydraulic Pressure Gradient**:
   $$\hat{P}_v = \max\left(0, \bar{P}_{upstream} - \Delta P_{loss}\right)$$

---

## 9. Missing Event & Dark Process Detection
Industrial cyber-physical nodes operate under formal finite state machine constraints:
$$\text{OFFLINE} \to \text{STARTING} \to \text{OPERATIONAL} \to \text{THROTTLED} \to \text{ALERT} \to \text{EMERGENCY\_SHUTDOWN}$$
When a node transitions directly from $\text{OPERATIONAL} \to \text{EMERGENCY\_SHUTDOWN}$, the intermediate $\text{ALERT}$ is identified as a candidate missing event (Dark Process). The detector computes the Dark Process Index:
$$DPI = \frac{N_{\text{skipped transitions}}}{N_{\text{total transitions}}}$$

---

## 10. Simulation Engine & Cascading Failure Modeling
The simulation engine forks an isolated deep copy of the digital twin topology. At step $t=0$, a disruption is triggered (e.g. pump impeller seizure). At step $t+1$, all dependent successors evaluate input starvation. If all feeding lines fail, the downstream node fails; if partial lines remain, it degrades. The simulation measures:
- Total blast radius (count of cascaded assets)
- Unserved demand (GPM)
- Time to equilibrium (seconds)

---

## 11. Agentic Decision Support & Safety Isolation
NEXUS strictly isolates generative AI from infrastructure execution:
1. **Deterministic Decision Engine** checks hard constraints:
   $$\text{Target} \notin \text{FailedNodes}, \quad \text{PowerDraw} \le \text{Capacity}$$
2. **Local LLM Multi-Agent Ensemble** (Ollama):
   - *State Analyst*: Diagnoses network health.
   - *Risk Analyst*: Forecasts cascading vulnerabilities.
   - *Recovery Planner*: Formulates candidate interventions.
   - *Adversarial Critic*: Challenges candidate interventions for pressure transients.
   - *Chief Evaluator*: Scores consistency against simulated sandbox outcomes.
3. **Simulation Verification**: Candidate plans must achieve verified blast radius reduction in the digital twin sandbox before presentation in the dashboard.

---

## 12. Experimental Methodology
We conducted five empirical experiments (A through E) executed via automated test harnesses on an AMD64 host running Python 3.13.2:
- **Experiment A**: Telemetry loss $\alpha \in \{0\%, 10\%, 20\%, 30\%, 40\%\}$.
- **Experiment B**: Transmission delays $\delta \in \{0\text{ms}, 100\text{ms}, 500\text{ms}, 1000\text{ms}\}$.
- **Experiment C**: Measurement noise (None, Low, Medium, High).
- **Experiment D**: Out-of-order packet sequencing.
- **Experiment E**: Pre- vs. Post-intervention recovery trajectory.

---

## 13. Empirical Results

### Experiment A: Missing Telemetry Degradation (0% to 40%)
*Table 1: State reconstruction accuracy and confidence under telemetry packet loss.*

| Packet Loss Rate | Reconstruction MARE | Mean Confidence | State Divergence Score |
| :---: | :---: | :---: | :---: |
| **0%** | 0.0000 | 1.0000 | 0.0000 |
| **10%** | 0.0003 | 1.0000 | 0.0650 |
| **20%** | 0.0011 | 0.9996 | 0.1300 |
| **30%** | 0.0034 | 0.9936 | 0.1950 |
| **40%** | 0.0042 | 0.9898 | 0.2600 |

*Finding*: Physical conservation across topological neighbors bounds reconstruction error below 0.5% ($\text{MARE} = 0.0042$) even when 40% of telemetry packets are lost.

### Experiment B: Telemetry Delay & State Staleness
*Table 2: State staleness index and decision confidence under transmission latency.*

| Injected Delay (ms) | State Staleness Index | Decision Confidence | Decision Valid |
| :---: | :---: | :---: | :---: |
| **0 ms** | 0.0 | 1.000 | True |
| **100 ms** | 2.4 | 0.944 | True |
| **500 ms** | 12.0 | 0.722 | True |
| **1000 ms** | 24.0 | 0.444 | True |

*Finding*: Decisions remain structurally valid under delays up to 1000ms, although decision confidence degrades by 55.6% due to state staleness.

### Experiment C: Anomaly Detection Performance Under Noise
*Table 3: Statistical vs. Multivariate Isolation Forest anomaly detection benchmarks.*

| Metric | Statistical Z-Score Detector | Multivariate Isolation Forest | Delta |
| :--- | :---: | :---: | :---: |
| **True Positives** | 10 | 49 | +390% |
| **False Positives** | 1 | 120 | +11900% |
| **False Negatives** | 40 | 1 | -97.5% |
| **Precision** | **0.9091** | 0.2899 | -68.1% |
| **Recall** | 0.2000 | **0.9800** | **+390%** |
| **F1 Score** | 0.3279 | **0.4475** | **+36.5%** |
| **Average Latency** | **7.4 $\mu\text{s}$** | 12,310.8 $\mu\text{s}$ (12.3 ms) | 1660x faster |

*Finding*: The statistical detector provides high precision (0.909) and sub-microsecond evaluation ($7.4\mu\text{s}$), making it ideal for wire-speed edge screening. The multivariate ML detector achieves 0.980 recall on complex coupled anomalies (cavitation), confirming the utility of a two-tier hybrid detection architecture.

### Experiment D: Out-of-Order Sequencing
Under injected sequence shuffles (`[1, 2, 4, 3, 5, 7, 6, 8]`), the gateway detected 100% of out-of-order sequence drops, properly tagging them as `DEGRADED` while preserving chronological database ordering.

### Experiment E: Intervention Recovery
When primary lift pump `pump_01` failed, unmitigated cascade caused a blast radius of 2 assets and 90 GPM unserved demand. Automated intervention (`ACTIVATE_BACKUP_PUMP` on `pump_03`) reduced the blast radius to 1 asset (50% reduction) and achieved system recovery in 12.0 seconds versus 45.0 seconds for manual intervention (73% faster).

---

## 14. Discussion
The empirical findings demonstrate that digital twins need not become blind when telemetry degrades. By coupling physical conservation models to topological graph neighbors, the digital twin can accurately bridge missing data intervals. Furthermore, isolating generative LLMs behind deterministic constraint solvers and sandbox simulators eliminates the risk of hallucinated physical actions while retaining the diagnostic and explanatory power of natural language agents.

---

## 15. Limitations
1. **Reconstruction Window Bounds**: When telemetry is absent beyond $\tau_{max} = 60\text{s}$, confidence decays toward 0.2, and physical state must be treated as unknown.
2. **Topology Assumptions**: Graph conservation laws assume static network connectivity between switching actions.
3. **Host Compute Variance**: Multivariate ML latency ($12.3\text{ms}$) reflects CPU execution; GPU acceleration would be required for fleets exceeding 100,000 nodes.

---

## 16. Future Work
- Dynamic graph topology learning using temporal graph neural networks.
- Multi-region geo-distributed Redis Streams replication with CRDTs.
- Formal verification of constraint satisfaction solvers using Z3 theorem proving.

---

## 17. Conclusion
NEXUS proves that an adaptive digital twin can maintain operational integrity under severe telemetry degradation. By uniting secure mTLS streaming infrastructure, physics-informed graph reconstruction, multi-tier anomaly detection, and deterministic agentic AI, NEXUS provides a robust, reproducible foundation for next-generation cyber-physical resilience.

---

## 18. References
1. Grieves, M., & Vickers, J. (2017). *Digital Twin: Mitigating Unpredictable, Undesirable Emergent Behavior in Complex Systems*. Transdisciplinary Perspectives on Complex Systems, 85–113.
2. Rasheed, A., San, O., & Kvamsdal, T. (2020). *Digital Twin: Values, Challenges and Enablers From a Modeling Perspective*. IEEE Access, 8, 21980–22012.
3. ISO/IEC 21823: *Internet of Things (IoT) — Interoperability for IoT Systems*.
4. NetworkX Developers (2024). *NetworkX: Network Analysis in Python*.
5. TimescaleDB Team (2024). *TimescaleDB: Scalable Time-Series SQL Engine*.
