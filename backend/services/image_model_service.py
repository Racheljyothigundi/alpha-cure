"""services/image_model_service.py - multi-model image inference"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image


IMAGE_MODEL_CONFIGS = {
    "skin_lesion": {
        "title": "Skin Lesion Screening",
        "dataset": "DermaMNIST",
        "model_name": "MobileNetV2 (DermaMNIST)",
        "model_filename": "skin_lesion_model.keras",
        "labels_filename": "skin_lesion_labels.json",
        "input_hint": "Upload a close-up skin lesion photo in bright, even lighting.",
        "short_note": "Visible skin-lesion images only.",
        "default_note": (
            "This image model supports visible skin-lesion screening only."
        ),
        "risk_mapping": {
            "melanoma": "CRITICAL",
            "actinic keratoses and intraepithelial carcinoma": "HIGH",
            "basal cell carcinoma": "HIGH",
            "benign keratosis-like lesions": "MODERATE",
            "dermatofibroma": "LOW",
            "melanocytic nevi": "LOW",
            "vascular lesions": "LOW",
        },
        "suggestions": {
            "melanoma": [
                "Urgent dermatology or oncology review is recommended within 24-48 hours.",
                "Do not rely on the image result alone; biopsy or dermoscopy is needed for confirmation.",
                "Avoid delaying care if the lesion is changing in size, color, or shape.",
            ],
            "actinic keratoses and intraepithelial carcinoma": [
                "Book a dermatologist appointment soon for a closer skin examination.",
                "A specialist may recommend dermoscopy or biopsy to confirm the finding.",
                "Protect the area from sun exposure and document any visible changes.",
            ],
            "basal cell carcinoma": [
                "Arrange a dermatology visit for evaluation and treatment planning.",
                "Photograph the lesion weekly if it is changing while you wait for the appointment.",
                "Seek faster review if there is bleeding, ulceration, or rapid growth.",
            ],
            "benign keratosis-like lesions": [
                "This pattern is often lower urgency, but a clinician should review persistent lesions.",
                "Monitor for itching, bleeding, or rapid visual changes.",
                "Keep a dated photo log if the spot evolves over time.",
            ],
            "dermatofibroma": [
                "This image pattern is commonly lower risk, but examine it clinically if it is new or changing.",
                "Book a routine skin check if you are unsure how long the lesion has been present.",
                "Avoid repeated irritation or picking at the area.",
            ],
            "melanocytic nevi": [
                "The image resembles a mole pattern, but continue routine self-checks.",
                "Watch for asymmetry, border changes, color change, or growth.",
                "Schedule a skin exam if you have many moles or a family history of skin cancer.",
            ],
            "vascular lesions": [
                "This image resembles a vascular lesion, which is often lower urgency.",
                "Ask a clinician to review it if it bleeds easily or appears to enlarge quickly.",
                "Track any change in color, texture, or size.",
            ],
        },
    },
    "breast_ultrasound": {
        "title": "Breast Ultrasound Screening",
        "dataset": "BreastMNIST",
        "model_name": "MobileNetV2 (BreastMNIST)",
        "model_filename": "breast_ultrasound_model.keras",
        "labels_filename": "breast_ultrasound_labels.json",
        "input_hint": "Upload a breast ultrasound image or ultrasound crop, not a normal phone photo.",
        "short_note": "Breast ultrasound images only.",
        "default_note": (
            "This model supports breast ultrasound demo screening only."
        ),
        "risk_mapping": {
            "malignant": "CRITICAL",
            "normal, benign": "LOW",
        },
        "suggestions": {
            "malignant": [
                "This pattern is higher risk and should be reviewed urgently by a radiologist or breast specialist.",
                "Do not use the AI result as a diagnosis; ultrasound findings should be confirmed with formal imaging review and, when indicated, biopsy.",
                "Bring any prior ultrasound, mammogram, or breast MRI reports to your follow-up appointment.",
            ],
            "normal, benign": [
                "This pattern is lower risk, but a clinician should still interpret it with your symptoms and exam.",
                "If a lump is growing, painful, or persistent, schedule follow-up imaging even if this screen appears reassuring.",
                "Keep routine screening appointments based on your age and risk profile.",
            ],
        },
    },
    "colorectal_histology": {
        "title": "Colorectal Pathology Tile Screening",
        "dataset": "PathMNIST",
        "model_name": "MobileNetV2 (PathMNIST)",
        "model_filename": "colorectal_histology_model.keras",
        "labels_filename": "colorectal_histology_labels.json",
        "input_hint": "Upload a histopathology tile or microscope crop from colorectal tissue, not a phone photo.",
        "short_note": "Pathology tile images only.",
        "default_note": (
            "This model supports colorectal histopathology tile screening only."
        ),
        "risk_mapping": {
            "adipose": "LOW",
            "background": "MODERATE",
            "debris": "MODERATE",
            "lymphocytes": "LOW",
            "mucus": "LOW",
            "smooth muscle": "LOW",
            "normal colon mucosa": "LOW",
            "cancer-associated stroma": "HIGH",
            "colorectal adenocarcinoma epithelium": "CRITICAL",
        },
        "suggestions": {
            "adipose": [
                "This tile resembles adipose tissue and is not by itself a strong cancer signal.",
                "A pathologist should still review the complete slide set rather than a single crop.",
                "If this came from a biopsy workflow, interpret it only in the context of the official pathology report.",
            ],
            "background": [
                "The uploaded tile looks non-diagnostic or background-heavy.",
                "Try another pathology crop with clearer tissue structure if you are testing the demo.",
                "Clinical decisions should not be based on low-information tiles.",
            ],
            "debris": [
                "The image contains debris-like structure and may not be a reliable diagnostic tile.",
                "Retest with a cleaner pathology crop or a better-centered tissue region.",
                "A pathologist should review the full slide and patient history.",
            ],
            "lymphocytes": [
                "This tile resembles lymphocyte-rich tissue rather than clear tumor epithelium.",
                "Interpret immune-cell rich regions together with surrounding tissue architecture.",
                "Use the official pathology workflow for diagnosis and staging.",
            ],
            "mucus": [
                "This tile resembles mucus-rich tissue, which is not by itself a confirmed malignancy result.",
                "If concern remains, additional pathology regions should be reviewed.",
                "Do not use a single mucus-heavy crop to rule cancer in or out.",
            ],
            "smooth muscle": [
                "This tile resembles smooth muscle tissue and is lower risk by itself.",
                "Pathology interpretation should include adjacent tissue architecture and clinical context.",
                "Follow the official pathology review rather than a demo screen alone.",
            ],
            "normal colon mucosa": [
                "This tile resembles normal colon mucosa and is lower risk by itself.",
                "A full pathology assessment is still needed before ruling out disease elsewhere on the slide.",
                "Keep your scheduled gastroenterology or pathology follow-up if symptoms persist.",
            ],
            "cancer-associated stroma": [
                "This pattern can appear near colorectal tumor tissue and deserves specialist review.",
                "Ask for the formal pathology interpretation and staging details from the treating team.",
                "Do not delay care if this image came from an active cancer workup.",
            ],
            "colorectal adenocarcinoma epithelium": [
                "This tile pattern is high concern for colorectal tumor epithelium and needs urgent pathology-led review.",
                "Formal diagnosis requires full-slide interpretation and the clinical pathology workflow.",
                "Discuss next-step staging and treatment planning promptly with your care team.",
            ],
        },
    },
}

_MODEL_CACHE = {}
_METADATA_CACHE = {}


def _models_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "models"


def _get_model_config(model_key: str) -> dict:
    if model_key not in IMAGE_MODEL_CONFIGS:
        raise KeyError(f"Unknown image screening model '{model_key}'.")
    return IMAGE_MODEL_CONFIGS[model_key]


def _model_path(model_key: str) -> Path:
    config = _get_model_config(model_key)
    return _models_dir() / config["model_filename"]


def _labels_path(model_key: str) -> Path:
    config = _get_model_config(model_key)
    return _models_dir() / config["labels_filename"]


def _format_label(label: str) -> str:
    words = label.replace("_", " ").split()
    return " ".join(
        word.upper() if word in {"I/II", "III/IV"} else word.capitalize()
        for word in words
    )


def load_image_model(model_key: str, force: bool = False):
    """Load one trained image model and its metadata."""
    if model_key in _MODEL_CACHE and model_key in _METADATA_CACHE and not force:
        return _MODEL_CACHE[model_key], _METADATA_CACHE[model_key]

    model_path = _model_path(model_key)
    labels_path = _labels_path(model_key)

    if not model_path.exists():
        raise FileNotFoundError(f"Image model not found at {model_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Image labels not found at {labels_path}")

    with open(labels_path, "r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    model = tf.keras.models.load_model(model_path, compile=False)
    _MODEL_CACHE[model_key] = model
    _METADATA_CACHE[model_key] = metadata
    print(f"[ImageModel] Loaded {model_key} from {model_path}")
    return model, metadata


def preload_image_models() -> list[str]:
    """Try loading all available image models and return the loaded keys."""
    loaded = []
    for model_key in IMAGE_MODEL_CONFIGS:
        try:
            load_image_model(model_key)
            loaded.append(model_key)
        except Exception as exc:
            print(f"[ImageModel] WARNING: {model_key}: {exc}")
    return loaded


def _risk_level_for_class(model_key: str, class_name: str) -> str:
    config = _get_model_config(model_key)
    return config["risk_mapping"].get(class_name.lower(), "MODERATE")


def _suggestions_for_class(model_key: str, class_name: str, confidence: float) -> list[str]:
    config = _get_model_config(model_key)
    low_confidence = confidence < 0.65
    base = config["suggestions"].get(
        class_name.lower(),
        [
            "A specialist should review the image result together with your symptoms, scan, or pathology context.",
            "Repeat the upload with a clearer, well-centered image if the sample was blurry or cropped poorly.",
            "This AI output is a screening demo and should not replace clinical diagnosis.",
        ],
    ).copy()

    if low_confidence:
        base.append(
            "This prediction had lower confidence, so a clearer image or specialist review is especially important."
        )

    base.append(config["default_note"])
    return base


def list_image_screening_models() -> list[dict]:
    """Return frontend-safe metadata for all supported image models."""
    models = []
    for model_key, config in IMAGE_MODEL_CONFIGS.items():
        labels_path = _labels_path(model_key)
        metadata = None
        if model_key in _METADATA_CACHE:
            metadata = _METADATA_CACHE[model_key]
        elif labels_path.exists():
            try:
                with open(labels_path, "r", encoding="utf-8") as handle:
                    metadata = json.load(handle)
            except Exception:
                metadata = None

        models.append(
            {
                "key": model_key,
                "title": config["title"],
                "dataset": config["dataset"],
                "model_name": config["model_name"],
                "input_hint": config["input_hint"],
                "short_note": config["short_note"],
                "note": (metadata or {}).get("note", config["default_note"]),
                "class_count": len((metadata or {}).get("class_names", [])),
                "available": _model_path(model_key).exists() and labels_path.exists(),
            }
        )
    return models


def predict_uploaded_image(image_bytes: bytes, model_key: str, filename: str | None = None) -> dict:
    """Run image inference on an uploaded image for a specific screening model."""
    model, metadata = load_image_model(model_key)
    config = _get_model_config(model_key)
    image_size = int(metadata.get("image_size", 64))
    class_names = metadata.get("class_names", [])

    if not class_names:
        raise ValueError(f"Class names are missing for image model '{model_key}'.")

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = image.resize((image_size, image_size))
    array = np.asarray(image, dtype="float32") / 255.0
    batch = np.expand_dims(array, axis=0)

    probabilities = model.predict(batch, verbose=0)[0]
    predicted_index = int(np.argmax(probabilities))
    class_name = class_names[predicted_index]
    confidence = float(probabilities[predicted_index])
    risk_level = _risk_level_for_class(model_key, class_name)

    probability_map = {
        _format_label(label): round(float(prob), 4)
        for label, prob in sorted(
            zip(class_names, probabilities),
            key=lambda item: item[1],
            reverse=True,
        )
    }

    return {
        "success": True,
        "analysis_type": "image",
        "model_key": model_key,
        "model_name": config["model_name"],
        "screening_title": config["title"],
        "prediction": predicted_index,
        "label": _format_label(class_name),
        "code": class_name.upper().replace(" ", "_").replace("-", "_").replace(",", ""),
        "confidence": round(confidence * 100, 2),
        "probabilities": probability_map,
        "risk_level": risk_level,
        "suggestions": _suggestions_for_class(model_key, class_name, confidence),
        "note": metadata.get("note", config["default_note"]),
        "filename": filename or "uploaded-image",
        "input_hint": config["input_hint"],
        "dataset": config["dataset"],
    }
