import argparse
import json
import os
import random
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix


SEED = 42
IMG_SIZE = (224, 224)


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
        description="Train an image classifier for visible cancer / lesion screening."
    )
    parser.add_argument(
        "--dataset-root",
        type=str,
        required=True,
        help="Dataset root. Expected either train/val/test folders or class folders for auto-splitting.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="research_outputs_image",
        help="Directory for metrics, labels, and model artifacts.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=20,
        help="Max training epochs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size.",
    )
    parser.add_argument(
        "--validation-split",
        type=float,
        default=0.15,
        help="Validation split when train/val folders are not provided.",
    )
    parser.add_argument(
        "--test-split",
        type=float,
        default=0.15,
        help="Test split when train/test folders are not provided.",
    )
    parser.add_argument(
        "--pretrained",
        choices=["imagenet", "none"],
        default="imagenet",
        help="Use ImageNet weights when available.",
    )
    parser.add_argument(
        "--fine-tune",
        action="store_true",
        help="Unfreeze the backbone after warmup for a second training phase.",
    )
    return parser.parse_args()


def _dataset_exists(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def load_datasets(args: argparse.Namespace):
    root = Path(args.dataset_root)
    train_dir = root / "train"
    val_dir = root / "val"
    test_dir = root / "test"

    common_kwargs = {
        "image_size": IMG_SIZE,
        "batch_size": args.batch_size,
        "seed": SEED,
    }

    if _dataset_exists(train_dir):
        train_ds = tf.keras.utils.image_dataset_from_directory(
            train_dir,
            shuffle=True,
            **common_kwargs,
        )
        class_names = train_ds.class_names

        if _dataset_exists(val_dir):
            val_ds = tf.keras.utils.image_dataset_from_directory(
                val_dir,
                shuffle=False,
                **common_kwargs,
            )
        else:
            raise ValueError("Dataset has train/ but no val/. Add val/ or use a flat class-folder dataset.")

        if _dataset_exists(test_dir):
            test_ds = tf.keras.utils.image_dataset_from_directory(
                test_dir,
                shuffle=False,
                **common_kwargs,
            )
        else:
            raise ValueError("Dataset has train/ but no test/. Add test/ or use a flat class-folder dataset.")
    else:
        full_ds = tf.keras.utils.image_dataset_from_directory(
            root,
            validation_split=args.validation_split + args.test_split,
            subset="training",
            shuffle=True,
            **common_kwargs,
        )
        class_names = full_ds.class_names

        holdout_ds = tf.keras.utils.image_dataset_from_directory(
            root,
            validation_split=args.validation_split + args.test_split,
            subset="validation",
            shuffle=True,
            **common_kwargs,
        )

        holdout_batches = tf.data.experimental.cardinality(holdout_ds).numpy()
        if holdout_batches < 2:
            raise ValueError("Dataset too small to split into validation and test sets.")

        test_batches = max(1, int(round(holdout_batches * (args.test_split / (args.validation_split + args.test_split)))))
        val_batches = holdout_batches - test_batches

        val_ds = holdout_ds.take(val_batches)
        test_ds = holdout_ds.skip(val_batches)
        train_ds = full_ds

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(autotune)
    val_ds = val_ds.cache().prefetch(autotune)
    test_ds = test_ds.cache().prefetch(autotune)
    return train_ds, val_ds, test_ds, class_names


def build_model(num_classes: int, pretrained: str = "imagenet") -> tf.keras.Model:
    try:
        weights = "imagenet" if pretrained == "imagenet" else None
        backbone = tf.keras.applications.EfficientNetB0(
            include_top=False,
            weights=weights,
            input_shape=(*IMG_SIZE, 3),
        )
    except Exception:
        backbone = tf.keras.applications.EfficientNetB0(
            include_top=False,
            weights=None,
            input_shape=(*IMG_SIZE, 3),
        )

    backbone.trainable = False

    data_augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.08),
        tf.keras.layers.RandomZoom(0.12),
        tf.keras.layers.RandomContrast(0.12),
    ])

    inputs = tf.keras.Input(shape=(*IMG_SIZE, 3))
    x = data_augmentation(inputs)
    x = tf.keras.applications.efficientnet.preprocess_input(x)
    x = backbone(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.35)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs, name="cancer_image_classifier")
    return model


def compile_model(model: tf.keras.Model, learning_rate: float) -> None:
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )


def evaluate_model(model: tf.keras.Model, test_ds, class_names: list[str]) -> dict:
    probabilities = model.predict(test_ds, verbose=0)
    predictions = np.argmax(probabilities, axis=1)

    y_true = np.concatenate([labels.numpy() for _, labels in test_ds], axis=0)
    report = classification_report(
        y_true,
        predictions,
        target_names=class_names,
        zero_division=0,
        output_dict=True,
    )
    cm = confusion_matrix(y_true, predictions).tolist()

    return {
        "confusion_matrix": cm,
        "classification_report": report,
        "accuracy": float(np.mean(predictions == y_true)),
    }


def main() -> None:
    args = parse_args()
    set_seed(SEED)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_ds, val_ds, test_ds, class_names = load_datasets(args)
    model = build_model(num_classes=len(class_names), pretrained=args.pretrained)
    compile_model(model, learning_rate=1e-3)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=output_dir / "best_image_model.keras",
            monitor="val_loss",
            save_best_only=True,
        ),
    ]

    warmup_history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=callbacks,
        verbose=1,
    )

    if args.fine_tune:
        backbone = model.layers[3]
        backbone.trainable = True
        for layer in backbone.layers[:-30]:
            layer.trainable = False
        compile_model(model, learning_rate=1e-5)
        model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=max(5, args.epochs // 2),
            callbacks=callbacks,
            verbose=1,
        )

    best_model = tf.keras.models.load_model(output_dir / "best_image_model.keras")
    metrics = evaluate_model(best_model, test_ds, class_names)

    metadata = {
        "class_names": class_names,
        "image_size": IMG_SIZE,
        "pretrained": args.pretrained,
        "fine_tune": args.fine_tune,
        "epochs_requested": args.epochs,
        "warmup_best_val_accuracy": float(max(warmup_history.history["val_accuracy"])),
        "warmup_best_val_loss": float(min(warmup_history.history["val_loss"])),
    }

    with open(output_dir / "image_model_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    with open(output_dir / "image_model_metrics.json", "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    deploy_dir = Path("backend") / "models"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    best_model.save(deploy_dir / "skin_lesion_model.keras")
    with open(deploy_dir / "skin_lesion_labels.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print("Training complete.")
    print(f"Classes: {class_names}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Saved deployable model to: {deploy_dir / 'skin_lesion_model.keras'}")


if __name__ == "__main__":
    main()
