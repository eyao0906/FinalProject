import numpy as np

from stat906cv.contracts import ArithmeticAsianPut, build_states
from stat906cv.hinge_expectations import (
    lognormal_call_put_hinges,
    scaled_average_hinges,
)
from stat906cv.value_fit import ValueModel


def _assert_mc_close(analytic, samples):
    estimate = float(np.mean(samples))
    se = float(np.std(samples, ddof=1) / np.sqrt(samples.size))
    assert abs(estimate - float(analytic)) <= 6.0 * se + 2e-4


def test_spot_hinges_match_independent_conditional_simulation_in_all_regions():
    rng = np.random.default_rng(621)
    n_paths, dt, rate, dividend, volatility = 350_000, 0.25, 0.06, 0.02, 0.30
    for spot, threshold in ((100.0, 70.0), (100.0, 100.0), (100.0, 130.0)):
        next_spot = spot * np.exp(
            (rate - dividend - 0.5 * volatility**2) * dt
            + volatility * np.sqrt(dt) * rng.standard_normal(n_paths)
        )
        call, put = lognormal_call_put_hinges(spot, threshold, rate, dividend, volatility, dt)
        _assert_mc_close(call, np.maximum(next_spot - threshold, 0.0))
        _assert_mc_close(put, np.maximum(threshold - next_spot, 0.0))


def test_asian_hinges_match_shifted_lognormal_simulation_and_edge_branches():
    rng = np.random.default_rng(622)
    n_paths, dt, rate, dividend, volatility = 300_000, 1.0 / 12.0, 0.06, 0.0, 0.30
    previous_spot, previous_average, time_index, strike, threshold = 100.0, 95.0, 3, 100.0, 100.0
    next_spot = previous_spot * np.exp(
        (rate - dividend - 0.5 * volatility**2) * dt
        + volatility * np.sqrt(dt) * rng.standard_normal(n_paths)
    )
    next_average = ((time_index - 1) * previous_average + next_spot) / time_index
    call, put = scaled_average_hinges(
        np.full(n_paths, previous_spot),
        np.full(n_paths, previous_average),
        time_index,
        threshold / strike,
        strike,
        rate,
        dividend,
        volatility,
        dt,
    )
    _assert_mc_close(call[0], np.maximum(next_average / strike - threshold / strike, 0.0))
    _assert_mc_close(put[0], np.maximum(threshold / strike - next_average / strike, 0.0))
    call_nonpositive, put_nonpositive = lognormal_call_put_hinges(
        100.0, -5.0, rate, dividend, volatility, dt
    )
    assert call_nonpositive == 100.0 * np.exp((rate - dividend) * dt) + 5.0
    assert put_nonpositive == 0.0
    call_zero, put_zero = lognormal_call_put_hinges(100.0, 95.0, rate, dividend, 0.0, dt)
    forward = 100.0 * np.exp((rate - dividend) * dt)
    assert call_zero == max(forward - 95.0, 0.0)
    assert put_zero == max(95.0 - forward, 0.0)
    first_date_call, first_date_put = scaled_average_hinges(
        np.array([100.0]),
        np.array([0.0]),
        1,
        1.0,
        100.0,
        rate,
        dividend,
        volatility,
        dt,
    )
    spot_call, spot_put = lognormal_call_put_hinges(
        100.0, 100.0, rate, dividend, volatility, dt
    )
    np.testing.assert_allclose(first_date_call, [spot_call / 100.0])
    np.testing.assert_allclose(first_date_put, [spot_put / 100.0])


def test_linear_value_model_has_exact_conditional_expectation():
    contract = ArithmeticAsianPut(100.0, 100.0, 0.06, 0.0, 0.3, 0.5, 6)
    paths = np.array([[100.0, 105.0, 108.0, 110.0], [100.0, 95.0, 96.0, 97.0]])
    states = build_states(paths, "asian_arithmetic")
    model = ValueModel(
        time_index=3,
        model_kind="linear",
        contract_kind=contract.kind,
        strike=contract.strike,
        coefficient=np.array([2.0, 0.5, -0.25]),
        coordinates=("spot", "average"),
        knots={},
        feature_names=["intercept", "linear:spot", "linear:average"],
        training_mse=0.0,
        validation_mse=0.0,
        condition_number=1.0,
        rank=3,
        regularization=0.0,
        n_terms=2,
    )
    expected_spot = states["spot"][:, 2] * np.exp(contract.rate / 12)
    expected_average = (
        2 * states["average"][:, 2] + states["spot"][:, 2] * np.exp(contract.rate / 12)
    ) / 3
    expected = 2.0 + 0.5 * expected_spot / contract.strike - 0.25 * expected_average / contract.strike
    np.testing.assert_allclose(
        model.expectation(states, contract, contract.rate, 0.0, 0.3, 1 / 12), expected
    )
