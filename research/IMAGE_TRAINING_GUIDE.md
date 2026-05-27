# Image Training Guide

This project does not currently include a labeled medical image dataset, so a real cancer image model cannot be trained from the repository alone.

## What I added

- `research/cancer_image_trainer.py`

This script trains an image classifier for visible lesion / cancer-photo style datasets and saves the deployable model to:

- `backend/models/skin_lesion_model.keras`
- `backend/models/skin_lesion_labels.json`

## Expected dataset formats

### Option 1: Explicit train / val / test folders

```text
your_dataset/
  train/
    benign/
    malignant/
    normal/
  val/
    benign/
    malignant/
    normal/
  test/
    benign/
    malignant/
    normal/
```

### Option 2: Flat class folders with auto-splitting

```text
your_dataset/
  benign/
  malignant/
  normal/
```

The script will split this into training, validation, and test sets automatically.

## Run locally

From the repo root:

```powershell
.venv\Scripts\python.exe research\cancer_image_trainer.py `
  --dataset-root "D:\path\to\your_dataset" `
  --output-dir "research_outputs_image" `
  --epochs 20 `
  --batch-size 16 `
  --pretrained imagenet `
  --fine-tune
```

## Notes

- This is appropriate only for cancers that can be screened from visible images, such as skin-lesion style datasets.
- It is not suitable for internal cancers unless you have the correct imaging modality and labels, such as histopathology, MRI, CT, mammography, or colposcopy data.
- If ImageNet weights are unavailable, the script falls back to random initialization.
- You should validate the dataset source, class balance, label quality, and clinical scope before using the resulting model.

## What I still need from you to truly train it

One of these:

1. A local dataset folder path already on this machine.
2. A zip of the dataset copied into the workspace.
3. Permission to download a dataset from Kaggle or another source.

Once you provide that, I can wire the trained model into the app prediction flow too.
