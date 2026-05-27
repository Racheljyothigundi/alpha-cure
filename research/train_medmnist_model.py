import argparse
import json
import random
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight


SEED = 42

DATASET_CONFIGS = {
    "dermamnist": {
        "python_class": "DermaMNIST",
        "image_size": 64,
        "deploy_model": "skin_lesion_model.keras",
        "deploy_labels": "skin_lesion_labels.json",
        "model_name": "MobileNetV2 (DermaMNIST)",
        "note": (
            "DermaMNIST is a skin-lesion dataset derived from HAM10000. "
            "This model is appropriate only for visible skin-lesion screening demos."
        ),
    },
    "breastmnist": {
        "python_class": "BreastMNIST",
        "image_size": 64,
        "deploy_model": "breast_ultrasound_model.keras",
        "deploy_labels": "breast_ultrasound_labels.json",
        "model_name": "MobileNetV2 (BreastMNIST)",
        "note": (
            "BreastMNIST is a compact breast ultrasound dataset. "
            "This model is appropriate only for breast ultrasound demo screening."
        ),
    },
    "pathmnist": {
        "python_class": "PathMNIST",
        "image_size": 64,
        "deploy_model": "colorectal_histology_model.keras",
        "deploy_labels": "colorectal_histology_labels.json",
        "model_name": "MobileNetV2 (PathMNIST)",
        "note": (
            "PathMNIST is a colorectal histopathology tile dataset. "
            "This model is appropriate only for pathology tile demo screening."
        ),
    },
}


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a MedMNIST image model and save deployable artifacts."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=sorted(DATASET_CONFIGS.keys()),
        help="MedMNIST dataset key to train.",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="research_datasets",
        help="Directory for downloaded MedMNIST files.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory for training metrics and checkpoints.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=6,
        help="Training epochs for the frozen-backbone phase.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Training batch size.",
    )
    parser.add_argument(
        "--fine-tune",
        action="store_true",
        help="Unfreeze the last part of the backbone for a short second phase.",
    )
    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=0,
        help="Optional cap on train samples for faster experiments. 0 uses the full split.",
    )
    parser.add_argument(
        "--max-val-samples",
        type=int,
        default=0,
        help="Optional cap on validation samples. 0 uses the full split.",
    )
    parser.add_argument(
        "--max-test-samples",
        type=int,
        default=0,
        help="Optional cap on test samples. 0 uses the full split.",
    )
    return parser.parse_args()


def _subset_split(images: np.ndarray, labels: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray]:
    if not limit or limit <= 0 or limit >= len(images):
        return images, labels

    rng = np.random.default_rng(SEED)
    indices = rng.choice(len(images), size=limit, replace=False)
    indices.sort()
    return images[indices], labels[indices]


def _ensure_rgb(images: np.ndarray) -> np.ndarray:
    if images.ndim == 3:
        images = np.expand_dims(images, -1)
    if images.shape[-1] == 1:
        images = np.repeat(images, 3, axis=-1)
    return images


def load_medmnist(args: argparse.Namespace):
    from medmnist import INFO
    from medmnist import dataset as medmnist_dataset

    config = DATASET_CONFIGS[args.dataset]
    image_size = int(config["image_size"])
    info = INFO[args.dataset]
    labels_map = info["label"]
    class_names = [labels_map[str(i)] for i in range(len(labels_map))]
    dataset_class = getattr(medmnist_dataset, config["python_class"])

    train_ds = dataset_class(split="train", download=True, root=str(args.data_dir), size=image_size)
    val_ds = dataset_class(split="val", download=True, root=str(args.data_dir), size=image_size)
    test_ds = dataset_class(split="test", download=True, root=str(args.data_dir), size=image_size)

    x_train = _ensure_rgb(train_ds.imgs.astype("float32") / 255.0)
    y_train = train_ds.labels.astype("int32").reshape(-1)
    x_val = _ensure_rgb(val_ds.imgs.astype("float32") / 255.0)
    y_val = val_ds.labels.astype("int32").reshape(-1)
    x_test = _ensure_rgb(test_ds.imgs.astype("float32") / 255.0)
    y_test = test_ds.labels.astype("int32").reshape(-1)

    source_counts = {
        "train": int(len(x_train)),
        "val": int(len(x_val)),
        "test": int(len(x_test)),
    }

    x_train, y_train = _subset_split(x_train, y_train, args.max_train_samples)
    x_val, y_val = _subset_split(x_val, y_val, args.max_val_samples)
    x_test, y_test = _subset_split(x_test, y_test, args.max_test_samples)

    used_counts = {
        "train": int(len(x_train)),
        "val": int(len(x_val)),
        "test": int(len(x_test)),
    }

    return (x_train, y_train), (x_val, y_val), (x_test, y_test), class_names, source_counts, used_counts


