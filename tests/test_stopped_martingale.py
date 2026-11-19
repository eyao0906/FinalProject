import numpy as np
import pytest

from stat906cv.contracts import ArithmeticAsianPut, BermudanPut, build_states
from stat906cv.gbm import simulate_gbm
from stat906cv.lsm_policy import fit_lsm_policy
from stat906cv.martingale import martingale_correction
from stat906cv.value_fit import fit_value_models


@pytest.mark.parametrize(
    "contract,kind",
    [
        (BermudanPut(40.0, 40.0, 0.06, 0.0, 0.2, 1.0, 12), "vanilla"),
        (ArithmeticAsianPut(100.0, 95.0, 0.06, 0.0, 0.3, 0.5, 6), "asian_arithmetic"),
    ],
)
def test_fixed_independent_value_fit_has_zero_mean_terminal_and_stopped_martingale(contract, kind):
    def paths(n, seed):
        spot = simulate_gbm(
            contract.spot0, contract.rate, contract.dividend, contract.volatility,
            contract.maturity, contract.steps, n, np.random.default_rng(seed)
        )
        return build_states(spot, kind)

    policy_fit = fit_lsm_policy(paths(5000, 901), contract, minimum_regression_paths=50)
    models, _ = fit_value_models(
        paths(6000, 902), paths(2000, 903), policy_fit.policy, contract, (0.25, 0.5, 0.75)
    )
    pricing_states = paths(70_000, 904)
    evaluation = policy_fit.policy.evaluate(pricing_states)
    increments, martingale_path, stopped = martingale_correction(
        pricing_states, evaluation, models["spline"], contract
    )
    for values in (martingale_path[:, -1], stopped):
        se = np.std(values, ddof=1) / np.sqrt(values.size)
        assert abs(np.mean(values)) <= 6.0 * se
    adjusted = evaluation.discounted_payoffs - stopped
    difference = np.mean(adjusted - evaluation.discounted_payoffs)
    difference_se = np.std(stopped, ddof=1) / np.sqrt(stopped.size)
    assert abs(difference) <= 6.0 * difference_se
    assert np.all(np.isfinite(increments))


def test_broken_undiscounted_conditioning_is_detected():
    n_paths, steps, dt, rate = 100_000, 12, 1.0 / 12.0, 0.06
    spots = simulate_gbm(40.0, rate, 0.0, 0.2, 1.0, steps, n_paths, np.random.default_rng(905))
    broken = np.zeros(n_paths)
    for k in range(1, steps + 1):
        broken += np.exp(-rate * k * dt) * (spots[:, k] - spots[:, k - 1])
    broken_se = np.std(broken, ddof=1) / np.sqrt(n_paths)
    assert np.mean(broken) > 6.0 * broken_se
