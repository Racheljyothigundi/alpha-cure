import argparse
import json
import os
import pickle
import random
import re
import tempfile
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


SEED = 42
TARGET_COLUMN = "Cancer_Risk_Level"


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass


def configure_runtime(output_dir: Path) -> None:
    temp_dir = output_dir / "_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TMPDIR"] = str(temp_dir)
    os.environ["TEMP"] = str(temp_dir)
    os.environ["TMP"] = str(temp_dir)
    tempfile.tempdir = str(temp_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train multiple deep learning models for multiclass cervical cancer risk classification."
    )
    parser.add_argument(
        "--excel-path",
        type=str,
        required=True,
        help="Path to the uploaded Excel dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="research_outputs",
        help="Directory where trained models and reports will be saved.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=80,
        help="Maximum training epochs per model.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=128,
        help="Batch size for training.",
    )
    parser.add_argument(
        "--target-column",
        type=str,
        default=TARGET_COLUMN,
        help="Target column name in the Excel file.",
    )
    return parser.parse_args()


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        raise ValueError(f"Unexpected Excel cell reference: {cell_ref}")
    index = 0
    for char in match.group(1):
        index = index * 26 + (ord(char) - 64)
    return index - 1


def _read_cell_value(cell: ET.Element, ns: dict[str, str], shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        return "".join(text_node.text or "" for text_node in cell.findall(".//main:t", ns))

    value_node = cell.find("main:v", ns)
    if value_node is None:
        return ""

    value = value_node.text or ""
    if cell_type == "s" and value:
        return shared_strings[int(value)]
    return value


def load_excel_with_fallback(excel_path: Path) -> pd.DataFrame:
    try:
        return pd.read_excel(excel_path, engine="openpyxl")
    except Exception:
        pass

    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(excel_path) as workbook_zip:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook_zip.namelist():
            shared_root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("main:si", ns):
                shared_text = "".join(text_node.text or "" for text_node in item.findall(".//main:t", ns))
                shared_strings.append(shared_text)

        sheet_root = ET.fromstring(workbook_zip.read("xl/worksheets/sheet1.xml"))
        rows = sheet_root.findall(".//main:sheetData/main:row", ns)

        matrix: list[list[str]] = []
        for row in rows:
            row_map: dict[int, str] = {}
            for cell in row.findall("main:c", ns):
                idx = _column_index(cell.attrib.get("r", "A1"))
                row_map[idx] = _read_cell_value(cell, ns, shared_strings)
            if not row_map:
                continue
            row_values = [row_map.get(i, "") for i in range(max(row_map.keys()) + 1)]
            matrix.append(row_values)

    header = matrix[0]
    data = matrix[1:]
    frame = pd.DataFrame(data, columns=header)
    for column in frame.columns:
        try:
            frame[column] = pd.to_numeric(frame[column])
        except Exception:
            pass
    return frame


def prepare_data(df: pd.DataFrame, target_column: str) -> tuple[np.ndarray, ...]:
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' was not found. Available columns: {list(df.columns)}")

    df = df.copy()
    df = df.dropna(axis=0).reset_index(drop=True)

    X = df.drop(columns=[target_column]).astype(np.float32)
    y = df[target_column]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    num_classes = len(label_encoder.classes_)

    x_train, x_temp, y_train, y_temp = train_test_split(
        X.values,
        y_encoded,
        test_size=0.30,
        stratify=y_encoded,
        random_state=SEED,
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=0.50,
        stratify=y_temp,
        random_state=SEED,
    )

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train).astype(np.float32)
    x_val_scaled = scaler.transform(x_val).astype(np.float32)
    x_test_scaled = scaler.transform(x_test).astype(np.float32)

    y_train_cat = tf.keras.utils.to_categorical(y_train, num_classes=num_classes)
    y_val_cat = tf.keras.utils.to_categorical(y_val, num_classes=num_classes)
    y_test_cat = tf.keras.utils.to_categorical(y_test, num_classes=num_classes)

    return (
        x_train_scaled,
        x_val_scaled,
        x_test_scaled,
        y_train,
        y_val,
        y_test,
        y_train_cat,
        y_val_cat,
        y_test_cat,
        scaler,
        label_encoder,
        list(X.columns),
    )


