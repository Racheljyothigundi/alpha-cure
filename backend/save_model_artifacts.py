"""
save_model_artifacts.py
───────────────────────
Run this script at the END of your Colab/Jupyter notebook after training
to export everything Alpha-Cure's backend needs.

Usage (in your notebook, after training):
    exec(open('save_model_artifacts.py').read())

Or add these cells at the end of your notebook directly.
"""

import pickle
import os

OUTPUT_DIR = './models'
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── 1. Save the Keras ANN model ───────────────────────────────────────────────
print("Saving Keras model...")
model.save(os.path.join(OUTPUT_DIR, 'cancer_model.h5'))
print(f"  ✓ Saved: {OUTPUT_DIR}/cancer_model.h5")


# ─── 2. Save sklearn preprocessing pipeline ────────────────────────────────────
print("Saving sklearn artifacts...")

# These variables must exist in your notebook's scope:
#   scaler        — StandardScaler fitted on X_train
#   selector      — SelectFromModel fitted on X_train
#   rf_model      — RandomForestClassifier used for probability augmentation

artifacts = {
    'scaler': scaler,
    'rf_selector': selector,
    'rf_model': rf_model,
}

with open(os.path.join(OUTPUT_DIR, 'model_artifacts.pkl'), 'wb') as f:
    pickle.dump(artifacts, f)

print(f"  ✓ Saved: {OUTPUT_DIR}/model_artifacts.pkl")


# ─── 3. Save label mapping ─────────────────────────────────────────────────────
print("Saving label info...")

label_info = {
    'num_classes': num_classes,
    'class_labels': {
        0: 'Normal (No Cancer Detected)',
        1: 'Benign Tumor',
        2: 'Malignant - Stage I/II',
        3: 'Malignant - Stage III/IV',
    }
}

with open(os.path.join(OUTPUT_DIR, 'label_info.pkl'), 'wb') as f:
    pickle.dump(label_info, f)

print(f"  ✓ Saved: {OUTPUT_DIR}/label_info.pkl")


# ─── 4. Quick verification ─────────────────────────────────────────────────────
print("\n── Verification ──────────────────────────────────────────────────────────")

import numpy as np

# Load and test
loaded_model = __import__('tensorflow').keras.models.load_model(
    os.path.join(OUTPUT_DIR, 'cancer_model.h5')
)
with open(os.path.join(OUTPUT_DIR, 'model_artifacts.pkl'), 'rb') as f:
    loaded_artifacts = pickle.load(f)

# Test with a dummy sample
test_sample = X_test_final[:1]
pred = loaded_model.predict(test_sample, verbose=0)
print(f"  Model input shape : {loaded_model.input_shape}")
print(f"  Model output shape: {loaded_model.output_shape}")
print(f"  Test prediction   : {pred[0].round(4)}")
print(f"  Predicted class   : {np.argmax(pred[0])}")
print(f"  Confidence        : {np.max(pred[0])*100:.1f}%")
print("\n✅ All artifacts saved and verified!")
print(f"\nCopy these files to your Alpha-Cure backend:")
print(f"  {OUTPUT_DIR}/cancer_model.h5      → alpha-cure/backend/models/")
print(f"  {OUTPUT_DIR}/model_artifacts.pkl  → alpha-cure/backend/models/")
print(f"  {OUTPUT_DIR}/label_info.pkl       → alpha-cure/backend/models/")
