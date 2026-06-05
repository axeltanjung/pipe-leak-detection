import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class RiskAssessment:
    pipeline_id: str
    leak_risk_score: float
    pipeline_health_score: float
    severity: str
    contributing_factors: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class PipelineRiskEngine:
    def __init__(self):
        self.weights = {
            "pressure_anomaly": 0.30,
            "acoustic_anomaly": 0.25,
            "structural_degradation": 0.20,
            "flow_imbalance": 0.15,
            "change_point": 0.10,
        }
        self.severity_thresholds = {
            "LOW": (0.0, 0.25),
            "MEDIUM": (0.25, 0.50),
            "HIGH": (0.50, 0.75),
            "CRITICAL": (0.75, 1.0),
        }

    def compute_risk(
        self,
        pressure_score: float,
        acoustic_score: float,
        structural_score: float,
        flow_score: float,
        changepoint_score: float = 0.0,
        pipeline_id: str = "unknown",
    ) -> RiskAssessment:
        scores = {
            "pressure_anomaly": np.clip(pressure_score, 0, 1),
            "acoustic_anomaly": np.clip(acoustic_score, 0, 1),
            "structural_degradation": np.clip(structural_score, 0, 1),
            "flow_imbalance": np.clip(flow_score, 0, 1),
            "change_point": np.clip(changepoint_score, 0, 1),
        }

        leak_risk = sum(self.weights[k] * scores[k] for k in self.weights)
        leak_risk = np.clip(leak_risk, 0, 1)
        health_score = (1 - leak_risk) * 100

        severity = self._classify_severity(leak_risk)
        recommendations = self._generate_recommendations(scores, severity)

        return RiskAssessment(
            pipeline_id=pipeline_id,
            leak_risk_score=round(leak_risk, 4),
            pipeline_health_score=round(health_score, 2),
            severity=severity,
            contributing_factors=scores,
            recommendations=recommendations,
        )

    def batch_risk_assessment(self, df: pd.DataFrame) -> List[RiskAssessment]:
        assessments = []
        for _, row in df.iterrows():
            assessment = self.compute_risk(
                pressure_score=row.get("pressure_anomaly_score", 0),
                acoustic_score=row.get("acoustic_anomaly_score", 0),
                structural_score=row.get("structural_risk_index", 0),
                flow_score=row.get("flow_imbalance_score", 0),
                changepoint_score=row.get("changepoint_score", 0),
                pipeline_id=row.get("pipeline_id", "unknown"),
            )
            assessments.append(assessment)
        return assessments

    def _classify_severity(self, risk_score: float) -> str:
        for severity, (low, high) in self.severity_thresholds.items():
            if low <= risk_score < high:
                return severity
        return "CRITICAL"

    def _generate_recommendations(self, scores: Dict[str, float], severity: str) -> List[str]:
        recommendations = []

        if severity == "CRITICAL":
            recommendations.append("IMMEDIATE: Isolate pipeline section and deploy emergency response")
            recommendations.append("Reduce operating pressure to minimum safe level")
        elif severity == "HIGH":
            recommendations.append("Schedule urgent inspection within 24 hours")
            recommendations.append("Increase monitoring frequency to every 5 minutes")

        if scores["pressure_anomaly"] > 0.6:
            recommendations.append("Investigate pressure differential - possible leak or blockage")
        if scores["acoustic_anomaly"] > 0.6:
            recommendations.append("Deploy acoustic leak detection team to segment")
        if scores["structural_degradation"] > 0.6:
            recommendations.append("Schedule pipeline integrity inspection (PIG run)")
        if scores["flow_imbalance"] > 0.6:
            recommendations.append("Verify flow meters and check for product loss")
        if scores["change_point"] > 0.5:
            recommendations.append("Analyze recent operational changes for root cause")

        if not recommendations:
            recommendations.append("Continue routine monitoring - no immediate action required")

        return recommendations

    def aggregate_network_risk(self, assessments: List[RiskAssessment]) -> Dict:
        if not assessments:
            return {"network_risk": 0, "health": 100, "critical_count": 0}

        risks = [a.leak_risk_score for a in assessments]
        return {
            "network_risk": round(np.mean(risks), 4),
            "max_risk": round(np.max(risks), 4),
            "min_risk": round(np.min(risks), 4),
            "average_health": round(np.mean([a.pipeline_health_score for a in assessments]), 2),
            "critical_count": sum(1 for a in assessments if a.severity == "CRITICAL"),
            "high_count": sum(1 for a in assessments if a.severity == "HIGH"),
            "medium_count": sum(1 for a in assessments if a.severity == "MEDIUM"),
            "low_count": sum(1 for a in assessments if a.severity == "LOW"),
            "total_pipelines": len(assessments),
        }
