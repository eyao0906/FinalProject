from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


METHOD_LABELS = {
    "plain": "Plain LSMC",
    "linear_cv": "Linear martingale CV",
    "spline_cv": "Additive spline martingale CV",
}


def make_figures(result_dir: Path) -> None:
    result_dir = Path(result_dir)
    figure_dir = result_dir / "figures"
    table_dir = result_dir / "tables"
    figure_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(result_dir / "summary.csv")
    replications = pd.read_csv(result_dir / "per_replication.csv")

    price_table = summary[
        ["scenario", "contract", "n_paths", "method", "mean_price", "replicate_ci_lower", "replicate_ci_upper"]
    ]
    price_table.to_csv(table_dir / "estimator_summary.csv", index=False)
    vrf_table = summary[
        ["scenario", "contract", "n_paths", "method", "mean_vrf", "median_vrf", "vrf_replicate_sd"]
    ]
    vrf_table.to_csv(table_dir / "variance_reduction.csv", index=False)

    fig, axis = plt.subplots(figsize=(11, 6))
    for method, group in summary.groupby("method", sort=False):
        x = np.arange(len(group))
        axis.errorbar(
            x,
            group["mean_price"],
            yerr=[
                group["mean_price"] - group["replicate_ci_lower"],
                group["replicate_ci_upper"] - group["mean_price"],
            ],
            marker="o",
            capsize=3,
            linestyle="none",
            label=METHOD_LABELS.get(method, method),
        )
    labels = [f"{row.scenario}\nN={row.n_paths}" for row in summary.drop_duplicates(["scenario", "n_paths"]).itertuples()]
    axis.set_xticks(np.arange(len(labels)), labels, rotation=35, ha="right")
    axis.set_ylabel("Policy-value estimate (currency units)")
    axis.set_title("Paired estimators: mean and 95% t interval across replications")
    axis.legend()
    fig.tight_layout()
    _save(fig, figure_dir, "price_confidence_intervals")

    vanilla = summary[summary["contract"] == "vanilla"]
    fig, axis = plt.subplots(figsize=(8, 5))
    for method in ("linear_cv", "spline_cv"):
        subset = vanilla[vanilla["method"] == method]
        for sigma, sigma_group in subset.groupby("volatility"):
            axis.plot(
                sigma_group["n_paths"],
                sigma_group["median_vrf"],
                marker="o",
                label=f"{METHOD_LABELS[method]}, sigma={sigma:g}",
            )
    axis.axhline(1.0, color="black", linewidth=1, linestyle="--")
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Pricing paths N")
    axis.set_ylabel("Median variance-reduction factor")
    axis.set_title("Vanilla put VRF by pricing size and volatility")
    axis.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, figure_dir, "vrf_vanilla_by_size_volatility")

    cross = summary[summary["method"].isin(("linear_cv", "spline_cv"))]
    cross_table = cross.pivot_table(
        index=["contract", "scenario", "n_paths"], columns="method", values="median_vrf"
    ).reset_index()
    cross_table.to_csv(table_dir / "asian_vs_vanilla_vrf.csv", index=False)
    fig, axis = plt.subplots(figsize=(9, 5))
    for (contract, method), group in cross.groupby(["contract", "method"]):
        axis.scatter(
            group["n_paths"],
            group["median_vrf"],
            label=f"{contract}: {METHOD_LABELS[method]}",
            alpha=0.8,
        )
    axis.axhline(1.0, color="black", linewidth=1, linestyle="--")
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Pricing paths N")
    axis.set_ylabel("Median variance-reduction factor")
    axis.set_title("Variance reduction across the two contract classes")
    axis.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, figure_dir, "vrf_asian_vs_vanilla")

    cv_summary = summary[summary["method"].isin(("plain", "linear_cv", "spline_cv"))]
    fig, axis = plt.subplots(figsize=(8, 5))
    for method, group in cv_summary.groupby("method", sort=False):
        axis.scatter(
            group["mean_total_cpu_seconds"],
            group["mean_path_se"],
            label=METHOD_LABELS.get(method, method),
            alpha=0.8,
        )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Allocated total CPU seconds per replication")
    axis.set_ylabel("Mean per-path estimator standard error")
    axis.set_title("Sampling error versus amortized computational cost")
    axis.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, figure_dir, "standard_error_vs_cpu")

    exercise = pd.read_csv(result_dir / "exercise_diagnostics.csv")
    representative = exercise[exercise["replicate"] == exercise["replicate"].min()]
    scenario_ids = representative["scenario"].drop_duplicates().tolist()
    examples = []
    for contract in ("vanilla", "asian_arithmetic"):
        candidates = [
            row for row in scenario_ids
            if representative.loc[representative["scenario"] == row, "contract"].iloc[0] == contract
        ]
        if candidates:
            examples.append(candidates[0])
    fig, axes = plt.subplots(1, max(len(examples), 1), figsize=(6 * max(len(examples), 1), 4))
    axes = np.atleast_1d(axes)
    for axis, scenario in zip(axes, examples):
        subset = representative[
            (representative["scenario"] == scenario)
            & (representative["n_paths"] == representative.loc[representative["scenario"] == scenario, "n_paths"].min())
        ]
        axis.bar(subset["time_index"], subset["frequency"])
        axis.set_xlabel("Exercise date index")
        axis.set_ylabel("Exercise probability")
        axis.set_title(scenario)
    fig.suptitle("Representative frozen-policy exercise-time distributions")
    fig.tight_layout()
    _save(fig, figure_dir, "exercise_time_histograms")

    archive_path = result_dir / "representative_paths.npz"
    if archive_path.exists():
        archive = np.load(archive_path)
        for contract, prefix in (("vanilla", "vanilla"), ("asian_arithmetic", "asian")):
            key = next(
                (name for name in archive.files if name.startswith(prefix + "_Y_")),
                None,
            )
            if key is None:
                continue
            scenario = key.removeprefix(prefix + "_Y_")
            y = archive[key]
            correction = archive[prefix + "_M_spline_" + scenario]
            adjusted = archive[prefix + "_Ycv_spline_" + scenario]
            pd.DataFrame(
                {"plain_payoff": y, "M_tau": correction, "spline_cv_payoff": adjusted}
            ).to_csv(table_dir / f"martingale_correction_{contract}.csv", index=False)
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            axes[0].scatter(y, correction, s=8, alpha=0.35)
            axes[0].set_xlabel("Discounted policy payoff Y")
            axes[0].set_ylabel("Stopped martingale M_tau")
            axes[0].set_title(f"{scenario}: payoff and correction")
            axes[1].hist(y, bins=40, alpha=0.55, label="Y")
            axes[1].hist(adjusted, bins=40, alpha=0.55, label="Y - M_tau")
            axes[1].set_xlabel("Pathwise discounted estimator")
            axes[1].set_ylabel("Count")
            axes[1].legend()
            fig.tight_layout()
            _save(fig, figure_dir, f"martingale_correction_{contract}")


def _save(fig: plt.Figure, directory: Path, name: str) -> None:
    fig.savefig(directory / f"{name}.png", dpi=220)
    fig.savefig(directory / f"{name}.pdf")
    plt.close(fig)
