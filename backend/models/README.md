# Alpha-Cure AI Models Directory

Place your trained model files here:

## Required Files

### cancer_model.h5
The trained Keras ANN model from your notebook training.

To save your trained model from the notebook:
```python
model.save('cancer_model.h5')
```

### model_artifacts.pkl
Serialized scikit-learn preprocessing artifacts:
```python
import pickle

artifacts = {
    'scaler': scaler,           # StandardScaler fitted on training data
    'rf_selector': selector,    # SelectFromModel (RandomForest-based)
    'rf_model': rf_model,       # RandomForestClassifier for prob augmentation
}

with open('model_artifacts.pkl', 'wb') as f:
    pickle.dump(artifacts, f)
```

## Without Model Files
Alpha-Cure will run in MOCK MODE — using heuristic-based predictions that simulate real
model behavior. This allows full UI/API testing without needing the trained model.

## Model Architecture (from notebook)
- Input: 9 features (after SMOTE + StandardScaler + RF selection)
- Hidden Layer 1: Dense(128, relu) + Dropout(0.3)
- Hidden Layer 2: Dense(64, relu) + Dropout(0.2)
- Hidden Layer 3: Dense(32, relu)
- Output: Dense(4, softmax) — 4 cancer classes
- Optimizer: Adam | Loss: Categorical Crossentropy
- Training Accuracy: 99.8%
