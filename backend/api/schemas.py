from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: str
    models_loaded: bool


class PipelineFeatures(BaseModel):
    pipeline_id: str = Field(..., description="Pipeline segment identifier")
    pressure_anomaly_score: float = Field(0.0, ge=0, le=1)
    acoustic_anomaly_score: float = Field(0.0, ge=0, le=1)
    structural_risk_index: float = Field(0.0, ge=0, le=1)
    flow_imbalance_score: float = Field(0.0, ge=0, le=1)
    changepoint_score: float = Field(0.0, ge=0, le=1)


class LeakPrediction(BaseModel):
    pipeline_id: str
    leak_detected: bool
    leak_probability: float
    severity: str
    health_score: float
    contributing_factors: Dict[str, float]
    recommendations: List[str]


class RiskResponse(BaseModel):
    pipeline_id: str
    leak_risk_score: float
    pipeline_health_score: float
    severity: str
    contributing_factors: Dict[str, float]
    recommendations: List[str]


class DashboardSummary(BaseModel):
    total_pipelines: int
    active_alerts: int
    average_health: float
    network_risk: float
    severity_distribution: Dict[str, int]
    pipeline_statuses: List[Dict]


class PipelineDetail(BaseModel):
    pipeline_id: str
    risk_assessment: Dict
    time_series: Dict
    statistics: Dict


class ChangePointResponse(BaseModel):
    pipeline_id: str
    overall_changepoint_score: float
    pressure: Dict
    flow_rate: Dict
    acoustic: Dict


class AlertResponse(BaseModel):
    pipeline_id: str
    severity: str
    risk_score: float
    health_score: float
    recommendations: List[str]


class NetworkViewResponse(BaseModel):
    nodes: List[Dict]
    edges: List[Dict]


class ExplanationResponse(BaseModel):
    prediction: float
    base_value: float
    feature_contributions: Dict[str, float]
    risk_increasing_factors: List[Dict]
    risk_decreasing_factors: List[Dict]
