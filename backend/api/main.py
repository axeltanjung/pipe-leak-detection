from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging

from backend.api.schemas import (
    HealthResponse,
    PipelineFeatures,
    LeakPrediction,
    DashboardSummary,
    ChangePointResponse,
    NetworkViewResponse,
    ExplanationResponse,
    AlertResponse,
)
from backend.services.monitoring import PipelineMonitoringService
from backend.services.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_TIME = time.time()
monitoring_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global monitoring_service
    logger.info("Initializing Pipeline Leak Detection System...")
    init_db()
    monitoring_service = PipelineMonitoringService()
    logger.info("System initialized successfully")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Pipeline Leak Detection API",
    description="AI-powered pipeline integrity monitoring and leak detection system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    uptime = time.time() - START_TIME
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=f"{hours}h {minutes}m",
        models_loaded=monitoring_service is not None,
    )


@app.post("/predict/leak", response_model=LeakPrediction)
async def predict_leak(features: PipelineFeatures):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    result = monitoring_service.predict_leak(features.model_dump())
    return LeakPrediction(**result)


@app.post("/predict/risk")
async def predict_risk(features: PipelineFeatures):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    result = monitoring_service.predict_leak(features.model_dump())
    return result


@app.get("/pipeline/{pipeline_id}")
async def get_pipeline_detail(pipeline_id: str, n_points: int = Query(500, le=2000)):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    result = monitoring_service.get_pipeline_detail(pipeline_id, n_points)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/changepoint/detect/{pipeline_id}")
async def detect_changepoints(pipeline_id: str):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        result = monitoring_service.detect_changepoints(pipeline_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Change point detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomaly/acoustic/{pipeline_id}")
async def acoustic_anomaly(pipeline_id: str):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    detail = monitoring_service.get_pipeline_detail(pipeline_id)
    if "error" in detail:
        raise HTTPException(status_code=404, detail=detail["error"])
    ts = detail["time_series"]
    return {
        "pipeline_id": pipeline_id,
        "acoustic_data": ts["acoustic_signal_amplitude"],
        "timestamps": ts["timestamps"],
    }


@app.get("/anomaly/pressure/{pipeline_id}")
async def pressure_anomaly(pipeline_id: str):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    detail = monitoring_service.get_pipeline_detail(pipeline_id)
    if "error" in detail:
        raise HTTPException(status_code=404, detail=detail["error"])
    ts = detail["time_series"]
    return {
        "pipeline_id": pipeline_id,
        "inlet_pressure": ts["inlet_pressure"],
        "outlet_pressure": ts["outlet_pressure"],
        "pressure_drop": ts["pressure_drop"],
        "timestamps": ts["timestamps"],
    }


@app.get("/explain/leak/{pipeline_id}")
async def explain_leak(pipeline_id: str):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    detail = monitoring_service.get_pipeline_detail(pipeline_id)
    if "error" in detail:
        raise HTTPException(status_code=404, detail=detail["error"])

    stats = detail["statistics"]
    risk = detail["risk_assessment"]
    return {
        "pipeline_id": pipeline_id,
        "explanation": {
            "risk_score": risk["risk_score"],
            "severity": risk["severity"],
            "primary_factors": {
                "pressure_anomaly": round(abs(stats["avg_pressure"] - 1200) / 1200, 3),
                "acoustic_anomaly": round(stats["avg_acoustic"] / 80, 3),
                "structural_degradation": 0.3,
                "flow_imbalance": round(abs(stats["avg_flow"] - 2000) / 2000, 3),
            },
            "recommendations": risk["recommendations"],
        },
    }


@app.get("/dashboard/summary")
async def dashboard_summary():
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return monitoring_service.get_dashboard_summary()


@app.get("/alerts")
async def get_alerts(severity: str = None):
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return monitoring_service.get_alerts(severity)


@app.get("/network/view")
async def network_view():
    if monitoring_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return monitoring_service.get_network_view()
