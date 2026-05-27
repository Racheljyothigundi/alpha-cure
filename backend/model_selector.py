"""
model_selector.py
Alpha-Cure AI Cancer Detection Model
Based on: ANN trained on tabular cancer dataset (9 features, multi-class)
Pipeline: SMOTE → StandardScaler → RandomForest selector → RF prob augment → ANN
"""

import os
import pickle
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel

# ─── Global model objects (loaded once) ────────────────────────────────────────
_ann_model = None
_scaler = None
_rf_selector = None
_rf_model = None
_num_classes = 4

# Cancer type labels matching the dataset
CANCER_LABELS = {
    0: "Normal (No Cancer Detected)",
    1: "Benign Tumor",
    2: "Malignant - Stage I/II",
    3: "Malignant - Stage III/IV",
}

CANCER_CODES = {
    0: "NORMAL",
    1: "BENIGN",
    2: "MALIGNANT_EARLY",
    3: "MALIGNANT_ADVANCED",
}


def get_model_path():
    """Returns the path to the saved .h5 model."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "models", "cancer_model.h5")


def get_artifacts_path():
    """Returns the path to saved sklearn artifacts."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "models", "model_artifacts.pkl")


def load_model():
    """Load model and preprocessing artifacts. Called once at startup."""
    global _ann_model, _scaler, _rf_selector, _rf_model

    model_path = get_model_path()
    artifacts_path = get_artifacts_path()

    if os.path.exists(model_path):
        _ann_model = tf.keras.models.load_model(model_path)
        print(f"[ModelSelector] ANN model loaded from {model_path}")
    else:
        print(f"[ModelSelector] WARNING: Model file not found at {model_path}. Using mock predictor.")
        _ann_model = None

    if os.path.exists(artifacts_path):
        with open(artifacts_path, "rb") as f:
            artifacts = pickle.load(f)
        _scaler = artifacts.get("scaler")
        _rf_selector = artifacts.get("rf_selector")
        _rf_model = artifacts.get("rf_model")
        print("[ModelSelector] Sklearn artifacts loaded.")
    else:
        print("[ModelSelector] WARNING: Artifacts not found. Using mock prediction pipeline.")
        _scaler = None
        _rf_selector = None
        _rf_model = None


def preprocess_features(features: dict) -> np.ndarray:
    """
    Preprocess raw input features through the same pipeline as training:
    1. Convert to numpy array
    2. StandardScaler transform
    3. RF feature selection
    4. RF probability augmentation
    Returns final feature array ready for ANN.
    """
    # Expected feature keys (from dataset with 18 cols, 9 selected)
    feature_keys = [
        "age", "gender", "bmi", "smoking", "genetic_risk",
        "physical_activity", "alcohol_intake", "cancer_history", "diagnosis"
    ]

    raw = np.array([[features.get(k, 0) for k in feature_keys]], dtype=float)

    if _scaler is None or _rf_selector is None or _rf_model is None:
        # Mock pipeline for development without saved artifacts
        return raw

    X_scaled = _scaler.transform(raw)
    X_selected = _rf_selector.transform(X_scaled)
    probs = _rf_model.predict_proba(X_selected)
    X_final = np.hstack((X_selected, probs))
    return X_final


def predict(features: dict) -> dict:
    """
    Main prediction function.
    Args:
        features: dict with patient clinical features
    Returns:
        dict with prediction, confidence, class_label, suggestions
    """
    try:
        X = preprocess_features(features)

        if _ann_model is not None:
            probs = _ann_model.predict(X, verbose=0)[0]
            pred_class = int(np.argmax(probs))
            confidence = float(np.max(probs))
        else:
            # Mock prediction for dev/demo mode
            pred_class, confidence, probs = _mock_predict(features)

        label = CANCER_LABELS.get(pred_class, "Unknown")
        code = CANCER_CODES.get(pred_class, "UNKNOWN")

        all_probs = {
            CANCER_LABELS[i]: round(float(p), 4)
            for i, p in enumerate(probs)
        } if len(probs) == _num_classes else {}

        return {
            "success": True,
            "prediction": pred_class,
            "label": label,
            "code": code,
            "confidence": round(confidence * 100, 2),
            "probabilities": all_probs,
            "risk_level": _get_risk_level(pred_class, confidence),
            "suggestions": _get_suggestions(pred_class, confidence, features),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prediction": -1,
            "label": "Error in prediction",
            "confidence": 0,
        }


