import numpy as np

from stat906cv.contracts import BermudanPut, build_states
from stat906cv.gbm import simulate_gbm
from stat906cv.lsm_policy import fit_lsm_policy
from stat906cv.martingale import apply_control_variate, martingale_correction
from stat906cv.value_fit import ValueModel


def test_zero_control_variate_is_exactly_plain_and_seed_is_reproducible():
    contract = BermudanPut(40.0, 40.0, 0.06, 0.0, 0.2, 1.0, 12)
    seed = 906
    spot = simulate_gbm(40.0, 0.06, 0.0, 0.2, 1.0, 12, 3000, np.random.default_rng(seed))
    states = build_states(spot, "vanilla")
    fit = fit_lsm_policy(states, contract, minimum_regression_paths=20)
    fit_again = fit_lsm_policy(states, contract, minimum_regression_paths=20)
    np.testing.assert_array_equal(fit.training_cashflows, fit_again.training_cashflows)
    np.testing.assert_array_equal(
        fit.training_stopping_indices, fit_again.training_stopping_indices
    )
    prices_a = simulate_gbm(40.0, 0.06, 0.0, 0.2, 1.0, 12, 2000, np.random.default_rng(907))
    prices_b = simulate_gbm(40.0, 0.06, 0.0, 0.2, 1.0, 12, 2000, np.random.default_rng(907))
    np.testing.assert_array_equal(prices_a, prices_b)
    pricing_states = build_states(prices_a, "vanilla")
    evaluation = fit.policy.evaluate(pricing_states)
    zero_models = {
        k: ValueModel(
            time_index=k,
            model_kind="linear",
            contract_kind=contract.kind,
            strike=contract.strike,
            coefficient=np.zeros(2),
            coordinates=("spot",),
            knots={},
            feature_names=["intercept", "slope"],
            training_mse=0.0,
            validation_mse=0.0,
            condition_number=1.0,
            rank=2,
            regularization=0.0,
            n_terms=1,
        )
        for k in range(1, contract.steps + 1)
    }
    _, _, stopped = martingale_correction(pricing_states, evaluation, zero_models, contract)
    plain = evaluation.discounted_payoffs
    adjusted = apply_control_variate(evaluation, stopped)
    np.testing.assert_array_equal(stopped, np.zeros_like(stopped))
    np.testing.assert_array_equal(adjusted, plain)
    assert np.all(np.isfinite(adjusted))
