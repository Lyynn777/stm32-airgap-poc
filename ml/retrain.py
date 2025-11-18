#!/usr/bin/env python3
"""
Automated retraining script for the ML subsystem.

This script automates the periodic retraining workflow:
1. Regenerates features from dataset/
2. Retrains the RandomForest model with timestamped outputs
3. Updates the stable model alias (ml/model_rf.pkl)
4. Maintains version history with retention policy
5. Provides dry-run mode for safe testing

Usage:
    python ml/retrain.py --dataset-dir dataset --labels dataset/labels.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path for importing features module
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from features.extract_features import extract_features as extract_features_lib
except ImportError:
    extract_features_lib = None


def log(message: str, verbose: bool = False) -> None:
    """Print log message if verbose mode is enabled."""
    if verbose:
        print(f"[LOG] {message}", file=sys.stderr)


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_safety_requirements(
    dataset_dir: Path, labels_path: Path, train_script: Path, dry_run: bool
) -> None:
    """
    Perform safety checks before proceeding.
    Exits with error code if any check fails.
    """
    if not dataset_dir.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Dataset directory '{dataset_dir}' does not exist.",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    if not labels_path.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Labels file '{labels_path}' does not exist.",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    # Verify labels CSV is readable
    try:
        with labels_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or "id" not in reader.fieldnames:
                raise ValueError("Labels CSV must have 'id' column.")
    except Exception as e:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Labels file '{labels_path}' is not a valid CSV: {e}",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    if not train_script.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Training script '{train_script}' does not exist.",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    if not dry_run:
        log("All safety checks passed.", verbose=True)


def regenerate_features(
    dataset_dir: Path,
    labels_path: Path,
    features_out: Path,
    dry_run: bool,
    verbose: bool,
) -> None:
    """
    Regenerate features CSV from dataset.
    Prefers importing library function, falls back to subprocess.
    """
    log(f"Regenerating features from '{dataset_dir}'...", verbose=verbose)

    if dry_run:
        if extract_features_lib:
            print(
                f"[DRY-RUN] Would call extract_features({dataset_dir}, {labels_path}) "
                f"and save to {features_out}",
                file=sys.stderr,
            )
        else:
            cmd = [
                "python",
                "features/extract_features.py",
                "--input-dir",
                str(dataset_dir),
                "--labels",
                str(labels_path),
                "--output",
                str(features_out),
            ]
            print(f"[DRY-RUN] Would run: {' '.join(cmd)}", file=sys.stderr)
        return

    # Try to use library function first
    if extract_features_lib:
        try:
            import pandas as pd

            df = extract_features_lib(dataset_dir, labels_path)
            features_out.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(features_out, index=False)
            log(f"Features regenerated using library function: {features_out}", verbose=verbose)
            return
        except Exception as e:
            log(
                f"Library function failed ({e}), falling back to subprocess...",
                verbose=verbose,
            )

    # Fallback to subprocess
    cmd = [
        sys.executable,
        str(ROOT_DIR / "features" / "extract_features.py"),
        "--input-dir",
        str(dataset_dir),
        "--labels",
        str(labels_path),
        "--output",
        str(features_out),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT_DIR)
    if result.returncode != 0:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Feature extraction failed: {result.stderr}",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    log(f"Features regenerated: {features_out}", verbose=verbose)


def retrain_model(
    features_path: Path,
    model_dir: Path,
    metrics_dir: Path,
    train_script: Path,
    timestamp: str,
    dry_run: bool,
    verbose: bool,
) -> tuple[Path, Path, Path]:
    """
    Retrain the model using train_rf.py.
    Returns (model_path, metrics_path, log_path).
    """
    # Create timestamped paths
    model_filename = f"model_rf_{timestamp}.pkl"
    metrics_filename = f"metrics_{timestamp}.png"
    log_filename = f"retrain_{timestamp}.log"

    model_path = model_dir / model_filename
    metrics_path = metrics_dir / metrics_filename
    log_path = model_dir / log_filename

    log(f"Retraining model (output: {model_path})...", verbose=verbose)

    if dry_run:
        cmd = [
            sys.executable,
            str(train_script),
            "--features",
            str(features_path),
            "--model-out",
            str(model_path),
            "--metrics-out",
            str(metrics_path),
        ]
        print(f"[DRY-RUN] Would run: {' '.join(cmd)}", file=sys.stderr)
        print(f"[DRY-RUN] Would save log to: {log_path}", file=sys.stderr)
        return model_path, metrics_path, log_path

    # Ensure directories exist
    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    # Call training script
    cmd = [
        sys.executable,
        str(train_script),
        "--features",
        str(features_path),
        "--model-out",
        str(model_path),
        "--metrics-out",
        str(metrics_path),
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=ROOT_DIR
    )

    # Save log
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write(f"Return code: {result.returncode}\n")
        f.write(f"\n--- STDOUT ---\n{result.stdout}\n")
        f.write(f"\n--- STDERR ---\n{result.stderr}\n")

    if result.returncode != 0:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Training failed (return code {result.returncode})",
                    "log_path": str(log_path),
                }
            ),
            file=sys.stderr,
        )
        print(f"Training log saved to: {log_path}", file=sys.stderr)
        sys.exit(1)

    log(f"Model trained successfully: {model_path}", verbose=verbose)
    return model_path, metrics_path, log_path


def promote_model(
    model_path: Path,
    metrics_path: Path,
    model_alias: Path,
    features_sha256: str,
    timestamp: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """
    Promote the new model to be the stable alias.
    Creates a copy (not symlink) for cross-platform compatibility.
    """
    log(f"Promoting model to stable alias: {model_alias}", verbose=verbose)

    if dry_run:
        print(
            f"[DRY-RUN] Would copy {model_path} to {model_alias}",
            file=sys.stderr,
        )
        return

    # Copy model to alias (ensuring parent directory exists)
    model_alias.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_path, model_alias)
    log(f"Model alias updated: {model_alias} -> {model_path}", verbose=verbose)


def update_manifest(
    model_dir: Path,
    timestamp: str,
    model_filename: str,
    metrics_filename: str,
    features_sha256: str,
    notes: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """
    Append entry to manifest.csv in model_dir.
    Format: timestamp, model_filename, metrics_filename, features_sha256, notes
    """
    manifest_path = model_dir / "manifest.csv"
    entry = {
        "timestamp": timestamp,
        "model_filename": model_filename,
        "metrics_filename": metrics_filename,
        "features_sha256": features_sha256,
        "notes": notes,
    }

    log(f"Updating manifest: {manifest_path}", verbose=verbose)

    if dry_run:
        print(f"[DRY-RUN] Would append to manifest: {entry}", file=sys.stderr)
        return

    # Create manifest if it doesn't exist
    file_exists = manifest_path.exists()
    with manifest_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "model_filename",
                "metrics_filename",
                "features_sha256",
                "notes",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)


def cleanup_old_models(
    model_dir: Path,
    metrics_dir: Path,
    n_keep: int,
    dry_run: bool,
    verbose: bool,
) -> None:
    """
    Keep only the latest N models, delete older ones.
    Also removes corresponding metrics and manifest entries.
    """
    log(f"Cleaning up old models (keeping latest {n_keep})...", verbose=verbose)

    # Find all model files
    model_files = sorted(
        model_dir.glob("model_rf_*.pkl"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    if len(model_files) <= n_keep:
        log(f"Only {len(model_files)} models found, no cleanup needed.", verbose=verbose)
        return

    # Files to delete (older than n_keep)
    to_delete = model_files[n_keep:]

    for model_file in to_delete:
        # Extract timestamp from filename
        timestamp = model_file.stem.replace("model_rf_", "")
        metrics_file = metrics_dir / f"metrics_{timestamp}.png"
        log_file = model_dir / f"retrain_{timestamp}.log"

        if dry_run:
            print(f"[DRY-RUN] Would delete: {model_file}", file=sys.stderr)
            if metrics_file.exists():
                print(f"[DRY-RUN] Would delete: {metrics_file}", file=sys.stderr)
            if log_file.exists():
                print(f"[DRY-RUN] Would delete: {log_file}", file=sys.stderr)
        else:
            if model_file.exists():
                model_file.unlink()
                log(f"Deleted old model: {model_file}", verbose=verbose)
            if metrics_file.exists():
                metrics_file.unlink()
                log(f"Deleted old metrics: {metrics_file}", verbose=verbose)
            if log_file.exists():
                log_file.unlink()
                log(f"Deleted old log: {log_file}", verbose=verbose)

    # Clean up manifest entries (remove rows for deleted models)
    manifest_path = model_dir / "manifest.csv"
    if manifest_path.exists() and not dry_run:
        # Read all entries
        entries = []
        with manifest_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        # Filter out entries for deleted models
        deleted_timestamps = {f.stem.replace("model_rf_", "") for f in to_delete}
        kept_entries = [
            e for e in entries if e["timestamp"] not in deleted_timestamps
        ]

        # Rewrite manifest
        with manifest_path.open("w", encoding="utf-8", newline="") as f:
            if kept_entries:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "timestamp",
                        "model_filename",
                        "metrics_filename",
                        "features_sha256",
                        "notes",
                    ],
                )
                writer.writeheader()
                writer.writerows(kept_entries)
            # If no entries left, just write header (or leave empty)
            elif entries:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "timestamp",
                        "model_filename",
                        "metrics_filename",
                        "features_sha256",
                        "notes",
                    ],
                )
                writer.writeheader()

        log(f"Cleaned up manifest entries.", verbose=verbose)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Automated retraining script for ML subsystem.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("dataset"),
        help="Path to dataset directory (default: dataset)",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("dataset/labels.csv"),
        help="Path to labels CSV (default: dataset/labels.csv)",
    )
    parser.add_argument(
        "--features-out",
        type=Path,
        default=Path("features/features.csv"),
        help="Path to output features CSV (default: features/features.csv)",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("ml/models"),
        help="Directory to store versioned models (default: ml/models)",
    )
    parser.add_argument(
        "--model-alias",
        type=Path,
        default=Path("ml/model_rf.pkl"),
        help="Path to stable model alias used by detect.py (default: ml/model_rf.pkl)",
    )
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=Path("ml/metrics"),
        help="Directory to store timestamped metrics images (default: ml/metrics)",
    )
    parser.add_argument(
        "--train-script",
        type=Path,
        default=Path("ml/train_rf.py"),
        help="Path to training script (default: ml/train_rf.py)",
    )
    parser.add_argument(
        "--n-keep",
        type=int,
        default=10,
        help="Keep latest N model versions, delete older ones (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Generate timestamp (ISO format for manifest, filesystem-safe for filenames)
    now = datetime.now(timezone.utc)
    timestamp_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_fs = now.strftime("%Y%m%d_%H%M%S")

    # Step 1: Safety checks
    check_safety_requirements(
        args.dataset_dir, args.labels, args.train_script, args.dry_run
    )

    # Step 2: Regenerate features
    regenerate_features(
        args.dataset_dir,
        args.labels,
        args.features_out,
        args.dry_run,
        args.verbose,
    )

    # Compute features SHA-256 (after regeneration, or use existing if dry-run)
    if args.dry_run or not args.features_out.exists():
        features_sha256 = "dry-run-sha256"
    else:
        features_sha256 = compute_sha256(args.features_out)

    # Step 3: Retrain model
    model_path, metrics_path, log_path = retrain_model(
        args.features_out,
        args.model_dir,
        args.metrics_dir,
        args.train_script,
        timestamp_fs,
        args.dry_run,
        args.verbose,
    )

    # Step 4: Promote model (update stable alias)
    promote_model(
        model_path,
        metrics_path,
        args.model_alias,
        features_sha256,
        timestamp_fs,
        args.dry_run,
        args.verbose,
    )

    # Step 5: Update manifest
    update_manifest(
        args.model_dir,
        timestamp_iso,
        model_path.name,
        metrics_path.name,
        features_sha256,
        "",  # notes (empty for now)
        args.dry_run,
        args.verbose,
    )

    # Step 6: Cleanup old models
    cleanup_old_models(
        args.model_dir, args.metrics_dir, args.n_keep, args.dry_run, args.verbose
    )

    # Step 7: Print success JSON
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run",
                    "message": "Dry-run completed. No files were modified.",
                },
                indent=2,
            )
        )
    else:
        print(
            json.dumps(
                {
                    "status": "success",
                    "timestamp": timestamp_iso,
                    "model": str(model_path),
                    "alias": str(args.model_alias),
                    "metrics": str(metrics_path),
                    "features_sha256": features_sha256,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()

