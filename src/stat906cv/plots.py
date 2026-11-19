from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


METHOD_LABELS = {
    "plain": "Plain LSMC",
    "linear_cv": "Linear CV",
    "spline_cv": "Spline CV",
}
METHOD_COLORS = {
    "plain": "#4c72b0",
    "linear_cv": "#55a868",
    "spline_cv": "#c44e52",
}
SCENARIO_LABELS = {
    "vanilla_atm_sigma20": "Vanilla ATM, σ=20%",
    "vanilla_atm_sigma40": "Vanilla ATM, σ=40%",
    "vanilla_itm_spot36_sigma20": "Vanilla ITM",
    "vanilla_otm_spot44_sigma20": "Vanilla OTM",
    "asian_put_k95": "Asian K=95",
    "asian_put_k115": "Asian K=115",
}
CONTRACT_LABELS = {
    "vanilla": "Vanilla Bermudan put",
    "asian_arithmetic": "Arithmetic-average Bermudan Asian put",
}


def primary_results(summary: pd.DataFrame) -> pd.DataFrame:
    largest = int(summary["n_paths"].max())
    return summary[summary["n_paths"] == largest].copy()


def volatility_results(summary: pd.DataFrame) -> pd.DataFrame:
    scenarios = ["vanilla_atm_sigma20", "vanilla_atm_sigma40"]
    return summary[
        summary["scenario"].isin(scenarios)
        & summary["method"].isin(("linear_cv", "spline_cv"))
    ].copy()


def moneyness_results(summary: pd.DataFrame) -> pd.DataFrame:
    scenarios = [
        "vanilla_itm_spot36_sigma20",
        "vanilla_atm_sigma20",
        "vanilla_otm_spot44_sigma20",
    ]
    return summary[
        summary["scenario"].isin(scenarios)
        & summary["method"].isin(("linear_cv", "spline_cv"))
    ].copy()


def aggregate_exercise_distribution(
    exercise: pd.DataFrame, scenario: str, n_paths: int
) -> pd.DataFrame:
    subset = exercise[
        (exercise["scenario"] == scenario) & (exercise["n_paths"] == n_paths)
    ].sort_values(["time_index", "replicate"])
    return (
        subset.groupby("time_index", sort=True)
        .agg(
            time=("time", "first"),
            contract=("contract", "first"),
            probability=("frequency", "mean"),
            replication_se=(
                "frequency",
                lambda values: values.std(ddof=1) / np.sqrt(values.size)
                if values.size > 1
                else 0.0,
            ),
        )
        .reset_index()
    )


def make_figures(result_dir: Path) -> None:
    result_dir = Path(result_dir)
    figure_dir = result_dir / "figures"
    table_dir = result_dir / "tables"
    figure_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(result_dir / "summary.csv")
    replications = pd.read_csv(result_dir / "per_replication.csv")
    references = pd.read_csv(result_dir / "reference_prices.csv")
    exercise = pd.read_csv(result_dir / "exercise_diagnostics.csv")
    _set_style()

    summary[
        [
            "scenario",
            "contract",
            "n_paths",
            "method",
            "mean_price",
            "replicate_ci_lower",
            "replicate_ci_upper",
        ]
    ].to_csv(table_dir / "estimator_summary.csv", index=False)
    summary[
        [
            "scenario",
            "contract",
            "n_paths",
            "method",
            "mean_vrf",
            "median_vrf",
            "vrf_replicate_sd",
        ]
    ].to_csv(table_dir / "variance_reduction.csv", index=False)

    _plot_vrf_main(primary_results(summary), table_dir, figure_dir)
    _plot_vrf_sensitivity(summary, table_dir, figure_dir)
    _plot_price_facets(
        primary_results(summary), references, table_dir, figure_dir
    )
    _plot_cpu_efficiency(primary_results(summary), table_dir, figure_dir)
    _plot_exercise_distributions(exercise, table_dir, figure_dir)
    _plot_martingale_corrections(result_dir, replications, table_dir, figure_dir)


