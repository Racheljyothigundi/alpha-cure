import argparse
import json
import random
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight


SEED = 42
DATASET_NAME = "dermamnist"
IMAGE_SIZE = 64


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
        description="Download DermaMNIST and train a skin-lesion image classifier."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="research_datasets",
        help="Directory for downloaded dataset files.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="research_outputs_dermamnist",
        help="Directory for training outputs and reports.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=8,
        help="Training epochs.",
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
        help="Unfreeze the backbone for a short fine-tuning phase.",
    )
    return parser.parse_args()


def load_dermamnist(data_dir: Path):
    from medmnist import INFO
    from medmnist.dataset import DermaMNIST

    info = INFO[DATASET_NAME]
    labels_map = info["label"]
    class_names = [labels_map[str(i)] for i in range(len(labels_map))]

    train_ds = DermaMNIST(split="train", download=True, root=str(data_dir), size=IMAGE_SIZE)
    val_ds = DermaMNIST(split="val", download=True, root=str(data_dir), size=IMAGE_SIZE)
    test_ds = DermaMNIST(split="test", download=True, root=str(data_dir), size=IMAGE_SIZE)

    x_train = train_ds.imgs.astype("float32") / 255.0
    y_train = train_ds.labels.astype("int32").reshape(-1)
    x_val = val_ds.imgs.astype("float32") / 255.0
    y_val = val_ds.labels.astype("int32").reshape(-1)
    x_test = test_ds.imgs.astype("float32") / 255.0
    y_test = test_ds.labels.astype("int32").reshape(-1)

    if x_train.ndim == 3:
        x_train = np.expand_dims(x_train, -1)
        x_val = np.expand_dims(x_val, -1)
        x_test = np.expand_dims(x_test, -1)

    if x_train.shape[-1] == 1:
        x_train = np.repeat(x_train, 3, axis=-1)
        x_val = np.repeat(x_val, 3, axis=-1)
        x_test = np.repeat(x_test, 3, axis=-1)

    return (x_train, y_train), (x_val, y_val), (x_test, y_test), class_names


def build_model(num_classes: int) -> tuple[tf.keras.Model, tf.keras.Model]:
    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    backbone.trainable = False

    inputs = tf.keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3))
    x = tf.keras.layers.RandomFlip("horizontal")(inputs)
    x = tf.keras.layers.RandomRotation(0.05)(x)
    x = tf.keras.layers.RandomZoom(0.1)(x)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x * 255.0)
    x = backbone(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.35)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs, name="dermamnist_classifier")
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

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    deploy_dir = Path("backend") / "models"

    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    deploy_dir.mkdir(parents=True, exist_ok=True)

    (x_train, y_train), (x_val, y_val), (x_test, y_test), class_names = load_dermamnist(data_dir)
    train_ds, val_ds, test_ds = make_datasets(
        x_train, y_train, x_val, y_val, x_test, y_test, args.batch_size
    )

    model, backbone = build_model(num_classes=len(class_names))
    compile_model(model, learning_rate=1e-3)

    class_weights_raw = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train),
        y=y_train,
    )
    class_weights = {idx: float(weight) for idx, weight in enumerate(class_weights_raw)}

    checkpoint_path = output_dir / "best_dermamnist_model.keras"
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
        "dataset": DATASET_NAME,
        "image_size": IMAGE_SIZE,
        "class_names": class_names,
        "train_samples": int(len(x_train)),
        "val_samples": int(len(x_val)),
        "test_samples": int(len(x_test)),
        "epochs_requested": args.epochs,
        "best_val_accuracy": float(max(history.history["val_accuracy"])),
        "best_val_loss": float(min(history.history["val_loss"])),
        "note": (
            "DermaMNIST is a skin-lesion dataset derived from HAM10000. "
            "This model is appropriate only for visible skin-lesion screening demos."
        ),
    }

    with open(output_dir / "dermamnist_metrics.json", "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    with open(output_dir / "dermamnist_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    best_model.save(deploy_dir / "skin_lesion_model.keras")
    with open(deploy_dir / "skin_lesion_labels.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print("Training complete.")
    print(f"Saved model: {deploy_dir / 'skin_lesion_model.keras'}")
    print(f"Saved labels: {deploy_dir / 'skin_lesion_labels.json'}")
    print(f"Test accuracy: {metrics['accuracy']:.4f}")


if __name__ == "__main__":
    main()
