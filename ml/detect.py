from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List

import joblib
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from features.extract_features import parse_strace_file


FEATURE_COLUMNS = [
    "open_count",
    "read_count",
    "write_count",
    "execve_count",
    "connect_count",
    "fork_count",
    "clone_count",
    "created_count",
    "deleted_count",
    "new_process_count",
]


def load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Model file '{path}' not found.")
    return joblib.load(path)


def load_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Features file '{path}' not found.")
    df = pd.read_csv(path)
    if "id" not in df.columns:
        df["id"] = [f"sample_{i}" for i in range(len(df))]
    return df


def extract_features_from_log(log_path: Path) -> pd.DataFrame:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file '{log_path}' not found.")
    counts = parse_strace_file(log_path)
    data = {col: counts.get(col, 0) for col in FEATURE_COLUMNS}
    data["id"] = log_path.stem
    return pd.DataFrame([data])


def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    missing_cols = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Input data missing required feature columns: {', '.join(missing_cols)}"
        )
    ordered_cols = ["id"] + FEATURE_COLUMNS
    label_set = set(df.columns) - set(ordered_cols)
    if "label" in label_set:
        ordered_cols.insert(1, "label")
    existing_cols = [col for col in ordered_cols if col in df.columns]
    existing_cols += [col for col in df.columns if col not in existing_cols]
    return df[existing_cols]


def predict_single(
    model, row: pd.Series, feature_columns: List[str]
) -> Dict[str, str | float]:
    malicious_index = list(model.classes_).index("malicious")
    proba = model.predict_proba(row[feature_columns].to_frame().T)[0][malicious_index]
    verdict = "malicious" if proba > 0.5 else "benign"
    result_type = "malware" if verdict == "malicious" else "clean"
    return {
        "id": str(row.get("id", "sample")),
        "verdict": verdict,
        "type": result_type,
        "confidence": round(float(proba), 4),
    }


def predict_batch(model, df: pd.DataFrame) -> List[Dict[str, str | float]]:
    feature_columns = FEATURE_COLUMNS
    results = []
    for _, row in df.iterrows():
        results.append(predict_single(model, row, feature_columns))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect malicious behavior from features or strace log."
    )
    parser.add_argument(
        "--features",
        type=Path,
        help="Path to features CSV file for batch detection.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="Path to individual .strace log for single detection.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("ml/model_rf.pkl"),
        help="Path to trained RandomForest model.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.features and not args.log:
        raise ValueError("Please provide --features or --log.")

    model = load_model(args.model)

    if args.features:
        df = load_features(args.features)
    else:
        df = extract_features_from_log(args.log)

    df = _prepare_features(df)
    results = predict_batch(model, df)

    output = results[0] if len(results) == 1 else results
    print(json.dumps(output, indent=4))


if __name__ == "__main__":
    main()