def common_callbacks(model_name: str, output_dir: Path) -> list[tf.keras.callbacks.Callback]:
    return [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=15,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=6,
            min_lr=1e-5,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=output_dir / f"{model_name}.keras",
            monitor="val_loss",
            save_best_only=True,
        ),
    ]


def build_baseline_mlp(input_dim: int, num_classes: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(input_dim,), name="features")
    x = tf.keras.layers.Dense(128, activation="relu")(inputs)
    x = tf.keras.layers.Dropout(0.25)(x)
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="baseline_mlp")


def build_deep_regularized_mlp(input_dim: int, num_classes: int) -> tf.keras.Model:
    regularizer = tf.keras.regularizers.l2(1e-4)
    inputs = tf.keras.Input(shape=(input_dim,), name="features")
    x = tf.keras.layers.Dense(256, kernel_regularizer=regularizer)(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Activation("relu")(x)
    x = tf.keras.layers.Dropout(0.35)(x)
    x = tf.keras.layers.Dense(128, kernel_regularizer=regularizer)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Activation("relu")(x)
    x = tf.keras.layers.Dropout(0.30)(x)
    x = tf.keras.layers.Dense(64, kernel_regularizer=regularizer)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Activation("relu")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="deep_regularized_mlp")


def residual_block(x: tf.Tensor, units: int, dropout_rate: float) -> tf.Tensor:
    shortcut = x
    x = tf.keras.layers.Dense(units)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Activation("relu")(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)
    x = tf.keras.layers.Dense(units)(x)
    x = tf.keras.layers.BatchNormalization()(x)

    if shortcut.shape[-1] != units:
        shortcut = tf.keras.layers.Dense(units)(shortcut)

    x = tf.keras.layers.Add()([x, shortcut])
    x = tf.keras.layers.Activation("relu")(x)
    return x


def build_residual_mlp(input_dim: int, num_classes: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(input_dim,), name="features")
    x = tf.keras.layers.Dense(128, activation="relu")(inputs)
    x = residual_block(x, 128, 0.25)
    x = residual_block(x, 64, 0.20)
    x = tf.keras.layers.Dropout(0.20)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="residual_mlp")


def build_feature_cnn(input_dim: int, num_classes: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(input_dim, 1), name="feature_sequence")
    x = tf.keras.layers.Conv1D(32, kernel_size=3, padding="same", activation="relu")(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv1D(64, kernel_size=3, padding="same", activation="relu")(x)
    x = tf.keras.layers.GlobalAveragePooling1D()(x)
    x = tf.keras.layers.Dropout(0.30)(x)
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="feature_cnn")


def compile_model(model: tf.keras.Model) -> tf.keras.Model:
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
) -> dict[str, object]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            target_names=class_names,
            zero_division=0,
            output_dict=True,
        ),
    }


def train_dense_model(
    model_name: str,
    model_builder,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    y_test_labels: np.ndarray,
    class_names: list[str],
    output_dir: Path,
    epochs: int,
    batch_size: int,
) -> dict[str, object]:
    model = compile_model(model_builder(x_train.shape[1], y_train.shape[1]))
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=common_callbacks(model_name, output_dir),
        verbose=0,
    )

    best_model = tf.keras.models.load_model(output_dir / f"{model_name}.keras")
    probabilities = best_model.predict(x_test, verbose=0)
    predictions = np.argmax(probabilities, axis=1)
    metrics = evaluate_predictions(y_test_labels, predictions, class_names)
    metrics["best_val_accuracy"] = float(max(history.history["val_accuracy"]))
    metrics["best_val_loss"] = float(min(history.history["val_loss"]))
    metrics["model_path"] = str(output_dir / f"{model_name}.keras")
    return metrics


