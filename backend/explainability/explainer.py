import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import shap
from sklearn.ensemble import GradientBoostingClassifier
import joblib


class LeakExplainer:
    def __init__(self):
        self.model = None
        self.explainer = None
        self.feature_names = None

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        self.feature_names = list(X.columns)
        self.model = GradientBoostingClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
        )
        X_clean = X.fillna(0)
        self.model.fit(X_clean, y)
        self.explainer = shap.TreeExplainer(self.model)

    def explain_prediction(self, features: pd.DataFrame) -> Dict:
        features_clean = features.fillna(0)
        shap_values = self.explainer.shap_values(features_clean)

        if isinstance(shap_values, list):
            shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_vals = shap_values

        if len(shap_vals.shape) > 1:
            shap_vals = shap_vals[0]

        feature_importance = {}
        for i, name in enumerate(self.feature_names):
            feature_importance[name] = float(shap_vals[i])

        sorted_features = sorted(
            feature_importance.items(), key=lambda x: abs(x[1]), reverse=True
        )

        top_contributors = sorted_features[:10]
        positive_factors = [(k, v) for k, v in sorted_features if v > 0][:5]
        negative_factors = [(k, v) for k, v in sorted_features if v < 0][:5]

        prediction = self.model.predict_proba(features_clean)[0]

        return {
            "prediction": float(prediction[1]) if len(prediction) > 1 else float(prediction[0]),
            "base_value": float(self.explainer.expected_value[1])
            if isinstance(self.explainer.expected_value, (list, np.ndarray))
            else float(self.explainer.expected_value),
            "feature_contributions": dict(top_contributors),
            "risk_increasing_factors": [
                {"feature": k, "contribution": v} for k, v in positive_factors
            ],
            "risk_decreasing_factors": [
                {"feature": k, "contribution": v} for k, v in negative_factors
            ],
            "all_shap_values": feature_importance,
        }

    def get_global_importance(self, X: pd.DataFrame) -> Dict[str, float]:
        X_clean = X.fillna(0).head(500)
        shap_values = self.explainer.shap_values(X_clean)

        if isinstance(shap_values, list):
            shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_vals = shap_values

        importance = np.abs(shap_vals).mean(axis=0)
        result = {}
        for i, name in enumerate(self.feature_names):
            result[name] = float(importance[i])

        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def explain_segment(
        self, segment_features: pd.DataFrame, pipeline_id: str
    ) -> Dict:
        explanations = []
        segment_clean = segment_features.fillna(0)
        shap_values = self.explainer.shap_values(segment_clean)

        if isinstance(shap_values, list):
            shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_vals = shap_values

        avg_shap = np.mean(np.abs(shap_vals), axis=0)
        top_features = sorted(
            zip(self.feature_names, avg_shap), key=lambda x: x[1], reverse=True
        )[:5]

        predictions = self.model.predict_proba(segment_clean)[:, 1]

        return {
            "pipeline_id": pipeline_id,
            "average_leak_probability": float(np.mean(predictions)),
            "max_leak_probability": float(np.max(predictions)),
            "top_contributing_features": [
                {"feature": k, "importance": float(v)} for k, v in top_features
            ],
            "risk_trend": "increasing" if predictions[-1] > predictions[0] else "stable",
        }

    def save(self, model_path: str):
        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names,
        }, model_path)

    def load(self, model_path: str):
        data = joblib.load(model_path)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        self.explainer = shap.TreeExplainer(self.model)
