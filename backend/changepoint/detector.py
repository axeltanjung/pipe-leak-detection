import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import ruptures as rpt
from dataclasses import dataclass


@dataclass
class ChangePointResult:
    signal_name: str
    change_points: List[int]
    scores: List[float]
    segments: List[dict]


class PipelineChangePointDetector:
    def __init__(self, min_segment_length: int = 20):
        self.min_segment_length = min_segment_length
        self.models = {
            "rbf": "rbf",
            "linear": "linear",
            "normal": "normal",
            "cosine": "cosine",
        }

    def detect_pressure_changepoints(
        self, pressure_series: np.ndarray, n_breakpoints: int = 5, model: str = "rbf"
    ) -> ChangePointResult:
        signal = np.array(pressure_series).reshape(-1, 1)
        algo = rpt.Pelt(model=model, min_size=self.min_segment_length).fit(signal)
        change_points = algo.predict(pen=10)

        scores = self._compute_segment_scores(signal.flatten(), change_points)
        segments = self._build_segments(signal.flatten(), change_points)

        return ChangePointResult(
            signal_name="pressure",
            change_points=change_points,
            scores=scores,
            segments=segments,
        )

    def detect_flow_changepoints(
        self, flow_series: np.ndarray, n_breakpoints: int = 5
    ) -> ChangePointResult:
        signal = np.array(flow_series).reshape(-1, 1)
        algo = rpt.Binseg(model="normal", min_size=self.min_segment_length).fit(signal)
        change_points = algo.predict(n_bkps=n_breakpoints)

        scores = self._compute_segment_scores(signal.flatten(), change_points)
        segments = self._build_segments(signal.flatten(), change_points)

        return ChangePointResult(
            signal_name="flow_rate",
            change_points=change_points,
            scores=scores,
            segments=segments,
        )

    def detect_acoustic_changepoints(
        self, acoustic_series: np.ndarray, pen: float = 5.0
    ) -> ChangePointResult:
        signal = np.array(acoustic_series).reshape(-1, 1)
        algo = rpt.KernelCPD(kernel="rbf", min_size=self.min_segment_length).fit(signal)
        change_points = algo.predict(pen=pen)

        scores = self._compute_segment_scores(signal.flatten(), change_points)
        segments = self._build_segments(signal.flatten(), change_points)

        return ChangePointResult(
            signal_name="acoustic",
            change_points=change_points,
            scores=scores,
            segments=segments,
        )

    def detect_multivariate_changepoints(
        self, signals: Dict[str, np.ndarray], pen: float = 10.0
    ) -> Dict[str, ChangePointResult]:
        results = {}
        combined = np.column_stack(list(signals.values()))

        algo = rpt.Pelt(model="rbf", min_size=self.min_segment_length).fit(combined)
        change_points = algo.predict(pen=pen)

        for name, signal in signals.items():
            scores = self._compute_segment_scores(signal, change_points)
            segments = self._build_segments(signal, change_points)
            results[name] = ChangePointResult(
                signal_name=name,
                change_points=change_points,
                scores=scores,
                segments=segments,
            )

        return results

    def _compute_segment_scores(
        self, signal: np.ndarray, change_points: List[int]
    ) -> List[float]:
        scores = []
        prev = 0
        for cp in change_points:
            if cp > len(signal):
                cp = len(signal)
            segment = signal[prev:cp]
            if len(segment) > 1:
                mean_shift = abs(np.mean(segment) - np.mean(signal))
                var_ratio = np.var(segment) / (np.var(signal) + 1e-8)
                score = min(1.0, (mean_shift / (np.std(signal) + 1e-8)) * 0.5 + var_ratio * 0.5)
            else:
                score = 0.0
            scores.append(score)
            prev = cp
        return scores

    def _build_segments(
        self, signal: np.ndarray, change_points: List[int]
    ) -> List[dict]:
        segments = []
        prev = 0
        for i, cp in enumerate(change_points):
            if cp > len(signal):
                cp = len(signal)
            segment = signal[prev:cp]
            segments.append({
                "start": prev,
                "end": cp,
                "mean": float(np.mean(segment)) if len(segment) > 0 else 0,
                "std": float(np.std(segment)) if len(segment) > 0 else 0,
                "min": float(np.min(segment)) if len(segment) > 0 else 0,
                "max": float(np.max(segment)) if len(segment) > 0 else 0,
                "trend": float(np.polyfit(range(len(segment)), segment, 1)[0]) if len(segment) > 1 else 0,
            })
            prev = cp
        return segments

    def compute_change_point_score(self, results: Dict[str, ChangePointResult]) -> float:
        total_score = 0
        weights = {
            "pressure": 0.35,
            "flow_rate": 0.25,
            "acoustic": 0.25,
            "vibration": 0.15,
        }

        for name, result in results.items():
            weight = weights.get(name, 0.25)
            if result.scores:
                avg_score = np.mean(result.scores)
                n_changes = len(result.change_points)
                change_density = min(1.0, n_changes / 10)
                signal_score = avg_score * 0.6 + change_density * 0.4
                total_score += weight * signal_score

        return min(1.0, total_score)
