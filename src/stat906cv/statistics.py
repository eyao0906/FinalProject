from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import t


CPU_AGGREGATE_FLOOR_SECONDS = 0.05


def summarize_replications(replications: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    key_columns = ["scenario", "contract", "n_paths", "method"]
    paired = replications.pivot_table(
        index=["scenario", "contract", "n_paths", "replicate"],
        columns="method",
        values="price",
        aggfunc="first",
    )
    for keys, group in replications.groupby(key_columns, sort=True):
        scenario, contract, n_paths, method = keys
        prices = group["price"].to_numpy(dtype=float)
        r = prices.size
        mean_price = float(np.mean(prices))
        replicate_sd = float(np.std(prices, ddof=1)) if r > 1 else float("nan")
        critical = float(t.ppf(0.975, r - 1)) if r > 1 else float("nan")
        replicate_half_width = critical * replicate_sd / np.sqrt(r) if r > 1 else float("nan")
        row: dict[str, object] = {
            "scenario": scenario,
            "contract": contract,
            "spot": float(group["spot"].iloc[0]),
            "strike": float(group["strike"].iloc[0]),
            "rate": float(group["rate"].iloc[0]),
            "dividend": float(group["dividend"].iloc[0]),
            "volatility": float(group["volatility"].iloc[0]),
            "maturity": float(group["maturity"].iloc[0]),
            "steps": int(group["steps"].iloc[0]),
            "n_paths": int(n_paths),
            "method": method,
            "replications": int(r),
            "mean_price": mean_price,
            "replicate_sd": replicate_sd,
            "replicate_ci_lower": mean_price - replicate_half_width,
            "replicate_ci_upper": mean_price + replicate_half_width,
            "mean_path_payoff_sd": float(group["path_payoff_sd"].mean()),
            "mean_path_se": float(group["standard_error"].mean()),
            "mean_path_ci_lower": float(group["ci_lower"].mean()),
            "mean_path_ci_upper": float(group["ci_upper"].mean()),
            "mean_marginal_cpu_seconds": float(group["marginal_cpu_seconds"].mean()),
            "mean_marginal_wall_seconds": float(group["marginal_wall_seconds"].mean()),
            "mean_total_cpu_seconds": float(group["total_cpu_seconds"].mean()),
            "mean_total_wall_seconds": float(group["total_wall_seconds"].mean()),
            "mean_exercise_frequency": float(group["exercise_frequency"].mean()),
            "mean_exercise_time": float(group["mean_exercise_time"].mean()),
            "mean_martingale": float(group["mean_martingale"].mean()),
            "mean_martingale_sd": float(group["martingale_sd"].mean()),
            "mean_y_martingale_correlation": float(group["y_martingale_correlation"].mean()),
            "mean_vrf": float(group["variance_reduction_factor"].mean()),
            "median_vrf": float(group["variance_reduction_factor"].median()),
            "vrf_replicate_sd": float(group["variance_reduction_factor"].std(ddof=1)),
            "mean_se_reduction": float(group["se_reduction"].mean()),
            "aggregate_cpu_adjusted_efficiency": float("nan"),
        }
        if method != "plain":
            differences = (
                paired.loc[(scenario, contract, int(n_paths))][method]
                - paired.loc[(scenario, contract, int(n_paths))]["plain"]
            ).to_numpy(dtype=float)
            difference_mean = float(np.mean(differences))
            difference_sd = float(np.std(differences, ddof=1))
            difference_half_width = critical * difference_sd / np.sqrt(r)
            row.update(
                {
                    "paired_difference_mean": difference_mean,
                    "paired_difference_ci_lower": difference_mean - difference_half_width,
                    "paired_difference_ci_upper": difference_mean + difference_half_width,
                }
            )
        else:
            row.update(
                {
                    "paired_difference_mean": 0.0,
                    "paired_difference_ci_lower": 0.0,
                    "paired_difference_ci_upper": 0.0,
                }
            )
        paired_group = replications[
            (replications["scenario"] == scenario)
            & (replications["contract"] == contract)
            & (replications["n_paths"] == n_paths)
        ]
        plain = paired_group[paired_group["method"] == "plain"].sort_values("replicate")
        current = group.sort_values("replicate")
        plain_cpu = float(plain["total_cpu_seconds"].sum())
        current_cpu = float(current["total_cpu_seconds"].sum())
        row["aggregate_plain_cpu_seconds"] = plain_cpu
        row["aggregate_method_cpu_seconds"] = current_cpu
        if min(plain_cpu, current_cpu) < CPU_AGGREGATE_FLOOR_SECONDS:
            row["aggregate_cpu_adjusted_efficiency"] = float("nan")
            row["cpu_efficiency_timing_status"] = "below 0.05 second aggregate measurement floor"
        elif method == "plain":
            row["aggregate_cpu_adjusted_efficiency"] = 1.0
            row["cpu_efficiency_timing_status"] = "aggregate timing usable"
        else:
            plain_variance = plain["path_payoff_sd"].to_numpy(dtype=float) ** 2
            current_variance = current["path_payoff_sd"].to_numpy(dtype=float) ** 2
            plain_cost = plain["total_cpu_seconds"].to_numpy(dtype=float)
            current_cost = current["total_cpu_seconds"].to_numpy(dtype=float)
            denominator = float(np.sum(current_variance * current_cost))
            numerator = float(np.sum(plain_variance * plain_cost))
            row["aggregate_cpu_adjusted_efficiency"] = numerator / denominator if denominator > 0 else float("nan")
            row["cpu_efficiency_timing_status"] = "aggregate timing usable"
        rows.append(row)
    return pd.DataFrame(rows)


def paired_path_diagnostics(
    y: np.ndarray, correction: np.ndarray, adjusted: np.ndarray
) -> dict[str, float]:
    payoff_variance = float(np.var(y, ddof=1))
    adjusted_variance = float(np.var(adjusted, ddof=1))
    correction_sd = float(np.std(correction, ddof=1))
    if adjusted_variance <= np.finfo(float).tiny:
        vrf = float("inf") if payoff_variance > 0 else 1.0
    else:
        vrf = payoff_variance / adjusted_variance
    if correction_sd == 0.0 or np.std(y, ddof=1) == 0.0:
        correlation = float("nan")
    else:
        correlation = float(np.corrcoef(y, correction)[0, 1])
    n = y.size
    y_sd = float(np.std(y, ddof=1))
    adjusted_sd = float(np.std(adjusted, ddof=1))
    return {
        "price": float(np.mean(adjusted)),
        "path_payoff_sd": adjusted_sd,
        "standard_error": adjusted_sd / np.sqrt(n),
        "ci_lower": float(np.mean(adjusted) - 1.96 * adjusted_sd / np.sqrt(n)),
        "ci_upper": float(np.mean(adjusted) + 1.96 * adjusted_sd / np.sqrt(n)),
        "mean_martingale": float(np.mean(correction)),
        "martingale_sd": correction_sd,
        "y_martingale_correlation": correlation,
        "variance_reduction_factor": vrf,
        "se_reduction": y_sd / adjusted_sd if adjusted_sd > 0.0 else float("inf"),
        "mean_increment": float("nan"),
        "increment_sd": float("nan"),
    }
