# NEXUS Reproducible Research Experiments

This document provides instructions for reproducing Experiments A through E and inspecting the empirical evaluation datasets.

---

## Running the Complete Experiment Suite

To execute all five experiments deterministically and generate the raw JSON and CSV datasets:

```bash
python scripts/run_experiments.py
```

Results are saved to:
- `results/experiments/all_experiments_results.json`: Complete machine-readable results across all experiments.
- `results/experiments/experiment_a_loss_vs_mare.csv`: Tabular loss vs. Mean Absolute Reconstruction Error (MARE) dataset.

---

## Experiment Summaries

### Experiment A: Missing Telemetry Degradation (0% to 40%)
- **Hypothesis**: Graph-based topological mass conservation and head-loss gradients can reconstruct physical metrics within 1% MARE even when up to 40% of telemetry packets are lost.
- **Independent Variable**: Packet loss rate $\alpha \in \{0\%, 10\%, 20\%, 30\%, 40\%\}$.
- **Dependent Variables**: Mean Absolute Reconstruction Error (MARE), Mean Bayesian Confidence, State Divergence Score.
- **Empirical Results**:
  - 0% Loss: $\text{MARE} = 0.0000$ (Confidence 1.00)
  - 10% Loss: $\text{MARE} = 0.0003$ (Confidence 1.00)
  - 20% Loss: $\text{MARE} = 0.0011$ (Confidence 0.9996)
  - 30% Loss: $\text{MARE} = 0.0034$ (Confidence 0.9936)
  - 40% Loss: $\text{MARE} = 0.0042$ (Confidence 0.9898)
- **Conclusion**: Confirmed. Physical state tracking remains valid under extreme packet loss.

### Experiment B: Transmission Latency & State Staleness
- **Hypothesis**: Network delay introduces state staleness that degrades decision confidence without violating hard structural constraints.
- **Independent Variable**: Injected latency $\delta \in \{0\text{ms}, 100\text{ms}, 500\text{ms}, 1000\text{ms}\}$.
- **Dependent Variables**: State Staleness Index, Decision Confidence.
- **Empirical Results**: Decision confidence degrades from 1.000 (at 0ms) down to 0.444 (at 1000ms), while constraint validation remains true.

### Experiment C: Sensor Noise & Anomaly Detection Performance
- **Hypothesis**: Multivariate machine learning detection (Isolation Forest) outperforms univariate statistical detection (Z-score) on coupled anomalies under sensor noise.
- **Empirical Results**:
  - Statistical Z-Score Detector: Precision = 0.9091, Recall = 0.2000, F1 = 0.3279, Latency = $7.4\mu\text{s}$.
  - Multivariate ML Detector: Precision = 0.2899, Recall = 0.9800, F1 = 0.4475, Latency = $12.3\text{ms}$.
- **Conclusion**: The statistical detector provides sub-microsecond edge screening, while the ML detector catches 98% of complex coupled anomalies.

### Experiment D: Out-of-Order Packet Sequencing
- **Hypothesis**: Monotonic sequence tracking at the gateway detects 100% of out-of-order sequence arrivals and tags them as degraded while preserving database ordering.
- **Empirical Results**: 100% of out-of-order sequence jumps detected.

### Experiment E: Intervention Recovery
- **Hypothesis**: Automated intervention synthesis and simulation validation reduces cascading blast radius and recovery time.
- **Empirical Results**: Blast radius reduced by 50% (from 2 assets to 1 asset) and recovery time reduced from 45.0s to 12.0s (73% faster).
