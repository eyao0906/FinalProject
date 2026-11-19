import numpy as np
import pandas as pd

from stat906cv.statistics import summarize_replications


def _row(method, replicate, price, payoff_sd, cpu):
    return {
        "scenario": "case",
        "contract": "vanilla",
        "spot": 40.0,
        "strike": 40.0,
        "rate": 0.06,
        "dividend": 0.0,
        "volatility": 0.2,
        "maturity": 1.0,
        "steps": 12,
        "n_paths": 5000,
        "method": method,
        "replicate": replicate,
        "price": price,
        "path_payoff_sd": payoff_sd,
        "standard_error": payoff_sd / np.sqrt(5000),
        "ci_lower": price - 0.01,
        "ci_upper": price + 0.01,
        "marginal_cpu_seconds": cpu,
        "marginal_wall_seconds": cpu,
        "total_cpu_seconds": cpu,
        "total_wall_seconds": cpu,
        "exercise_frequency": 0.2,
        "mean_exercise_time": 0.8,
        "mean_martingale": 0.0,
        "martingale_sd": 1.0,
        "y_martingale_correlation": 0.8,
        "variance_reduction_factor": 4.0 if method != "plain" else 1.0,
        "se_reduction": 2.0 if method != "plain" else 1.0,
        "cpu_adjusted_efficiency": np.nan,
    }


def test_cpu_adjusted_efficiency_uses_aggregate_paired_costs():
    rows = []
    for replicate in range(2):
        rows.extend(
            [
                _row("plain", replicate, 2.0, 2.0, 0.1),
                _row("spline_cv", replicate, 2.0, 1.0, 0.2),
            ]
        )
    summary = summarize_replications(pd.DataFrame(rows))
    cv = summary[summary["method"] == "spline_cv"].iloc[0]
    assert cv["aggregate_cpu_adjusted_efficiency"] == 2.0
    assert cv["cpu_efficiency_timing_status"] == "aggregate timing usable"


def test_cpu_efficiency_is_flagged_below_aggregate_clock_floor():
    rows = [
        _row(method, replicate, 2.0, 2.0 if method == "plain" else 1.0, 0.001)
        for replicate in range(2)
        for method in ("plain", "spline_cv")
    ]
    summary = summarize_replications(pd.DataFrame(rows))
    cv = summary[summary["method"] == "spline_cv"].iloc[0]
    assert np.isnan(cv["aggregate_cpu_adjusted_efficiency"])
    assert "below" in cv["cpu_efficiency_timing_status"]
