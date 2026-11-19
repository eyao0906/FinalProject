from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from stat906cv.plots import make_figures
from stat906cv.statistics import summarize_replications


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate all result tables and figures.")
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    result_dir = args.result_dir.resolve()
    summary = summarize_replications(pd.read_csv(result_dir / "per_replication.csv"))
    summary.to_csv(result_dir / "summary.csv", index=False)
    make_figures(result_dir)


if __name__ == "__main__":
    main()