def _mock_predict(features: dict):
    """
    Deterministic mock predictor for development (no model file needed).
    Uses clinical heuristics to simulate realistic predictions.
    """
    risk_score = 0
    risk_score += features.get("smoking", 0) * 2
    risk_score += features.get("genetic_risk", 0) * 3
    risk_score += features.get("cancer_history", 0) * 4
    risk_score += max(0, (features.get("age", 40) - 40) / 10)
    risk_score += features.get("alcohol_intake", 0) * 1.5
    risk_score -= features.get("physical_activity", 3) * 0.5

    if risk_score < 2:
        pred_class = 0
        probs = np.array([0.85, 0.10, 0.04, 0.01])
    elif risk_score < 5:
        pred_class = 1
        probs = np.array([0.10, 0.75, 0.12, 0.03])
    elif risk_score < 8:
        pred_class = 2
        probs = np.array([0.05, 0.10, 0.78, 0.07])
    else:
        pred_class = 3
        probs = np.array([0.02, 0.05, 0.13, 0.80])

    confidence = float(probs[pred_class])
    return pred_class, confidence, probs


def _get_risk_level(pred_class: int, confidence: float) -> str:
    if pred_class == 0:
        return "LOW"
    elif pred_class == 1:
        return "MODERATE"
    elif pred_class == 2:
        return "HIGH"
    else:
        return "CRITICAL"


def _get_suggestions(pred_class: int, confidence: float, features: dict) -> list:
    suggestions = []

    if pred_class == 0:
        suggestions = [
            "Continue with regular health check-ups every 6–12 months.",
            "Maintain a balanced diet rich in antioxidants and fiber.",
            "Stay physically active with at least 150 minutes of exercise per week.",
            "Avoid tobacco and limit alcohol consumption.",
            "Perform self-examinations monthly and report any unusual changes.",
        ]
    elif pred_class == 1:
        suggestions = [
            "Schedule a follow-up with an oncologist within 2 weeks.",
            "Request a biopsy or advanced imaging (MRI/CT scan) for confirmation.",
            "Do not panic — benign tumors are non-cancerous but require monitoring.",
            "Track any changes in size, pain, or associated symptoms.",
            "Consider genetic counseling if family history is positive.",
        ]
    elif pred_class == 2:
        suggestions = [
            "⚠️ Urgent: Consult an oncologist immediately — within 48–72 hours.",
            "A comprehensive staging workup (PET scan, biopsy) is recommended.",
            "Discuss treatment options: surgery, radiation, chemotherapy, or immunotherapy.",
            "Seek a second opinion from a cancer specialist.",
            "Inform family members for emotional and logistical support.",
            "Consider joining a cancer support group.",
        ]
    else:
        suggestions = [
            "🚨 CRITICAL: Immediate oncology consultation is required today.",
            "Emergency referral to a multi-disciplinary cancer team.",
            "Discuss palliative care options alongside curative treatment.",
            "Advanced staging requires urgent PET/CT and bone scan.",
            "Explore clinical trials that may be available for your cancer type.",
            "Legal and financial planning support is advisable at this stage.",
        ]

    # Add personalized tips
    if features.get("smoking", 0):
        suggestions.append("Quitting smoking immediately can significantly improve treatment outcomes.")
    if features.get("alcohol_intake", 0) > 2:
        suggestions.append("Reducing alcohol intake to below 1 unit/day is strongly recommended.")
    if features.get("physical_activity", 3) < 2:
        suggestions.append("Increasing physical activity supports immune function and reduces cancer risk.")

    return suggestions
