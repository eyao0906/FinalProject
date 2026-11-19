from __future__ import annotations

import argparse
import json
import subprocess
from io import StringIO
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILES = (
    "results/core_20261118/per_replication.csv",
    "results/core_20261118/summary.csv",
    "results/core_20261118/reference_prices.csv",
    "results/core_20261118/seeds.csv",
    "results/core_20261118/exercise_diagnostics.csv",
)


def _reference_bytes(reference_ref: str, relative_path: str) -> bytes:
    process = subprocess.run(
        ["git", "show", f"{reference_ref}:{relative_path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Cannot read {relative_path} from {reference_ref}: "
            f"{process.stderr.decode(errors='replace')}"
        )
    return process.stdout


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare core numerical CSVs with the original committed source."
    )
    parser.add_argument("--reference-ref", default="main")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "numerical_integrity.json",
    )
    args = parser.parse_args()
    results: list[dict[str, object]] = []
    for relative_path in DEFAULT_FILES:
        reference = pd.read_csv(
            StringIO(_reference_bytes(args.reference_ref, relative_path).decode("utf-8"))
        )
        current = pd.read_csv(ROOT / relative_path)
        same_shape = reference.shape == current.shape
        changed_columns: list[str] = []
        if same_shape:
            for column in reference.columns:
                left = reference[column]
                right = current[column]
                equal = left.equals(right)
                if not equal and pd.api.types.is_numeric_dtype(left):
                    equal = bool(
                        ((left.fillna(0) - right.fillna(0)).abs() <= 1e-12).all()
                        and (left.isna() == right.isna()).all()
                    )
                if not equal:
                    changed_columns.append(column)
        results.append(
            {
                "file": relative_path,
                "reference_shape": list(reference.shape),
                "current_shape": list(current.shape),
                "unchanged": same_shape and not changed_columns,
                "changed_columns": changed_columns,
            }
        )
    report = {
        "reference_ref": args.reference_ref,
        "all_numerical_outputs_unchanged": all(
            bool(row["unchanged"]) for row in results
        ),
        "files": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_numerical_outputs_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
