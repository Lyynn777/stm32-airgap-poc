from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd


SYSCALL_KEYWORDS = {
    "open_count": ["open"],
    "read_count": ["read"],
    "write_count": ["write"],
    "execve_count": ["execve"],
    "connect_count": ["connect"],
    "fork_count": ["fork"],
    "clone_count": ["clone"],
}

# Include both creation-centric keywords and the explicitly requested
# unlink/remove/deleted tokens to satisfy the requirements.
CREATED_KEYWORDS = [
    "create",
    "creat",
    "mkdir",
    "mknod",
    "mkfifo",
    "link",
    "symlink",
    "touch",
    "unlink",
    "remove",
    "deleted",
]

DELETED_KEYWORDS = [
    "unlink",
    "remove",
    "deleted",
    "unlinkat",
    "rmdir",
]


def parse_strace_file(path: Path) -> Dict[str, int]:
    counts = {
        "open_count": 0,
        "read_count": 0,
        "write_count": 0,
        "execve_count": 0,
        "connect_count": 0,
        "fork_count": 0,
        "clone_count": 0,
        "created_count": 0,
        "deleted_count": 0,
    }

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            line_lower = line.lower()

            for key, keywords in SYSCALL_KEYWORDS.items():
                if any(keyword in line_lower for keyword in keywords):
                    counts[key] += 1

            if any(keyword in line_lower for keyword in CREATED_KEYWORDS):
                counts["created_count"] += 1

            if any(keyword in line_lower for keyword in DELETED_KEYWORDS):
                counts["deleted_count"] += 1

    counts["new_process_count"] = counts["fork_count"] + counts["clone_count"]
    return counts


def load_labels(path: Path) -> Dict[str, str]:
    labels: Dict[str, str] = {}

    with path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if reader.fieldnames is None or set(reader.fieldnames) != {"id", "label"}:
            raise ValueError("labels.csv must contain 'id' and 'label' headers.")
        for row in reader:
            row_id = row["id"].strip()
            label = row["label"].strip()
            if not row_id or not label:
                raise ValueError("Label rows cannot have empty id or label values.")
            labels[row_id] = label
    return labels


def extract_features(input_dir: Path, labels_path: Path) -> pd.DataFrame:
    labels = load_labels(labels_path)
    records: List[Dict[str, int | str]] = []

    strace_files = sorted(input_dir.rglob("*.strace"))
    if not strace_files:
        raise FileNotFoundError(
            f"No .strace files found under '{input_dir.as_posix()}'."
        )

    for strace_file in strace_files:
        file_id = strace_file.stem
        if file_id not in labels:
            raise KeyError(f"No label found for '{file_id}' in labels CSV.")

        counts = parse_strace_file(strace_file)
        counts["id"] = file_id
        counts["label"] = labels[file_id]
        records.append(counts)

    df = pd.DataFrame.from_records(records)
    ordered_columns = [
        "id",
        "label",
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
    df = df[ordered_columns].sort_values("id").reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract syscall-based features from strace logs."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Path to the dataset directory containing .strace files.",
    )
    parser.add_argument(
        "--labels",
        required=True,
        type=Path,
        help="Path to labels.csv file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path where the features CSV will be written.",
    )

    args = parser.parse_args()

    input_dir: Path = args.input_dir
    labels_path: Path = args.labels
    output_path: Path = args.output

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file '{labels_path}' does not exist.")

    df = extract_features(input_dir, labels_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
