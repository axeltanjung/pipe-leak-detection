import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, List, Optional
import os

class PipelineLeakSimulator:
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.pipeline_configs = self._generate_pipeline_configs()

    def _generate_pipeline_configs(self) -> List[dict]:
        configs = []
        for i in range(20):
            configs.append({
                "pipeline_id": f"PL-{i+1:03d}",
                "length_km": np.random.uniform(5, 150),
                "diameter_inches": np.random.choice([6, 8, 12, 16, 24, 36]),
                "material": np.random.choice(["carbon_steel", "stainless_steel", "composite"]),
                "age_years": np.random.uniform(2, 45),
                "max_operating_pressure": np.random.uniform(500, 2000),
                "nominal_flow_rate": np.random.uniform(100, 5000),
            })
        return configs

    def _simulate_normal(self, config: dict, n_samples: int) -> pd.DataFrame:
        mop = config["max_operating_pressure"]
        nfr = config["nominal_flow_rate"]

        inlet_pressure = np.random.normal(mop * 0.85, mop * 0.02, n_samples)
        outlet_pressure = inlet_pressure - np.random.normal(mop * 0.05, mop * 0.005, n_samples)
        pressure_drop = inlet_pressure - outlet_pressure
        pressure_gradient = pressure_drop / config["length_km"]
        pressure_variance = np.abs(np.random.normal(0, mop * 0.005, n_samples))

        flow_rate = np.random.normal(nfr, nfr * 0.03, n_samples)
        flow_velocity = flow_rate / (np.pi * (config["diameter_inches"] * 0.0254 / 2) ** 2)
        flow_turbulence = np.random.uniform(0.01, 0.1, n_samples)
        volumetric_flow_loss = np.random.normal(0.5, 0.2, n_samples)

        acoustic_amplitude = np.random.normal(20, 3, n_samples)
        acoustic_frequency = np.random.normal(50, 5, n_samples)
        acoustic_entropy = np.random.uniform(0.1, 0.3, n_samples)
        vibration_frequency = np.random.normal(30, 4, n_samples)
        vibration_intensity = np.random.normal(5, 1, n_samples)

        temperature = np.random.normal(35, 5, n_samples)
        humidity = np.random.uniform(30, 80, n_samples)
        soil_movement = np.random.uniform(0, 0.05, n_samples)
        pump_load = np.random.normal(70, 5, n_samples)
        compressor_status = np.ones(n_samples)

        corrosion_index = np.random.uniform(0.01, 0.15, n_samples)
        material_degradation = np.random.uniform(0.05, 0.2, n_samples)
        joint_stress = np.random.uniform(0.1, 0.3, n_samples)
        wall_thickness = np.random.normal(0.95, 0.02, n_samples)

        return pd.DataFrame({
            "inlet_pressure": inlet_pressure,
            "outlet_pressure": outlet_pressure,
            "pressure_drop": pressure_drop,
            "pressure_gradient": pressure_gradient,
            "pressure_variance": pressure_variance,
            "flow_rate": flow_rate,
            "flow_velocity": flow_velocity,
            "flow_turbulence_index": flow_turbulence,
            "volumetric_flow_loss": volumetric_flow_loss,
            "acoustic_signal_amplitude": acoustic_amplitude,
            "acoustic_frequency": acoustic_frequency,
            "acoustic_entropy": acoustic_entropy,
            "vibration_frequency": vibration_frequency,
            "vibration_intensity": vibration_intensity,
            "temperature": temperature,
            "humidity": humidity,
            "soil_movement_index": soil_movement,
            "pump_load": pump_load,
            "compressor_status": compressor_status,
            "corrosion_index": corrosion_index,
            "material_degradation_score": material_degradation,
            "joint_stress_level": joint_stress,
            "wall_thickness_estimate": wall_thickness,
        })

    def _simulate_early_leak(self, config: dict, n_samples: int) -> pd.DataFrame:
        df = self._simulate_normal(config, n_samples)
        progress = np.linspace(0, 1, n_samples)

        df["inlet_pressure"] -= progress * config["max_operating_pressure"] * 0.03
        df["pressure_drop"] += progress * config["max_operating_pressure"] * 0.02
        df["pressure_variance"] += progress * config["max_operating_pressure"] * 0.01
        df["flow_rate"] -= progress * config["nominal_flow_rate"] * 0.02
        df["volumetric_flow_loss"] += progress * 2
        df["acoustic_signal_amplitude"] += progress * 8
        df["acoustic_entropy"] += progress * 0.15
        df["vibration_intensity"] += progress * 2

        return df

    def _simulate_developing_leak(self, config: dict, n_samples: int) -> pd.DataFrame:
        df = self._simulate_normal(config, n_samples)
        progress = np.linspace(0, 1, n_samples)

        df["inlet_pressure"] -= progress * config["max_operating_pressure"] * 0.08
        df["outlet_pressure"] -= progress * config["max_operating_pressure"] * 0.12
        df["pressure_drop"] += progress * config["max_operating_pressure"] * 0.06
        df["pressure_gradient"] += progress * 0.5
        df["pressure_variance"] += progress * config["max_operating_pressure"] * 0.03
        df["flow_rate"] -= progress * config["nominal_flow_rate"] * 0.08
        df["flow_turbulence_index"] += progress * 0.4
        df["volumetric_flow_loss"] += progress * 8
        df["acoustic_signal_amplitude"] += progress * 25
        df["acoustic_frequency"] += progress * 30
        df["acoustic_entropy"] += progress * 0.4
        df["vibration_frequency"] += progress * 15
        df["vibration_intensity"] += progress * 8
        df["corrosion_index"] += progress * 0.2
        df["material_degradation_score"] += progress * 0.3
        df["joint_stress_level"] += progress * 0.3

        return df

    def _simulate_critical_failure(self, config: dict, n_samples: int) -> pd.DataFrame:
        df = self._simulate_normal(config, n_samples)
        progress = np.linspace(0, 1, n_samples)

        rupture_point = int(n_samples * 0.6)
        pre_rupture = np.linspace(0, 0.5, rupture_point)
        post_rupture = np.linspace(0.5, 1, n_samples - rupture_point)
        severity = np.concatenate([pre_rupture, post_rupture ** 2 + 0.5])

        df["inlet_pressure"] -= severity * config["max_operating_pressure"] * 0.4
        df["outlet_pressure"] -= severity * config["max_operating_pressure"] * 0.5
        df["pressure_drop"] = np.abs(df["inlet_pressure"] - df["outlet_pressure"])
        df["pressure_variance"] += severity * config["max_operating_pressure"] * 0.1
        df["flow_rate"] -= severity * config["nominal_flow_rate"] * 0.4
        df["flow_turbulence_index"] += severity * 0.8
        df["volumetric_flow_loss"] += severity * 30
        df["acoustic_signal_amplitude"] += severity * 60
        df["acoustic_frequency"] += severity * 80
        df["acoustic_entropy"] += severity * 0.7
        df["vibration_frequency"] += severity * 40
        df["vibration_intensity"] += severity * 25
        df["joint_stress_level"] += severity * 0.6
        df["wall_thickness_estimate"] -= severity * 0.3
        df["corrosion_index"] += severity * 0.5

        return df

    def _add_noise_and_artifacts(self, df: pd.DataFrame) -> pd.DataFrame:
        n = len(df)
        for col in df.columns:
            if df[col].dtype in [np.float64, np.float32]:
                noise = np.random.normal(0, df[col].std() * 0.02, n)
                df[col] += noise

        missing_mask = np.random.random(df.shape) < 0.005
        for i, col in enumerate(df.columns):
            if df[col].dtype in [np.float64, np.float32]:
                df.loc[missing_mask[:, i], col] = np.nan

        n_outliers = int(n * 0.002)
        for col in df.select_dtypes(include=[np.float64, np.float32]).columns:
            outlier_idx = np.random.choice(n, n_outliers, replace=False)
            df.loc[outlier_idx, col] *= np.random.choice([1.5, 2.0, 0.5, 0.3], n_outliers)

        return df

    def _compute_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        pressure_cols = ["pressure_drop", "pressure_variance", "pressure_gradient"]
        df["pressure_anomaly_score"] = df[pressure_cols].apply(
            lambda x: (x - x.mean()) / (x.std() + 1e-8)
        ).mean(axis=1).clip(0, 1)

        acoustic_cols = ["acoustic_signal_amplitude", "acoustic_entropy", "vibration_intensity"]
        df["acoustic_anomaly_score"] = df[acoustic_cols].apply(
            lambda x: (x - x.mean()) / (x.std() + 1e-8)
        ).mean(axis=1).clip(0, 1)

        df["structural_risk_index"] = (
            df["corrosion_index"] * 0.3 +
            df["material_degradation_score"] * 0.3 +
            df["joint_stress_level"] * 0.2 +
            (1 - df["wall_thickness_estimate"].clip(0, 1)) * 0.2
        ).clip(0, 1)

        df["flow_imbalance_score"] = (
            df["volumetric_flow_loss"] / (df["flow_rate"].abs() + 1e-8)
        ).clip(0, 1)

        df["leak_probability_indicator"] = (
            df["pressure_anomaly_score"] * 0.3 +
            df["acoustic_anomaly_score"] * 0.3 +
            df["structural_risk_index"] * 0.2 +
            df["flow_imbalance_score"] * 0.2
        ).clip(0, 1)

        return df

    def generate_dataset(self, total_samples: int = 200000) -> pd.DataFrame:
        normal_ratio = 0.60
        early_ratio = 0.15
        developing_ratio = 0.15
        critical_ratio = 0.10

        all_data = []
        samples_per_pipeline = total_samples // len(self.pipeline_configs)

        for config in self.pipeline_configs:
            n_normal = int(samples_per_pipeline * normal_ratio)
            n_early = int(samples_per_pipeline * early_ratio)
            n_developing = int(samples_per_pipeline * developing_ratio)
            n_critical = samples_per_pipeline - n_normal - n_early - n_developing

            normal_df = self._simulate_normal(config, n_normal)
            normal_df["leak_detected"] = 0
            normal_df["leak_severity"] = "NONE"
            normal_df["leak_probability"] = np.random.uniform(0, 0.1, n_normal)

            early_df = self._simulate_early_leak(config, n_early)
            early_df["leak_detected"] = 0
            early_df["leak_severity"] = "LOW"
            early_df["leak_probability"] = np.linspace(0.1, 0.35, n_early)

            developing_df = self._simulate_developing_leak(config, n_developing)
            developing_df["leak_detected"] = 1
            developing_df["leak_severity"] = "MEDIUM"
            developing_df["leak_probability"] = np.linspace(0.35, 0.7, n_developing)

            critical_df = self._simulate_critical_failure(config, n_critical)
            critical_df["leak_detected"] = 1
            critical_df["leak_severity"] = np.where(
                np.linspace(0, 1, n_critical) > 0.5, "CRITICAL", "HIGH"
            )
            critical_df["leak_probability"] = np.linspace(0.7, 0.99, n_critical)

            for df in [normal_df, early_df, developing_df, critical_df]:
                df["pipeline_id"] = config["pipeline_id"]
                df["pipe_age"] = config["age_years"]

            pipeline_data = pd.concat([normal_df, early_df, developing_df, critical_df], ignore_index=True)
            all_data.append(pipeline_data)

        dataset = pd.concat(all_data, ignore_index=True)

        start_time = datetime(2023, 1, 1)
        timestamps = [start_time + timedelta(minutes=i * 5) for i in range(len(dataset))]
        dataset.insert(0, "timestamp", timestamps[:len(dataset)])

        dataset = self._add_noise_and_artifacts(dataset)
        dataset = self._compute_derived_features(dataset)

        dataset["pipeline_health_score"] = (
            (1 - dataset["leak_probability_indicator"]) * 100
        ).clip(0, 100)

        dataset["time_to_failure_estimate"] = np.where(
            dataset["leak_detected"] == 1,
            np.random.exponential(48, len(dataset)),
            np.random.exponential(2000, len(dataset))
        )

        dataset = dataset.sample(frac=1, random_state=42).reset_index(drop=True)

        return dataset


def main():
    print("Generating synthetic pipeline leak dataset...")
    simulator = PipelineLeakSimulator(seed=42)
    dataset = simulator.generate_dataset(total_samples=200000)

    os.makedirs("data", exist_ok=True)
    dataset.to_csv("data/pipeline_sensor_data.csv", index=False)

    print(f"Dataset shape: {dataset.shape}")
    print(f"Columns: {list(dataset.columns)}")
    print(f"\nLeak distribution:")
    print(dataset["leak_detected"].value_counts())
    print(f"\nSeverity distribution:")
    print(dataset["leak_severity"].value_counts())
    print(f"\nDataset saved to data/pipeline_sensor_data.csv")


if __name__ == "__main__":
    main()
