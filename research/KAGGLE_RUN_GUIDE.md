Use this script in Kaggle after uploading your Excel dataset.

Kaggle steps:
1. Create a new notebook.
2. Upload `synthetic_multiclass_cancer_dataset_v2(1) (1).xlsx` as a Kaggle dataset or notebook input.
3. Upload or paste [`research/cervical_cancer_deep_models.py`](D:/rachel%20jyothi/Documents/alpha-cure/research/cervical_cancer_deep_models.py) into the notebook working area.
4. Run:

```python
!python /kaggle/working/cervical_cancer_deep_models.py \
  --excel-path "/kaggle/input/your-dataset-name/synthetic_multiclass_cancer_dataset_v2(1) (1).xlsx" \
  --output-dir "/kaggle/working/research_outputs" \
  --epochs 80 \
  --batch-size 128
```

Models included:
- `baseline_mlp`: simple dense neural network baseline.
- `deep_regularized_mlp`: deeper dense network with batch normalization, dropout, and L2 regularization.
- `residual_mlp`: skip-connection MLP that often works well on tabular medical data.
- `feature_cnn`: 1D CNN over the ordered feature vector.

Files generated:
- `model_comparison.json`: metrics for all models.
- `dataset_metadata.json`: class names and feature list.
- `preprocessing.pkl`: scaler and label encoder.
- `*.keras`: saved best checkpoint for each model.

For your paper, report at least:
- Accuracy
- Macro F1-score
- Weighted F1-score
- Precision
- Recall
- Confusion matrix

Because your dataset is synthetic and perfectly balanced, weighted F1 and macro F1 are both appropriate summary metrics.
