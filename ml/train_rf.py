from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


def load_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Features file '{path}' does not exist.")
    df = pd.read_csv(path)
    required_columns = {"id", "label"}
    if not required_columns.issubset(df.columns):
        raise ValueError(
            "Features CSV must include at least 'id' and 'label' columns."
        )
    feature_columns = [col for col in df.columns if col not in ("id", "label")]
    if not feature_columns:
        raise ValueError("Features CSV must contain numeric feature columns.")
    return df


def train_model(df: pd.DataFrame) -> Tuple[RandomForestClassifier, pd.DataFrame, float]:
    feature_columns = [col for col in df.columns if col not in ("id", "label")]
    X = df[feature_columns]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
        if len(y.unique()) > 1 and len(y) > 1
        else None,
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    conf_matrix = confusion_matrix(y_test, y_pred, labels=clf.classes_)
    acc = accuracy_score(y_test, y_pred)

    return clf, pd.DataFrame(conf_matrix, index=clf.classes_, columns=clf.classes_), acc


def save_model(model: RandomForestClassifier, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def save_metrics(conf_matrix_df: pd.DataFrame, accuracy: float, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    display = ConfusionMatrixDisplay(
        confusion_matrix=conf_matrix_df.values,
        display_labels=conf_matrix_df.index,
    )
    display.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Random Forest Confusion Matrix")
    ax.text(
        0.5,
        -0.15,
        f"Accuracy: {accuracy:.4f}",
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=12,
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a RandomForest model on extracted features."
    )
    parser.add_argument(
        "--features",
        required=True,
        type=Path,
        help="Path to features CSV file.",
    )
    parser.add_argument(
        "--model-out",
        type=Path,
        default=Path("ml/model_rf.pkl"),
        help="Path to save the trained model.",
    )
    parser.add_argument(
        "--metrics-out",
        type=Path,
        default=Path("ml/metrics.png"),
        help="Path to save the metrics plot.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    df = load_features(args.features)
    model, conf_matrix_df, accuracy = train_model(df)

    save_model(model, args.model_out)
    save_metrics(conf_matrix_df, accuracy, args.metrics_out)

    print(f"Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()