def _plot_vrf_main(
    summary: pd.DataFrame, table_dir: Path, figure_dir: Path
) -> None:
    data = summary[summary["method"].isin(("linear_cv", "spline_cv"))].copy()
    data["scenario_label"] = data["scenario"].map(SCENARIO_LABELS)
    data.to_csv(table_dir / "vrf_main_presentation.csv", index=False)
    scenarios = [item for item in SCENARIO_LABELS if item in set(data["scenario"])]
    fig, axis = plt.subplots(figsize=(12, 6.2))
    x = np.arange(len(scenarios))
    width = 0.36
    for offset, method in ((-width / 2, "linear_cv"), (width / 2, "spline_cv")):
        values = data[data["method"].eq(method)].set_index("scenario")[
            "median_vrf"
        ].reindex(scenarios)
        bars = axis.bar(
            x + offset,
            values.to_numpy(dtype=float),
            width,
            label=METHOD_LABELS[method],
            color=METHOD_COLORS[method],
        )
        _annotate_bars(axis, bars, "{:.1f}×")
    axis.axhline(1.0, color="#222222", linestyle="--", linewidth=1)
    axis.set_yscale("log")
    axis.set_ylim(bottom=0.8)
    axis.set_xticks(x, [SCENARIO_LABELS[item] for item in scenarios], rotation=20)
    axis.set_ylabel("Median variance-reduction factor (VRF, ×)")
    axis.set_title(
        f"Scenario-level variance reduction at N={int(data['n_paths'].iloc[0]):,}"
    )
    axis.text(
        0.0,
        -0.22,
        f"Median across {int(data['replications'].iloc[0])} independent pricing "
        "replications; VRF = Var(Y) / Var(Y − Mτ).",
        transform=axis.transAxes,
        fontsize=9,
        color="#555555",
    )
    axis.legend(frameon=False, ncol=2, loc="upper right")
    axis.axvspan(-0.5, 3.5, color="#f2f2f2", zorder=-1)
    fig.tight_layout()
    _save(fig, figure_dir, "vrf_asian_vs_vanilla")


def _plot_vrf_sensitivity(
    summary: pd.DataFrame, table_dir: Path, figure_dir: Path
) -> None:
    panels = [
        ("Volatility: ATM (S₀=K=40)", volatility_results(summary), [
            "vanilla_atm_sigma20",
            "vanilla_atm_sigma40",
        ]),
        ("Moneyness: K=40, σ=20%", moneyness_results(summary), [
            "vanilla_itm_spot36_sigma20",
            "vanilla_atm_sigma20",
            "vanilla_otm_spot44_sigma20",
        ]),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), sharey=True)
    combined: list[pd.DataFrame] = []
    for axis, (title, data, scenarios) in zip(axes, panels):
        combined.append(data)
        x = np.arange(len(scenarios))
        slots = [
            ("linear_cv", 5000),
            ("linear_cv", 20000),
            ("spline_cv", 5000),
            ("spline_cv", 20000),
        ]
        width = 0.18
        for index, (method, n_paths) in enumerate(slots):
            values = (
                data[
                    (data["method"] == method) & (data["n_paths"] == n_paths)
                ]
                .set_index("scenario")["median_vrf"]
                .reindex(scenarios)
            )
            bars = axis.bar(
                x + (index - 1.5) * width,
                values.to_numpy(dtype=float),
                width,
                label=f"{METHOD_LABELS[method]}, N={n_paths:,}",
                color=METHOD_COLORS[method],
                alpha=0.45 if n_paths == 5000 else 0.95,
            )
            _annotate_bars(axis, bars, "{:.0f}×", fontsize=7)
        axis.axhline(1.0, color="#222222", linestyle="--", linewidth=1)
        axis.set_yscale("log")
        axis.set_ylim(bottom=0.8)
        axis.set_title(title)
        labels = (
            ["ATM σ=20%", "ATM σ=40%"]
            if "Volatility" in title
            else ["ITM S₀=36", "ATM S₀=40", "OTM S₀=44"]
        )
        axis.set_xticks(x, labels)
        axis.tick_params(axis="x", rotation=15)
    axes[0].set_ylabel("Median variance-reduction factor (×)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle(
        "Spline and linear control effectiveness by volatility and moneyness"
    )
    fig.tight_layout(rect=(0, 0.12, 1, 0.96))
    pd.concat(combined, ignore_index=True).to_csv(
        table_dir / "vrf_sensitivity_presentation.csv", index=False
    )
    _save(fig, figure_dir, "vrf_vanilla_by_size_volatility")