def train_cnn_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    y_test_labels: np.ndarray,
    class_names: list[str],
    output_dir: Path,
    epochs: int,
    batch_size: int,
) -> dict[str, object]:
    model_name = "feature_cnn"
    x_train_seq = np.expand_dims(x_train, axis=-1)
    x_val_seq = np.expand_dims(x_val, axis=-1)
    x_test_seq = np.expand_dims(x_test, axis=-1)

    model = compile_model(build_feature_cnn(x_train.shape[1], y_train.shape[1]))
    history = model.fit(
        x_train_seq,
        y_train,
        validation_data=(x_val_seq, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=common_callbacks(model_name, output_dir),
        verbose=0,
    )

    best_model = tf.keras.models.load_model(output_dir / f"{model_name}.keras")
    probabilities = best_model.predict(x_test_seq, verbose=0)
    predictions = np.argmax(probabilities, axis=1)
    metrics = evaluate_predictions(y_test_labels, predictions, class_names)
    metrics["best_val_accuracy"] = float(max(history.history["val_accuracy"]))
    metrics["best_val_loss"] = float(min(history.history["val_loss"]))
    metrics["model_path"] = str(output_dir / f"{model_name}.keras")
    return metrics


def save_metadata(
    output_dir: Path,
    scaler: StandardScaler,
    label_encoder: LabelEncoder,
    feature_columns: list[str],
) -> None:
    metadata = {
        "feature_columns": feature_columns,
        "class_names": label_encoder.classes_.tolist(),
    }
    with open(output_dir / "preprocessing.pkl", "wb") as file_handle:
        pickle.dump(
            {
                "scaler": scaler,
                "label_encoder": label_encoder,
                "feature_columns": feature_columns,
            },
            file_handle,
        )
    with open(output_dir / "dataset_metadata.json", "w", encoding="utf-8") as file_handle:
        json.dump(metadata, file_handle, indent=2)


def print_leaderboard(results: dict[str, dict[str, object]]) -> None:
    leaderboard = (
        pd.DataFrame(
            [
                {
                    "model": model_name,
                    "accuracy": metrics["accuracy"],
                    "macro_f1": metrics["macro_f1"],
                    "weighted_f1": metrics["weighted_f1"],
                    "macro_precision": metrics["macro_precision"],
                    "macro_recall": metrics["macro_recall"],
                    "best_val_accuracy": metrics["best_val_accuracy"],
                }
                for model_name, metrics in results.items()
            ]
        )
        .sort_values(by=["weighted_f1", "accuracy"], ascending=False)
        .reset_index(drop=True)
    )
    print("\nModel leaderboard:")
    print(leaderboard.to_string(index=False))


def main() -> None:
    set_seed()
    args = parse_args()
    excel_path = Path(args.excel_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_runtime(output_dir)

    df = load_excel_with_fallback(excel_path)
    print("Loaded dataset shape:", df.shape)
    print("Columns:", list(df.columns))
    print("Class distribution:", dict(Counter(df[args.target_column])))

    (
        x_train,
        x_val,
        x_test,
        y_train_labels,
        y_val_labels,
        y_test_labels,
        y_train_cat,
        y_val_cat,
        y_test_cat,
        scaler,
        label_encoder,
        feature_columns,
    ) = prepare_data(df, args.target_column)

    del y_train_labels, y_val_labels

    class_names = [str(name) for name in label_encoder.classes_.tolist()]

    results: dict[str, dict[str, object]] = {}
    dense_models = {
        "baseline_mlp": build_baseline_mlp,
        "deep_regularized_mlp": build_deep_regularized_mlp,
        "residual_mlp": build_residual_mlp,
    }

    for model_name, builder in dense_models.items():
        print(f"\nTraining {model_name}...")
        results[model_name] = train_dense_model(
            model_name=model_name,
            model_builder=builder,
            x_train=x_train,
            y_train=y_train_cat,
            x_val=x_val,
            y_val=y_val_cat,
            x_test=x_test,
            y_test=y_test_cat,
            y_test_labels=y_test_labels,
            class_names=class_names,
            output_dir=output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )

    print("\nTraining feature_cnn...")
    results["feature_cnn"] = train_cnn_model(
        x_train=x_train,
        y_train=y_train_cat,
        x_val=x_val,
        y_val=y_val_cat,
        x_test=x_test,
        y_test=y_test_cat,
        y_test_labels=y_test_labels,
        class_names=class_names,
        output_dir=output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )

    save_metadata(output_dir, scaler, label_encoder, feature_columns)

    with open(output_dir / "model_comparison.json", "w", encoding="utf-8") as file_handle:
        json.dump(results, file_handle, indent=2)

    print_leaderboard(results)

    best_model_name = max(results, key=lambda name: results[name]["weighted_f1"])
    print(f"\nBest model: {best_model_name}")
    print(json.dumps(results[best_model_name], indent=2))


if __name__ == "__main__":
    main()
