import pandas as pd
import pytest

from stat906cv.plots import (
    aggregate_exercise_distribution,
    moneyness_results,
    primary_results,
    volatility_results,
)


def _summary_row(scenario, contract, n_paths, method, spot=40.0, volatility=0.2):
    return {
        "scenario": scenario,
        "contract": contract,
        "n_paths": n_paths,
        "method": method,
        "spot": spot,
        "volatility": volatility,
    }


def test_primary_vrf_data_selects_all_scenarios_at_largest_sample_size():
    rows = [
        _summary_row(scenario, "vanilla", n_paths, "linear_cv")
        for scenario in ("vanilla_atm_sigma20", "vanilla_otm_spot44_sigma20")
        for n_paths in (5000, 20000)
    ]
    data = primary_results(pd.DataFrame(rows))
    assert set(data["n_paths"]) == {20000}
    assert set(data["scenario"]) == {
        "vanilla_atm_sigma20",
        "vanilla_otm_spot44_sigma20",
    }


def test_vrf_sensitivity_panels_do_not_mix_unrelated_scenarios():
    scenarios = [
        ("vanilla_atm_sigma20", 40.0, 0.2),
        ("vanilla_atm_sigma40", 40.0, 0.4),
        ("vanilla_itm_spot36_sigma20", 36.0, 0.2),
        ("vanilla_otm_spot44_sigma20", 44.0, 0.2),
    ]
    summary = pd.DataFrame(
        [
            _summary_row(scenario, "vanilla", 20000, method, spot, volatility)
            for scenario, spot, volatility in scenarios
            for method in ("linear_cv", "spline_cv")
        ]
    )
    volatility = volatility_results(summary)
    moneyness = moneyness_results(summary)

    assert set(volatility["scenario"]) == {
        "vanilla_atm_sigma20",
        "vanilla_atm_sigma40",
    }
    assert set(volatility["spot"]) == {40.0}
    assert set(moneyness["scenario"]) == {
        "vanilla_itm_spot36_sigma20",
        "vanilla_atm_sigma20",
        "vanilla_otm_spot44_sigma20",
    }
    assert set(moneyness["volatility"]) == {0.2}


def test_exercise_aggregation_uses_exact_sample_size_and_averages_replicates():
    exercise = pd.DataFrame(
        [
            {
                "scenario": "case",
                "n_paths": n_paths,
                "replicate": replicate,
                "time_index": 1,
                "time": 0.1,
                "contract": "vanilla",
                "frequency": frequency,
            }
            for n_paths, replicate, frequency in (
                (5000, 0, 0.9),
                (20000, 0, 0.2),
                (20000, 1, 0.4),
            )
        ]
    )
    result = aggregate_exercise_distribution(exercise, "case", 20000)
    assert len(result) == 1
    assert result.loc[0, "probability"] == pytest.approx(0.3)
    assert result.loc[0, "replication_se"] > 0
