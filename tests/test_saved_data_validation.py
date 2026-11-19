import pandas as pd
import pytest

from stat906cv.experiments import (
    benchmark_comparison_table,
    martingale_validation_checks,
)


def _replication(n_paths, mean_martingale, martingale_sd, scenario="case"):
    return {
        "scenario": scenario,
        "method": "spline_cv",
        "n_paths": n_paths,
        "mean_martingale": mean_martingale,
        "martingale_sd": martingale_sd,
    }


def test_martingale_validation_uses_each_replication_sample_size():
    replications = pd.DataFrame(
        [
            _replication(100, 0.6, 2.0),
            _replication(10_000, 0.6, 2.0),
        ]
    )
    check = martingale_validation_checks(replications)

    assert len(check) == 2
    small, large = (check[0], check[1])
    assert small["n_paths"] == 100
    assert large["n_paths"] == 10_000
    assert small["value"]["max_abs_mean_over_se"] == pytest.approx(3.0)
    assert large["value"]["max_abs_mean_over_se"] == pytest.approx(30.0)
    assert small["passed"] is True
    assert large["passed"] is False


def test_martingale_validation_rejects_nonfinite_or_zero_standard_error():
    for sd in (0.0, float("nan"), float("inf")):
        replications = pd.DataFrame([_replication(100, 0.1, sd)])
        check = martingale_validation_checks(replications)[0]
        assert check["passed"] is False
        assert check["value"]["valid_replications"] == 0


def test_benchmark_comparison_reports_signed_and_relative_gap_by_method():
    summary = pd.DataFrame(
        [
            {
                "scenario": "vanilla",
                "contract": "vanilla",
                "n_paths": 20_000,
                "method": method,
                "mean_price": price,
                "replicate_sd": 0.1,
                "replications": 30,
                "replicate_ci_lower": price - 0.04,
                "replicate_ci_upper": price + 0.04,
            }
            for method, price in (("plain", 9.95), ("spline_cv", 9.92))
        ]
    )
    references = pd.DataFrame(
        [
            {
                "scenario": "vanilla",
                "benchmark": "same-grid monthly Bermudan CRR",
                "tree_steps": steps,
                "price": price,
            }
            for steps, price in ((1200, 10.0), (2400, 10.02))
        ]
    )
    comparison = benchmark_comparison_table(summary, references).set_index("method")

    assert comparison.loc["plain", "gap"] == pytest.approx(-0.07)
    assert comparison.loc["plain", "relative_gap_percent"] == pytest.approx(
        -0.6986027944111774
    )
    assert comparison.loc["spline_cv", "gap"] == pytest.approx(-0.1)
    assert bool(comparison["possible_lower_bound_violation"].all()) is False
