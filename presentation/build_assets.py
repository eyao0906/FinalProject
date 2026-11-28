from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "core_20261118"
OUT = Path(__file__).resolve().parent / "assets"
IVORY = "#FDF6E3"
CHARCOAL = "#2B2B2B"
BLUE = "#2E6F95"
CORAL = "#C65D62"
GOLD = "#D49B35"


def load_summary():
    summary = pd.read_csv(RESULTS / "summary.csv")
    required = {
        "scenario",
        "n_paths",
        "method",
        "mean_price",
        "replicate_ci_lower",
        "replicate_ci_upper",
        "median_vrf",
        "aggregate_cpu_adjusted_efficiency",
    }
    if not required.issubset(summary.columns):
        raise ValueError(f"summary.csv is missing columns: {sorted(required - set(summary.columns))}")
    return summary


def unique_row(frame, **filters):
    match = frame
    for column, value in filters.items():
        match = match[match[column] == value]
    if len(match) != 1:
        raise ValueError(f"Expected one saved row for {filters}, found {len(match)}")
    return match.iloc[0]


def finish(fig, filename):
    fig.savefig(OUT / filename, dpi=220, facecolor=IVORY, bbox_inches="tight")
    plt.close(fig)


def make_control_shapes():
    x = pd.Series([0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8])
    linear = 4.1 - 1.8 * x
    spline = pd.Series([4.1, 3.35, 2.45, 1.75, 1.1, 0.55, 0.22])
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.0), sharey=True)
    for ax, y, title, color in (
        (axes[0], linear, "Linear control", BLUE),
        (axes[1], spline, "Piecewise-linear hinges", CORAL),
    ):
        ax.plot(x, y, color=color, linewidth=3)
        ax.set_title(title, color=CHARCOAL, fontsize=15, pad=12)
        ax.set_xlabel("State coordinate", color=CHARCOAL)
        ax.grid(axis="y", alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Approximate value $h(x)$", color=CHARCOAL)
    axes[1].scatter([2.0, 4.0], [1.8, 3.55], color=GOLD, zorder=3, s=42)
    fig.patch.set_facecolor(IVORY)
    finish(fig, "control_shapes.png")


def make_main_vrf(summary):
    scenarios = [
        ("vanilla_atm_sigma20", "Vanilla ATM, 20%"),
        ("vanilla_atm_sigma40", "Vanilla ATM, 40%"),
        ("vanilla_itm_spot36_sigma20", "Vanilla ITM, $S_0=36$"),
        ("vanilla_otm_spot44_sigma20", "Vanilla OTM, $S_0=44$"),
        ("asian_put_k95", "Asian, $K=95$"),
        ("asian_put_k115", "Asian, $K=115$"),
    ]
    methods = [("linear_cv", "Linear", BLUE, -0.13), ("spline_cv", "Spline", CORAL, 0.13)]
    fig, ax = plt.subplots(figsize=(8.4, 4.5))
    for method, label, color, offset in methods:
        values = [
            float(unique_row(summary, scenario=scenario, n_paths=20000, method=method)["median_vrf"])
            for scenario, _ in scenarios
        ]
        y = [i + offset for i in range(len(scenarios))]
        ax.scatter(values, y, color=color, label=label, s=62, zorder=3)
        for value, yi in zip(values, y):
            ax.annotate(f"{value:.2f}", (value, yi), xytext=(6, 0), textcoords="offset points", va="center", fontsize=9)
    ax.axvline(1, color=CHARCOAL, linestyle="--", linewidth=1.1, alpha=0.65)
    ax.set_xscale("log")
    ax.set_yticks(range(len(scenarios)), [label for _, label in scenarios])
    ax.invert_yaxis()
    ax.set_xlabel("Median variance-reduction factor (log scale)", color=CHARCOAL)
    ax.set_title("Blue = linear · coral = spline · 30 paired replications · 20,000 paths", color=CHARCOAL, fontsize=13, pad=12)
    ax.grid(axis="x", which="both", alpha=0.22)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.patch.set_facecolor(IVORY)
    finish(fig, "vrf_main.png")


def make_atm_price(summary):
    scenario = "vanilla_atm_sigma20"
    rows = [
        unique_row(summary, scenario=scenario, n_paths=20000, method=method)
        for method in ("plain", "spline_cv")
    ]
    references = pd.read_csv(RESULTS / "reference_prices.csv")
    crr = references[
        (references["scenario"] == scenario)
        & (references["benchmark"] == "same-grid monthly Bermudan CRR")
        & (references["tree_steps"] == 2400)
    ]
    if len(crr) != 1:
        raise ValueError(f"Expected one 2,400-step monthly Bermudan reference, found {len(crr)}")
    crr_price = float(crr.iloc[0]["price"])

    fig, ax = plt.subplots(figsize=(8.1, 3.4))
    labels = ["Plain LSMC", "Spline CV"]
    colors = [BLUE, CORAL]
    for i, (row, label, color) in enumerate(zip(rows, labels, colors)):
        mean = float(row["mean_price"])
        low = float(row["replicate_ci_lower"])
        high = float(row["replicate_ci_upper"])
        ax.errorbar(
            mean,
            i,
            xerr=[[mean - low], [high - mean]],
            fmt="o",
            color=color,
            capsize=6,
            markersize=8,
            linewidth=2,
            label=f"{label}: {mean:.6f} [{low:.6f}, {high:.6f}]",
        )
    ax.axvline(crr_price, color=GOLD, linestyle="--", linewidth=2, label=f"Monthly Bermudan CRR: {crr_price:.6f}")
    ax.set_yticks([0, 1], labels)
    ax.invert_yaxis()
    ax.set_xlim(2.285, 2.311)
    ax.set_xlabel("Estimated fixed-policy value (95% Student-t interval across 30 replications)", color=CHARCOAL)
    ax.grid(axis="x", alpha=0.22)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=1, fontsize=8)
    fig.subplots_adjust(top=0.78)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.patch.set_facecolor(IVORY)
    finish(fig, "atm20_price.png")


