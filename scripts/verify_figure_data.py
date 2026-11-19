from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from stat906cv.plots import aggregate_exercise_distribution, primary_results


def _equal(left: pd.DataFrame, right: pd.DataFrame, keys: list[str], values: list[str]) -> bool:
    lhs = left.sort_values(keys).reset_index(drop=True)[keys + values]
    rhs = right.sort_values(keys).reset_index(drop=True)[keys + values]
    return lhs.shape == rhs.shape and all(
        np.allclose(
            lhs[column].to_numpy(dtype=float),
            rhs[column].to_numpy(dtype=float),
            rtol=1e-12,
            atol=1e-12,
            equal_nan=True,
        )
        if pd.api.types.is_numeric_dtype(lhs[column])
        else lhs[column].astype(str).equals(rhs[column].astype(str))
        for column in lhs.columns
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify presentation tables against saved experiment data."
    )
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result_dir = args.result_dir.resolve()
    summary = pd.read_csv(result_dir / "summary.csv")
    exercise = pd.read_csv(result_dir / "exercise_diagnostics.csv")
    expected_primary = primary_results(summary)
    table_dir = result_dir / "tables"
    checks: list[dict[str, object]] = []
    for table, methods, values in (
        (
            "vrf_main_presentation.csv",
            ("linear_cv", "spline_cv"),
            ["median_vrf"],
        ),
        (
            "price_facets_presentation.csv",
            ("plain", "linear_cv", "spline_cv"),
            ["mean_price", "replicate_ci_lower", "replicate_ci_upper"],
        ),
        (
            "cpu_efficiency_presentation.csv",
            ("linear_cv", "spline_cv"),
            ["aggregate_cpu_adjusted_efficiency"],
        ),
    ):
        expected = expected_primary[expected_primary["method"].isin(methods)]
        actual = pd.read_csv(table_dir / table)
        checks.append(
            {
                "table": table,
                "passed": _equal(
                    actual, expected, ["scenario", "method"], values
                ),
            }
        )

    n_paths = int(exercise["n_paths"].max())
    expected_exercise = pd.concat(
        [
            aggregate_exercise_distribution(exercise, scenario, n_paths).assign(
                scenario=scenario
            )
            for scenario in exercise["scenario"].drop_duplicates()
        ],
        ignore_index=True,
    )
    actual_exercise = pd.read_csv(
        table_dir / "exercise_distribution_presentation.csv"
    )
    checks.append(
        {
            "table": "exercise_distribution_presentation.csv",
            "passed": _equal(
                actual_exercise,
                expected_exercise,
                ["scenario", "time_index"],
                ["time", "probability", "replication_se"],
            ),
        }
    )
    passed = all(bool(check["passed"]) for check in checks)
    report = {"result_dir": str(result_dir), "passed": passed, "checks": checks}
    output = args.output or result_dir / "figure_data_integrity.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