def _plot_price_facets(
    summary: pd.DataFrame,
    references: pd.DataFrame,
    table_dir: Path,
    figure_dir: Path,
) -> None:
    methods = ("plain", "linear_cv", "spline_cv")
    data = summary[summary["method"].isin(methods)].copy()
    data["scenario_label"] = data["scenario"].map(SCENARIO_LABELS)
    data.to_csv(table_dir / "price_facets_presentation.csv", index=False)
    crr = (
        references[
            references["benchmark"] == "same-grid monthly Bermudan CRR"
        ]
        .sort_values("tree_steps")
        .groupby("scenario")["price"]
        .last()
    )
    scenarios = [item for item in SCENARIO_LABELS if item in set(data["scenario"])]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for axis, scenario in zip(axes.ravel(), scenarios):
        subset = data[data["scenario"] == scenario].set_index("method")
        y = np.arange(len(methods))[::-1]
        for position, method in zip(y, methods):
            row = subset.loc[method]
            half_low = float(row["mean_price"] - row["replicate_ci_lower"])
            half_high = float(row["replicate_ci_upper"] - row["mean_price"])
            axis.errorbar(
                row["mean_price"],
                position,
                xerr=np.array([[half_low], [half_high]]),
                fmt="o",
                color=METHOD_COLORS[method],
                ecolor=METHOD_COLORS[method],
                capsize=4,
                markersize=6,
                label=METHOD_LABELS[method],
            )
        if scenario in crr.index:
            axis.axvline(
                float(crr.loc[scenario]),
                color="#222222",
                linestyle="--",
                linewidth=1.2,
                label="Matched Bermudan CRR",
            )
        axis.set_yticks(y, [METHOD_LABELS[item] for item in methods])
        axis.set_xlabel("Fixed-policy value (currency units)")
        axis.set_title(SCENARIO_LABELS[scenario], fontsize=11)
        axis.grid(axis="x", alpha=0.25)
    handles, labels = axes.ravel()[0].get_legend_handles_labels()
    crr_handle = next(
        (
            line
            for line in axes.ravel()[0].lines
            if line.get_label() == "Matched Bermudan CRR"
        ),
        None,
    )
    if crr_handle is not None:
        handles.append(crr_handle)
        labels.append("Matched Bermudan CRR")
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle(
        f"Fixed-policy price estimates at N={int(data['n_paths'].iloc[0]):,}: "
        f"95% Student-t intervals across {int(data['replications'].iloc[0])} "
        "independent pricing replications"
    )
    fig.text(
        0.5,
        0.055,
        "Intervals are conditional on the single frozen policy/value training fit; "
        "they do not quantify training uncertainty or policy approximation error.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.09, 1, 0.95))
    _save(fig, figure_dir, "price_confidence_intervals")


def _plot_cpu_efficiency(
    summary: pd.DataFrame, table_dir: Path, figure_dir: Path
) -> None:
    data = summary[summary["method"].isin(("linear_cv", "spline_cv"))].copy()
    data.to_csv(table_dir / "cpu_efficiency_presentation.csv", index=False)
    scenarios = [item for item in SCENARIO_LABELS if item in set(data["scenario"])]
    x = np.arange(len(scenarios))
    fig, axis = plt.subplots(figsize=(12, 6.2))
    width = 0.36
    for offset, method in ((-width / 2, "linear_cv"), (width / 2, "spline_cv")):
        rows = data[data["method"].eq(method)].set_index("scenario").reindex(
            scenarios
        )
        values = rows["aggregate_cpu_adjusted_efficiency"].to_numpy(dtype=float)
        bars = axis.bar(
            x + offset,
            np.where(np.isfinite(values), values, np.nan),
            width,
            label=METHOD_LABELS[method],
            color=METHOD_COLORS[method],
        )
        for bar, value, status in zip(
            bars, values, rows["cpu_efficiency_timing_status"]
        ):
            if np.isfinite(value):
                axis.annotate(
                    f"{value:.2f}×",
                    (bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
            else:
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    1.05,
                    "N/A",
                    ha="center",
                    va="bottom",
                    rotation=90,
                    fontsize=8,
                )
    axis.axhline(1.0, color="#222222", linestyle="--", linewidth=1)
    axis.set_yscale("log")
    axis.set_ylim(bottom=0.8)
    axis.set_xticks(x, [SCENARIO_LABELS[item] for item in scenarios], rotation=20)
    axis.set_ylabel("Aggregate CPU-adjusted efficiency relative to plain LSMC (×)")
    axis.set_title(
        f"Scenario-level computational efficiency at N={int(data['n_paths'].iloc[0]):,}"
    )
    axis.legend(frameon=False, ncol=2)
    fig.text(
        0.5,
        0.015,
        "Ratio = Σ Var(Yᵢ)CPU_plain,ᵢ / Σ Var(Ycv,ᵢ)CPU_cv,ᵢ; CPU includes "
        "allocated training costs. Windows timings are hardware-specific and "
        "approximate; N/A means the 0.05 s aggregate reliability floor was not met.",
        ha="center",
        fontsize=8.5,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    _save(fig, figure_dir, "standard_error_vs_cpu")


def _plot_exercise_distributions(
    exercise: pd.DataFrame, table_dir: Path, figure_dir: Path
) -> None:
    n_paths = int(exercise["n_paths"].max())
    replication_count = int(exercise["replicate"].nunique())
    scenarios = [item for item in SCENARIO_LABELS if item in set(exercise["scenario"])]
    distributions = []
    for scenario in scenarios:
        distribution = aggregate_exercise_distribution(exercise, scenario, n_paths)
        distribution["scenario"] = scenario
        distributions.append(distribution)
    distribution_table = pd.concat(distributions, ignore_index=True)
    distribution_table.to_csv(
        table_dir / "exercise_distribution_presentation.csv", index=False
    )
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for axis, scenario in zip(axes.ravel(), scenarios):
        data = distribution_table[distribution_table["scenario"] == scenario]
        maturity = int(data["time_index"].max())
        colors = [
            "#d62728" if time_index == maturity else METHOD_COLORS["plain"]
            for time_index in data["time_index"]
        ]
        spacing = float(data["time"].diff().dropna().min())
        axis.bar(
            data["time"],
            data["probability"],
            width=spacing * 0.75,
            yerr=1.96 * data["replication_se"],
            capsize=2,
            color=colors,
            linewidth=0.5,
        )
        axis.yaxis.set_major_formatter(PercentFormatter(1.0))
        axis.set_title(SCENARIO_LABELS[scenario], fontsize=11)
        axis.set_xlabel("Exercise time (years)")
        axis.set_ylabel("Probability")
        maturity_probability = float(
            data.loc[data["time_index"] == maturity, "probability"].iloc[0]
        )
        first_time = float(data.loc[data["time_index"] == data["time_index"].min(), "time"].iloc[0])
        eligibility = "initial exercise eligible" if first_time == 0 else "exercise begins at month 1"
        axis.text(
            0.03,
            0.95,
            f"Maturity: {maturity_probability:.1%}",
            transform=axis.transAxes,
            va="top",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8},
        )
        axis.text(
            0.03,
            0.06,
            eligibility,
            transform=axis.transAxes,
            fontsize=8,
            color="#555555",
        )
    fig.suptitle(
        f"Exercise-time distributions of the fitted LSM policy "
        f"(N={n_paths:,}; mean ± 95% replicate error bars across "
        f"{replication_count} replications)"
    )
    fig.text(
        0.5,
        0.015,
        "Red bars identify the contractual maturity stopping date. These are "
        "fitted-policy stopping times, not the unknown optimal exercise policy.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    _save(fig, figure_dir, "exercise_time_histograms")


def _plot_martingale_corrections(
    result_dir: Path,
    replications: pd.DataFrame,
    table_dir: Path,
    figure_dir: Path,
) -> None:
    archive_path = result_dir / "representative_paths.npz"
    if not archive_path.exists():
        return
    archive = np.load(archive_path)
    for contract, prefix in (("vanilla", "vanilla"), ("asian_arithmetic", "asian")):
        key = next(
            (name for name in archive.files if name.startswith(prefix + "_Y_")),
            None,
        )
        if key is None:
            continue
        scenario = key.removeprefix(prefix + "_Y_")
        source_n = int(
            replications.loc[
                replications["scenario"] == scenario, "n_paths"
            ].min()
        )
        y = np.asarray(archive[key], dtype=float)
        correction = np.asarray(archive[prefix + "_M_spline_" + scenario], dtype=float)
        adjusted = np.asarray(archive[prefix + "_Ycv_spline_" + scenario], dtype=float)
        sample_n = y.size
        data = pd.DataFrame(
            {
                "plain_payoff": y,
                "M_tau": correction,
                "spline_cv_payoff": adjusted,
            }
        )
        table_name = f"martingale_correction_{contract}.csv"
        data.to_csv(table_dir / table_name, index=False)
        correlation = float(np.corrcoef(y, correction)[0, 1])
        sd_before = float(np.std(y, ddof=1))
        sd_after = float(np.std(adjusted, ddof=1))
        vrf = sd_before**2 / sd_after**2
        all_values = np.concatenate((y, adjusted))
        bins = np.linspace(
            float(np.min(all_values)),
            float(np.max(all_values)),
            35,
        )
        fig = plt.figure(figsize=(14, 4.8))
        grid = fig.add_gridspec(1, 3, width_ratios=(1.25, 1, 1))
        scatter = fig.add_subplot(grid[0, 0])
        before = fig.add_subplot(grid[0, 1])
        after = fig.add_subplot(grid[0, 2], sharex=before, sharey=before)
        scatter.scatter(
            y,
            correction,
            s=14,
            alpha=0.42,
            color=METHOD_COLORS["spline_cv"],
            edgecolors="none",
        )
        scatter.axhline(0, color="#777777", linewidth=0.8)
        scatter.set_xlabel("Discounted policy payoff Y")
        scatter.set_ylabel("Stopped martingale Mτ")
        scatter.set_title("A. Payoff–correction relationship")
        scatter.text(
            0.04,
            0.95,
            f"corr(Y, Mτ) = {correlation:.3f}",
            transform=scatter.transAxes,
            va="top",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8},
        )
        before.hist(
            y,
            bins=bins,
            color=METHOD_COLORS["plain"],
            alpha=0.9,
        )
        before.set_title("B. Plain discounted payoff")
        before.set_xlabel("Estimator value")
        before.set_ylabel("Path count")
        before.text(
            0.96,
            0.95,
            f"sample SD = {sd_before:.4f}",
            transform=before.transAxes,
            ha="right",
            va="top",
        )
        after.hist(
            adjusted,
            bins=bins,
            color=METHOD_COLORS["spline_cv"],
            alpha=0.9,
        )
        after.set_title("C. Spline-CV adjusted payoff")
        after.set_xlabel("Estimator value")
        after.text(
            0.96,
            0.95,
            f"sample SD = {sd_after:.4f}\nVRF = {vrf:.1f}×",
            transform=after.transAxes,
            ha="right",
            va="top",
        )
        fig.suptitle(
            f"{SCENARIO_LABELS.get(scenario, scenario)}: how the martingale "
            f"tracks and reduces payoff fluctuations"
        )
        fig.text(
            0.5,
            0.012,
            f"Illustrative representative sample of {sample_n} paths from "
            f"replication 0 of the saved N={source_n:,} experiment archive; VRF is computed from "
            "this plotted sample, not inferred from a different run.",
            ha="center",
            fontsize=8.5,
            color="#555555",
        )
        fig.tight_layout(rect=(0, 0.05, 1, 0.95))
        _save(fig, figure_dir, f"martingale_correction_{contract}")


def _annotate_bars(
    axis: plt.Axes, bars, template: str = "{:.1f}", fontsize: int = 8
) -> None:
    for bar in bars:
        value = bar.get_height()
        if not np.isfinite(value):
            continue
        axis.annotate(
            template.format(value),
            (bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=fontsize,
        )


def _set_style() -> None:
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "grid.color": "#d9d9d9",
            "grid.linewidth": 0.6,
        }
    )


def _save(fig: plt.Figure, directory: Path, name: str) -> None:
    fig.savefig(directory / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(directory / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
