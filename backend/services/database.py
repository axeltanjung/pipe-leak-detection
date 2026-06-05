from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./pipeline_monitor.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PipelineSegment(Base):
    __tablename__ = "pipeline_segments"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String, index=True)
    name = Column(String)
    length_km = Column(Float)
    diameter_inches = Column(Float)
    material = Column(String)
    age_years = Column(Float)
    max_operating_pressure = Column(Float)
    status = Column(String, default="active")
    last_inspection = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    inlet_pressure = Column(Float)
    outlet_pressure = Column(Float)
    pressure_drop = Column(Float)
    flow_rate = Column(Float)
    acoustic_signal_amplitude = Column(Float)
    acoustic_frequency = Column(Float)
    vibration_intensity = Column(Float)
    temperature = Column(Float)
    leak_detected = Column(Boolean, default=False)


class LeakAlert(Base):
    __tablename__ = "leak_alerts"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(String)
    leak_risk_score = Column(Float)
    pipeline_health_score = Column(Float)
    description = Column(Text)
    status = Column(String, default="active")
    recommendations = Column(Text)


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String)
    leak_probability = Column(Float)
    anomaly_score = Column(Float)
    risk_score = Column(Float)
    severity = Column(String)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
