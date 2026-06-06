import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import joblib

from backend.models.risk_engine import PipelineRiskEngine, RiskAssessment
from backend.changepoint.detector import PipelineChangePointDetector
from backend.anomaly.lstm_detector import LSTMAnomalyDetector
from backend.explainability.explainer import LeakExplainer


class PipelineMonitoringService:
    def __init__(self, data_path: str = "data/pipeline_sensor_data.csv"):
        self.data_path = Path(data_path)
        self.risk_engine = PipelineRiskEngine()
        self.changepoint_detector = PipelineChangePointDetector()
        self.data = None
        self._load_data()

    def _load_data(self):
        if self.data_path.exists():
            self.data = pd.read_csv(self.data_path)
            self.data["timestamp"] = pd.to_datetime(self.data["timestamp"])

    def get_dashboard_summary(self) -> Dict:
        if self.data is None:
            return {"error": "No data loaded"}

        latest = self.data.groupby("pipeline_id").last().reset_index()

        assessments = self.risk_engine.batch_risk_assessment(latest)
        network_summary = self.risk_engine.aggregate_network_risk(assessments)

        return {
            "total_pipelines": len(latest),
            "active_alerts": network_summary["critical_count"] + network_summary["high_count"],
            "average_health": network_summary["average_health"],
            "network_risk": network_summary["network_risk"],
            "severity_distribution": {
                "critical": network_summary["critical_count"],
                "high": network_summary["high_count"],
                "medium": network_summary["medium_count"],
                "low": network_summary["low_count"],
            },
            "pipeline_statuses": [
                {
                    "pipeline_id": a.pipeline_id,
                    "risk_score": a.leak_risk_score,
                    "health_score": a.pipeline_health_score,
                    "severity": a.severity,
                }
                for a in assessments
            ],
        }

    def get_pipeline_detail(self, pipeline_id: str, n_points: int = 500) -> Dict:
        if self.data is None:
            return {"error": "No data loaded"}

        pipeline_data = self.data[self.data["pipeline_id"] == pipeline_id].tail(n_points)

        if pipeline_data.empty:
            return {"error": f"Pipeline {pipeline_id} not found"}

        latest = pipeline_data.iloc[-1]

        def safe_numeric(value, default: float = 0.0) -> float:
            if pd.isna(value):
                return default
            value = float(value)
            if not np.isfinite(value):
                return default
            return value

        assessment = self.risk_engine.compute_risk(
            pressure_score=safe_numeric(latest.get("pressure_anomaly_score", 0)),
            acoustic_score=safe_numeric(latest.get("acoustic_anomaly_score", 0)),
            structural_score=safe_numeric(latest.get("structural_risk_index", 0)),
            flow_score=safe_numeric(latest.get("flow_imbalance_score", 0)),
            pipeline_id=pipeline_id,
        )

        pipe_age_series = pipeline_data["pipe_age"].dropna()
        pipe_age = safe_numeric(pipe_age_series.iloc[0] if not pipe_age_series.empty else 0.0)

        pipeline_data = pipeline_data.fillna(0)
        
        return {
            "pipeline_id": pipeline_id,
            "risk_assessment": {
                "risk_score": assessment.leak_risk_score,
                "health_score": assessment.pipeline_health_score,
                "severity": assessment.severity,
                "recommendations": assessment.recommendations,
            },
            "time_series": {
                "timestamps": pipeline_data["timestamp"].astype(str).tolist(),
                "inlet_pressure": pipeline_data["inlet_pressure"].tolist(),
                "outlet_pressure": pipeline_data["outlet_pressure"].tolist(),
                "pressure_drop": pipeline_data["pressure_drop"].tolist(),
                "flow_rate": pipeline_data["flow_rate"].tolist(),
                "acoustic_signal_amplitude": pipeline_data["acoustic_signal_amplitude"].tolist(),
                "vibration_intensity": pipeline_data["vibration_intensity"].tolist(),
                "leak_probability": pipeline_data["leak_probability"].tolist(),
            },
            "statistics": {
                "avg_pressure": safe_numeric(pipeline_data["inlet_pressure"].mean()),
                "avg_flow": safe_numeric(pipeline_data["flow_rate"].mean()),
                "avg_acoustic": safe_numeric(pipeline_data["acoustic_signal_amplitude"].mean()),
                "pipe_age": pipe_age,
            },
        }

    def detect_changepoints(self, pipeline_id: str) -> Dict:
        if self.data is None:
            return {"error": "No data loaded"}

        pipeline_data = self.data[self.data["pipeline_id"] == pipeline_id].tail(1000)

        if pipeline_data.empty:
            return {"error": f"Pipeline {pipeline_id} not found"}

        pressure_result = self.changepoint_detector.detect_pressure_changepoints(
            pipeline_data["inlet_pressure"].values
        )
        flow_result = self.changepoint_detector.detect_flow_changepoints(
            pipeline_data["flow_rate"].values
        )
        acoustic_result = self.changepoint_detector.detect_acoustic_changepoints(
            pipeline_data["acoustic_signal_amplitude"].values
        )

        results = {
            "pressure": pressure_result,
            "flow_rate": flow_result,
            "acoustic": acoustic_result,
        }
        overall_score = self.changepoint_detector.compute_change_point_score(results)

        return {
            "pipeline_id": pipeline_id,
            "overall_changepoint_score": overall_score,
            "pressure": {
                "change_points": pressure_result.change_points,
                "scores": pressure_result.scores,
                "segments": pressure_result.segments,
            },
            "flow_rate": {
                "change_points": flow_result.change_points,
                "scores": flow_result.scores,
                "segments": flow_result.segments,
            },
            "acoustic": {
                "change_points": acoustic_result.change_points,
                "scores": acoustic_result.scores,
                "segments": acoustic_result.segments,
            },
        }

    def predict_leak(self, features: Dict) -> Dict:
        assessment = self.risk_engine.compute_risk(
            pressure_score=features.get("pressure_anomaly_score", 0),
            acoustic_score=features.get("acoustic_anomaly_score", 0),
            structural_score=features.get("structural_risk_index", 0),
            flow_score=features.get("flow_imbalance_score", 0),
            changepoint_score=features.get("changepoint_score", 0),
            pipeline_id=features.get("pipeline_id", "unknown"),
        )

        return {
            "pipeline_id": assessment.pipeline_id,
            "leak_detected": assessment.leak_risk_score > 0.5,
            "leak_probability": assessment.leak_risk_score,
            "severity": assessment.severity,
            "health_score": assessment.pipeline_health_score,
            "contributing_factors": assessment.contributing_factors,
            "recommendations": assessment.recommendations,
        }

    def get_alerts(self, severity_filter: Optional[str] = None) -> List[Dict]:
        if self.data is None:
            return []

        latest = self.data.groupby("pipeline_id").last().reset_index()
        assessments = self.risk_engine.batch_risk_assessment(latest)

        alerts = []
        for a in assessments:
            if a.severity in ["HIGH", "CRITICAL"]:
                if severity_filter and a.severity != severity_filter:
                    continue
                alerts.append({
                    "pipeline_id": a.pipeline_id,
                    "severity": a.severity,
                    "risk_score": a.leak_risk_score,
                    "health_score": a.pipeline_health_score,
                    "recommendations": a.recommendations,
                })

        return sorted(alerts, key=lambda x: x["risk_score"], reverse=True)

    def get_network_view(self) -> Dict:
        if self.data is None:
            return {"error": "No data loaded"}

        latest = self.data.groupby("pipeline_id").last().reset_index()
        assessments = self.risk_engine.batch_risk_assessment(latest)

        nodes = []
        for a in assessments:
            nodes.append({
                "id": a.pipeline_id,
                "risk_score": a.leak_risk_score,
                "health_score": a.pipeline_health_score,
                "severity": a.severity,
            })

        edges = []
        pipeline_ids = [a.pipeline_id for a in assessments]
        for i in range(len(pipeline_ids) - 1):
            edges.append({
                "source": pipeline_ids[i],
                "target": pipeline_ids[i + 1],
                "stress": float(np.random.uniform(0.1, 0.8)),
            })
        for _ in range(len(pipeline_ids) // 3):
            i, j = np.random.choice(len(pipeline_ids), 2, replace=False)
            edges.append({
                "source": pipeline_ids[i],
                "target": pipeline_ids[j],
                "stress": float(np.random.uniform(0.2, 0.6)),
            })

        return {"nodes": nodes, "edges": edges}