def build_model(image_size: int, num_classes: int) -> tuple[tf.keras.Model, tf.keras.Model]:
    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(image_size, image_size, 3),
        include_top=False,
        weights="imagenet",
    )
    backbone.trainable = False

    inputs = tf.keras.Input(shape=(image_size, image_size, 3))
    x = tf.keras.layers.RandomFlip("horizontal")(inputs)
    x = tf.keras.layers.RandomRotation(0.05)(x)
    x = tf.keras.layers.RandomZoom(0.1)(x)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x * 255.0)
    x = backbone(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.35)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs, name=f"{num_classes}_class_medmnist_classifier")
    return model, backbone


def compile_model(model: tf.keras.Model, learning_rate: float) -> None:
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )


def make_datasets(x_train, y_train, x_val, y_val, x_test, y_test, batch_size: int):
    autotune = tf.data.AUTOTUNE

    train = tf.data.Dataset.from_tensor_slices((x_train, y_train))
    train = train.shuffle(len(x_train), seed=SEED).batch(batch_size).prefetch(autotune)

    val = tf.data.Dataset.from_tensor_slices((x_val, y_val)).batch(batch_size).prefetch(autotune)
    test = tf.data.Dataset.from_tensor_slices((x_test, y_test)).batch(batch_size).prefetch(autotune)
    return train, val, test


def evaluate_model(model: tf.keras.Model, x_test: np.ndarray, y_test: np.ndarray, class_names: list[str]) -> dict:
    probabilities = model.predict(x_test, verbose=0)
    predictions = np.argmax(probabilities, axis=1)

    report = classification_report(
        y_test,
        predictions,
        target_names=class_names,
        zero_division=0,
        output_dict=True,
    )
    cm = confusion_matrix(y_test, predictions).tolist()

    return {
        "accuracy": float(np.mean(predictions == y_test)),
        "confusion_matrix": cm,
        "classification_report": report,
    }


def main() -> None:
    args = parse_args()
    set_seed()

    config = DATASET_CONFIGS[args.dataset]
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    deploy_dir = Path("backend") / "models"

    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    deploy_dir.mkdir(parents=True, exist_ok=True)

    (x_train, y_train), (x_val, y_val), (x_test, y_test), class_names, source_counts, used_counts = load_medmnist(args)
    train_ds, val_ds, test_ds = make_datasets(
        x_train, y_train, x_val, y_val, x_test, y_test, args.batch_size
    )

    model, backbone = build_model(
        image_size=int(config["image_size"]),
        num_classes=len(class_names),
    )
    compile_model(model, learning_rate=1e-3)

    classes = np.unique(y_train)
    class_weights_raw = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train,
    )
    class_weights = {
        int(class_id): float(weight)
        for class_id, weight in zip(classes, class_weights_raw)
    }

    checkpoint_path = output_dir / f"best_{args.dataset}_model.keras"
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_loss",
            save_best_only=True,
        ),
    ]

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,
    )

    if args.fine_tune:
        backbone.trainable = True
        for layer in backbone.layers[:-30]:
            layer.trainable = False
        compile_model(model, learning_rate=1e-5)
        model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=max(3, args.epochs // 2),
            class_weight=class_weights,
            callbacks=callbacks,
            verbose=1,
        )

    best_model = tf.keras.models.load_model(checkpoint_path)
    metrics = evaluate_model(best_model, x_test, y_test, class_names)

    metadata = {
        "dataset": args.dataset,
        "model_name": config["model_name"],
        "image_size": int(config["image_size"]),
        "class_names": class_names,
        "source_samples": source_counts,
        "used_samples": used_counts,
        "epochs_requested": args.epochs,
        "best_val_accuracy": float(max(history.history["val_accuracy"])),
        "best_val_loss": float(min(history.history["val_loss"])),
        "note": config["note"],
    }

    with open(output_dir / f"{args.dataset}_metrics.json", "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    with open(output_dir / f"{args.dataset}_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    best_model.save(deploy_dir / config["deploy_model"])
    with open(deploy_dir / config["deploy_labels"], "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print("Training complete.")
    print(f"Dataset: {args.dataset}")
    print(f"Saved model: {deploy_dir / config['deploy_model']}")
    print(f"Saved labels: {deploy_dir / config['deploy_labels']}")
    print(f"Test accuracy: {metrics['accuracy']:.4f}")


if __name__ == "__main__":
    main()