def make_cpu_efficiency(summary):
    scenarios = [
        ("vanilla_atm_sigma20", "Vanilla ATM, 20%"),
        ("vanilla_atm_sigma40", "Vanilla ATM, 40%"),
        ("vanilla_itm_spot36_sigma20", "Vanilla ITM"),
        ("vanilla_otm_spot44_sigma20", "Vanilla OTM"),
        ("asian_put_k95", "Asian, $K=95$"),
        ("asian_put_k115", "Asian, $K=115$"),
    ]
    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    methods = [("linear_cv", "Linear", BLUE, -0.12), ("spline_cv", "Spline", CORAL, 0.12)]
    for method, label, color, offset in methods:
        values = []
        for scenario, _ in scenarios:
            row = unique_row(summary, scenario=scenario, n_paths=20000, method=method)
            value = row["aggregate_cpu_adjusted_efficiency"]
            if pd.isna(value):
                raise ValueError(f"Missing CPU-adjusted efficiency for {scenario} / {method}")
            values.append(float(value))
        y = [i + offset for i in range(len(scenarios))]
        ax.scatter(values, y, color=color, label=label, s=62, zorder=3)
    ax.axvline(1, color=CHARCOAL, linestyle="--", linewidth=1.1, alpha=0.65)
    ax.set_xscale("log")
    ax.set_yticks(range(len(scenarios)), [label for _, label in scenarios])
    ax.invert_yaxis()
    ax.set_ylim(len(scenarios) - 0.75, -0.75)
    ax.set_xlabel("CPU-adjusted efficiency ratio (log scale; >1 favors the control)", color=CHARCOAL)
    ax.set_title("Blue = linear · coral = spline · 20,000 paths · training cost included", color=CHARCOAL, fontsize=13, pad=12)
    ax.grid(axis="x", which="both", alpha=0.22)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.patch.set_facecolor(IVORY)
    finish(fig, "cpu_efficiency.png")


def make_vanilla_sensitivity(summary):
    frame = summary[summary["contract"] == "vanilla"]
    scenarios = [
        ("vanilla_atm_sigma20", "ATM, 20%"),
        ("vanilla_atm_sigma40", "ATM, 40%"),
        ("vanilla_itm_spot36_sigma20", "ITM, $S_0=36$"),
        ("vanilla_otm_spot44_sigma20", "OTM, $S_0=44$"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.3), sharey=True)
    for ax, n_paths in zip(axes, (5000, 20000)):
        for method, label, color, offset in (
            ("linear_cv", "Linear", BLUE, -0.12),
            ("spline_cv", "Spline", CORAL, 0.12),
        ):
            values = []
            for scenario, _ in scenarios:
                row = unique_row(frame, scenario=scenario, n_paths=n_paths, method=method)
                values.append(float(row["median_vrf"]))
            y = [i + offset for i in range(len(scenarios))]
            ax.scatter(values, y, color=color, label=label, s=55, zorder=3)
            for value, yi in zip(values, y):
                vertical_offset = 7 if method == "linear_cv" else -9
                ax.annotate(
                    f"{value:.2f}",
                    (value, yi),
                    xytext=(5, vertical_offset),
                    textcoords="offset points",
                    va="center",
                    fontsize=8,
                )
        ax.axvline(1, color=CHARCOAL, linestyle="--", linewidth=1, alpha=0.6)
        ax.set_xscale("log")
        ax.set_ylim(len(scenarios) - 0.55, -0.55)
        ax.set_title(f"N = {n_paths:,}", color=CHARCOAL, fontsize=14)
        ax.set_xlabel("Median VRF (log scale)", color=CHARCOAL)
        ax.grid(axis="x", which="both", alpha=0.2)
        ax.spines[["top", "right", "left"]].set_visible(False)
    axes[0].set_yticks(range(len(scenarios)), [label for _, label in scenarios])
    fig.suptitle("Blue = linear · coral = spline", color=CHARCOAL, fontsize=13, y=1.03)
    fig.patch.set_facecolor(IVORY)
    finish(fig, "vanilla_vrf_sensitivity.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = load_summary()
    expected_scenarios = {
        "vanilla_atm_sigma20",
        "vanilla_atm_sigma40",
        "vanilla_itm_spot36_sigma20",
        "vanilla_otm_spot44_sigma20",
        "asian_put_k95",
        "asian_put_k115",
    }
    available = set(summary.loc[summary["n_paths"] == 20000, "scenario"])
    if not expected_scenarios.issubset(available):
        raise ValueError(f"Missing core scenarios: {sorted(expected_scenarios - available)}")
    for scenario in expected_scenarios:
        for method in ("linear_cv", "spline_cv"):
            unique_row(summary, scenario=scenario, n_paths=20000, method=method)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "text.color": CHARCOAL,
            "axes.labelcolor": CHARCOAL,
            "xtick.color": CHARCOAL,
            "ytick.color": CHARCOAL,
            "axes.facecolor": IVORY,
            "figure.facecolor": IVORY,
        }
    )
    make_control_shapes()
    make_main_vrf(summary)
    make_atm_price(summary)
    make_cpu_efficiency(summary)
    make_vanilla_sensitivity(summary)


if __name__ == "__main__":
    main()
