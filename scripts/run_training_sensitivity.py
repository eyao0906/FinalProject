from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import t

from stat906cv.experiments import run_experiment


ROOT = Path(__file__).resolve().parents[1]


def _fit_summary(result_dir: Path, fit_index: int) -> pd.DataFrame:
    summary = pd.read_csv(result_dir / "summary.csv")
    summary["training_fit"] = fit_index
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all-scenario training-seed sensitivity study."
    )
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "sensitivity.yaml"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "results" / "training_sensitivity"
    )
    parser.add_argument(
        "--core-results", type=Path, default=ROOT / "results" / "core_20261118"
    )
    args = parser.parse_args()
    config_path = args.config.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    fit_summaries: list[pd.DataFrame] = []
    seed_frames: list[pd.DataFrame] = []
    replication_frames: list[pd.DataFrame] = []
    references: pd.DataFrame | None = None
    for fit_index in range(int(config["training_fits"])):
        fit_config = dict(config)
        fit_config["run_id"] = f"sensitivity_fit_{fit_index}"
        fit_config["base_seed"] = int(config["base_seed"]) + fit_index * 10_007
        fit_dir = output / f"fit_{fit_index:02d}"
        fit_dir.mkdir(parents=True, exist_ok=True)
        fit_config_path = fit_dir / "run_config.yaml"
        fit_config_path.write_text(
            yaml.safe_dump(fit_config, sort_keys=False), encoding="utf-8"
        )
        validation = run_experiment(fit_config_path, fit_dir)
        if not validation["passed"]:
            return 2
        fit_summaries.append(_fit_summary(fit_dir, fit_index))
        seeds = pd.read_csv(fit_dir / "seeds.csv")
        seeds["training_fit"] = fit_index
        seed_frames.append(seeds)
        replications = pd.read_csv(fit_dir / "per_replication.csv")
        replications["training_fit"] = fit_index
        replication_frames.append(replications)
        current_references = pd.read_csv(fit_dir / "reference_prices.csv")
        if references is None:
            references = current_references

    fit_summary = pd.concat(fit_summaries, ignore_index=True)
    fit_summary.to_csv(output / "training_fit_summary.csv", index=False)
    pd.concat(seed_frames, ignore_index=True).to_csv(
        output / "seeds.csv", index=False
    )
    pd.concat(replication_frames, ignore_index=True).to_csv(
        output / "per_replication.csv", index=False
    )
    assert references is not None
    crr = (
        references[
            references["benchmark"] == "same-grid monthly Bermudan CRR"
        ]
        .sort_values("tree_steps")
        .groupby("scenario")["price"]
        .last()
    )
    summary_rows: list[dict[str, object]] = []
    for (scenario, method), group in fit_summary.groupby(
        ["scenario", "method"], sort=True
    ):
        prices = group["mean_price"].to_numpy(dtype=float)
        fit_count = prices.size
        critical = float(t.ppf(0.975, fit_count - 1))
        between_sd = float(np.std(prices, ddof=1))
        between_se = between_sd / np.sqrt(fit_count)
        price_mean = float(np.mean(prices))
        reference = float(crr.get(scenario, np.nan))
        row: dict[str, object] = {
            "scenario": scenario,
            "contract": group["contract"].iloc[0],
            "method": method,
            "training_fits": int(fit_count),
            "pricing_replications_per_fit": int(
                group["replications"].iloc[0]
            ),
            "n_paths": int(group["n_paths"].iloc[0]),
            "mean_price": price_mean,
            "between_fit_price_sd": between_sd,
            "between_fit_price_se": between_se,
            "between_fit_ci_lower": price_mean - critical * between_se,
            "between_fit_ci_upper": price_mean + critical * between_se,
            "mean_within_fit_price_se": float(
                np.mean(group["replicate_sd"] / np.sqrt(group["replications"]))
            ),
            "median_vrf_across_fits": float(group["median_vrf"].median()),
            "mean_vrf_across_fits": float(group["mean_vrf"].mean()),
            "between_fit_vrf_sd": float(
                np.std(group["mean_vrf"].to_numpy(dtype=float), ddof=1)
            ),
            "reference_price": reference,
            "mean_reference_gap": price_mean - reference
            if np.isfinite(reference)
            else float("nan"),
            "mean_relative_reference_gap_percent": (
                100.0 * (price_mean - reference) / reference
                if np.isfinite(reference)
                else float("nan")
            ),
        }
        summary_rows.append(row)
    sensitivity = pd.DataFrame(summary_rows)
    sensitivity.to_csv(output / "sensitivity_summary.csv", index=False)

    original = pd.read_csv(args.core_results.resolve() / "summary.csv")
    original = original[original["n_paths"] == 20000][
        ["scenario", "method", "mean_price", "replicate_ci_lower", "replicate_ci_upper"]
    ].rename(
        columns={
            "mean_price": "original_core_price",
            "replicate_ci_lower": "original_core_ci_lower",
            "replicate_ci_upper": "original_core_ci_upper",
        }
    )
    comparison = sensitivity.merge(original, on=["scenario", "method"])
    comparison["difference_from_original_core"] = (
        comparison["mean_price"] - comparison["original_core_price"]
    )
    comparison["original_inside_sensitivity_ci"] = (
        (comparison["original_core_price"] >= comparison["between_fit_ci_lower"])
        & (comparison["original_core_price"] <= comparison["between_fit_ci_upper"])
    )
    comparison.to_csv(output / "core_stability_comparison.csv", index=False)
    (output / "config_resolved.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    print(sensitivity.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
