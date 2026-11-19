import numpy as np

from stat906cv.contracts import ArithmeticAsianPut, BermudanPut, build_states
from stat906cv.lsm_policy import (
    FittedLSMPolicy,
    backward_cashflow_step,
    fit_lsm_policy,
)


def test_backward_cashflow_recursion_allows_earlier_exercise_to_replace_later():
    next_cashflow = np.array([12.0, 0.0])
    earlier_intrinsic = np.array([8.0, 3.0])
    exercise_at_earlier_date = np.array([True, False])
    result = backward_cashflow_step(next_cashflow, earlier_intrinsic, 0.9, exercise_at_earlier_date)
    np.testing.assert_allclose(result, [8.0, 0.0])


def test_out_of_sample_policy_uses_forward_first_exercise_and_discounted_payoff():
    contract = BermudanPut(40.0, 40.0, 0.06, 0.0, 0.2, 1.0, 3)
    spot = np.array(
        [
            [40.0, 35.0, 30.0, 30.0],
            [40.0, 45.0, 35.0, 40.0],
            [40.0, 50.0, 50.0, 50.0],
        ]
    )
    states = build_states(spot, "vanilla")
    policy = FittedLSMPolicy(
        contract,
        1.0 / 3.0,
        {1: np.array([4.0, 0.0, 0.0]), 2: np.zeros(3)},
        t0_exercise=False,
    )
    result = policy.evaluate(states)
    np.testing.assert_array_equal(result.stopping_indices, [1, 2, 3])
    np.testing.assert_allclose(result.stopping_payoffs, [5.0, 5.0, 0.0])
    expected = np.exp(-contract.rate * result.stopping_indices / 3.0) * result.stopping_payoffs
    np.testing.assert_allclose(result.discounted_payoffs, expected)


def test_missing_regression_falls_back_to_later_eligible_date_and_asian_excludes_time_zero():
    contract = ArithmeticAsianPut(100.0, 100.0, 0.06, 0.0, 0.3, 0.5, 2)
    spot = np.array([[100.0, 90.0, 95.0], [100.0, 110.0, 100.0]])
    states = build_states(spot, "asian_arithmetic")
    policy = FittedLSMPolicy(contract, 0.25, {1: np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])}, False)
    assert not np.any(policy.decision(states, 0))
    result = policy.evaluate(states)
    assert np.all(result.stopping_indices >= 1)
    assert np.all(result.stopping_indices <= 2)


def test_vanilla_time_zero_exercise_uses_mean_continuation_value():
    contract = BermudanPut(30.0, 40.0, 0.06, 0.0, 0.2, 1.0, 2)
    spot = np.full((300, 3), 30.0)
    states = build_states(spot, "vanilla")
    fitted = fit_lsm_policy(states, contract, minimum_regression_paths=20)
    assert fitted.policy.t0_exercise
    evaluated = fitted.policy.evaluate(states)
    np.testing.assert_array_equal(evaluated.stopping_indices, np.zeros(300, dtype=int))
    np.testing.assert_allclose(evaluated.discounted_payoffs, 10.0)


def test_fit_regresses_only_in_the_money_paths_and_returns_unique_stops():
    rng = np.random.default_rng(119)
    n_paths, steps = 4000, 3
    spot = np.empty((n_paths, steps + 1))
    spot[:, 0] = 40.0
    for k in range(1, steps + 1):
        spot[:, k] = spot[:, k - 1] * np.exp(0.01 + 0.12 * rng.standard_normal(n_paths))
    states = build_states(spot, "vanilla")
    contract = BermudanPut(40.0, 40.0, 0.06, 0.0, 0.2, 1.0, steps)
    fitted = fit_lsm_policy(states, contract, minimum_regression_paths=20)
    diagnostics = {row.time_index: row for row in fitted.diagnostics}
    for k, row in diagnostics.items():
        expected_itm = int(np.sum(contract.payoff(states, k) > 0.0))
        assert row.n_regression_paths == expected_itm
    assert np.all((fitted.training_stopping_indices >= 0) & (fitted.training_stopping_indices <= steps))
    assert np.all(np.isfinite(fitted.training_cashflows))
