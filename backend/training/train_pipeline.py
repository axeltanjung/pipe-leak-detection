import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import mlflow.pytorch
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, f1_score

from backend.anomaly.lstm_detector import LSTMAnomalyDetector
from backend.explainability.explainer import LeakExplainer


FEATURE_COLS = [
    "inlet_pressure", "outlet_pressure", "pressure_drop", "pressure_gradient",
    "pressure_variance", "flow_rate", "flow_velocity", "flow_turbulence_index",
    "volumetric_flow_loss", "acoustic_signal_amplitude", "acoustic_frequency",
    "acoustic_entropy", "vibration_frequency", "vibration_intensity",
    "temperature", "humidity", "soil_movement_index", "pump_load",
    "corrosion_index", "material_degradation_score", "joint_stress_level",
    "wall_thickness_estimate", "pipe_age",
]


def train_classification_model(data_path: str = "data/pipeline_sensor_data.csv"):
    print("Loading data...")
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["leak_detected"])

    X = df[FEATURE_COLS].fillna(0)
    y = df["leak_detected"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    mlflow.set_tracking_uri("mlruns")
    mlflow.set_experiment("pipeline-leak-detection")

    with mlflow.start_run(run_name="gradient_boosting_classifier"):
        print("Training Gradient Boosting Classifier...")
        model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, y_proba)
        f1 = f1_score(y_test, y_pred)

        mlflow.log_param("model_type", "GradientBoostingClassifier")
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("max_depth", 6)
        mlflow.log_param("learning_rate", 0.1)
        mlflow.log_metric("auc_roc", auc)
        mlflow.log_metric("f1_score", f1)

        print(f"AUC-ROC: {auc:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/leak_classifier.joblib")
        mlflow.sklearn.log_model(model, "leak_classifier")

        print("Training explainability model...")
        explainer = LeakExplainer()
        explainer.fit(X_train, y_train)
        explainer.save("models/leak_explainer.joblib")

        print("Models saved successfully!")

    return model


def train_lstm_anomaly_model(data_path: str = "data/pipeline_sensor_data.csv"):
    print("\nTraining LSTM Anomaly Detection Model...")
    df = pd.read_csv(data_path)

    normal_data = df[df["leak_detected"] == 0][FEATURE_COLS].fillna(0).values

    sample_size = min(50000, len(normal_data))
    normal_sample = normal_data[:sample_size]

    input_dim = len(FEATURE_COLS)
    detector = LSTMAnomalyDetector(
        input_dim=input_dim,
        sequence_length=50,
        hidden_dim=64,
        latent_dim=32,
    )

    mlflow.set_tracking_uri("mlruns")
    mlflow.set_experiment("pipeline-leak-detection")

    with mlflow.start_run(run_name="lstm_anomaly_detector"):
        history = detector.train(
            normal_sample,
            epochs=30,
            batch_size=64,
            learning_rate=0.001,
        )

        mlflow.log_param("model_type", "LSTM_Autoencoder")
        mlflow.log_param("sequence_length", 50)
        mlflow.log_param("hidden_dim", 64)
        mlflow.log_param("epochs", 30)
        mlflow.log_metric("final_train_loss", history["train_loss"][-1])
        mlflow.log_metric("final_val_loss", history["val_loss"][-1])
        mlflow.log_metric("anomaly_threshold", history["threshold"])

        os.makedirs("models", exist_ok=True)
        detector.save("models/lstm_anomaly_detector.pt")

        print(f"Final Train Loss: {history['train_loss'][-1]:.6f}")
        print(f"Final Val Loss: {history['val_loss'][-1]:.6f}")
        print(f"Anomaly Threshold: {history['threshold']:.6f}")
        print("LSTM model saved!")

    return detector


def main():
    from backend.training.synthetic_pipeline_leak_generator import PipelineLeakSimulator

    data_path = "data/pipeline_sensor_data.csv"
    if not Path(data_path).exists():
        print("Generating synthetic data...")
        simulator = PipelineLeakSimulator()
        dataset = simulator.generate_dataset(200000)
        os.makedirs("data", exist_ok=True)
        dataset.to_csv(data_path, index=False)

    train_classification_model(data_path)
    train_lstm_anomaly_model(data_path)
    print("\n=== Training Complete ===")


if __name__ == "__main__":
    main()
