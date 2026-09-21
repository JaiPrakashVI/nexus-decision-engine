"""
NEXUS Anomaly Detection Benchmarking & Evaluation
Computes ground-truth precision, recall, F1-score, and latency comparisons between detectors.
"""

from typing import Dict, List, Any
import time
import numpy as np

from anomaly_detection.diagnostics.statistical import StreamingStatisticalDetector
from anomaly_detection.diagnostics.ml_detector import MultivariateMLDetector


def evaluate_detector_performance(num_samples: int = 1000, anomaly_ratio: float = 0.1) -> Dict[str, Any]:
    """
    Generates synthetic labeled test data with known anomalies and benchmarks both detectors.
    Returns quantitative evaluation comparison.
    """
    np.random.seed(42)
    num_anomalies = int(num_samples * anomaly_ratio)
    labels = np.zeros(num_samples, dtype=int)
    anomaly_indices = np.random.choice(num_samples, num_anomalies, replace=False)
    labels[anomaly_indices] = 1

    # Base normal telemetry
    p = np.random.normal(60.0, 5.0, num_samples)
    q = np.random.normal(50.0, 5.0, num_samples)
    t = np.random.normal(20.0, 2.0, num_samples)
    v = np.random.exponential(0.5, num_samples)
    w = 0.3 * q + np.random.normal(5.0, 0.5, num_samples)

    # Inject anomalies into designated indices
    for idx in anomaly_indices:
        atype = idx % 3
        if atype == 0:  # Spike
            p[idx] += 40.0
        elif atype == 1:  # Flow drop / cavitation
            q[idx] = 0.0
            w[idx] += 30.0  # High power, zero flow
        else:  # High vibration
            v[idx] += 12.0

    # 1. Benchmark Statistical Detector
    stat_detector = StreamingStatisticalDetector()
    stat_preds = []
    t0 = time.perf_counter()
    for i in range(num_samples):
        is_anom, _, _, _ = stat_detector.check_reading("bench_dev", "pressure", float(p[i]))
        stat_preds.append(1 if is_anom else 0)
    stat_time = (time.perf_counter() - t0) * 1000.0  # ms total

    # 2. Benchmark ML Detector
    ml_detector = MultivariateMLDetector()
    ml_preds = []
    t0 = time.perf_counter()
    for i in range(num_samples):
        is_anom, _, _ = ml_detector.evaluate_vector(
            float(p[i]), float(q[i]), float(t[i]), float(v[i]), float(w[i])
        )
        ml_preds.append(1 if is_anom else 0)
    ml_time = (time.perf_counter() - t0) * 1000.0  # ms total

    def compute_metrics(y_true, y_pred, total_ms):
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        tp = int(np.sum((y_true == 1) & (y_pred == 1)))
        fp = int(np.sum((y_true == 0) & (y_pred == 1)))
        fn = int(np.sum((y_true == 1) & (y_pred == 0)))
        tn = int(np.sum((y_true == 0) & (y_pred == 0)))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        avg_latency_us = (total_ms / len(y_true)) * 1000.0

        return {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "avg_latency_microseconds": round(avg_latency_us, 2),
        }

    return {
        "dataset_size": num_samples,
        "anomalies_injected": num_anomalies,
        "statistical_detector": compute_metrics(labels, stat_preds, stat_time),
        "multivariate_ml_detector": compute_metrics(labels, ml_preds, ml_time),
    }
