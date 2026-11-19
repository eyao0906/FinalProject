import numpy as np

from stat906cv.gbm import simulate_correlated_gbm
from stat906cv.hinge_expectations import lognormal_call_put_hinges


def _call_crr(spot, strike, rate, volatility, maturity, steps, exercise_early):
    dt = maturity / steps
    up = np.exp(volatility * np.sqrt(dt))
    down = 1.0 / up
    probability = (np.exp(rate * dt) - down) / (up - down)
    value = np.maximum(
        spot * np.power(up, np.arange(steps + 1))
        * np.power(down, steps - np.arange(steps + 1)) - strike,
        0.0,
    )
    for time_index in range(steps - 1, -1, -1):
        value = np.exp(-rate * dt) * (probability * value[1:] + (1 - probability) * value[:-1])
        if exercise_early:
            indices = np.arange(time_index + 1)
            stock = spot * np.power(up, indices) * np.power(down, time_index - indices)
            value = np.maximum(value, stock - strike)
    return float(value[0])


def test_optional_basket_prerequisite_psd_identical_assets_and_nondividend_call():
    n_paths = 20_000
    parameters = (
        np.array([100.0, 100.0]),
        np.array([0.05, 0.05]),
        np.array([0.10, 0.10]),
        np.array([0.20, 0.20]),
    )
    identical = simulate_correlated_gbm(
        *parameters, 1.0, 12, n_paths, np.ones((2, 2)), np.random.default_rng(1001)
    )
    np.testing.assert_allclose(identical[:, :, 0], identical[:, :, 1], rtol=1e-13, atol=1e-13)
    basket = np.mean(identical[:, :, :], axis=2)
    np.testing.assert_allclose(basket, identical[:, :, 0], rtol=1e-13, atol=1e-13)
    exact_basket_call = np.maximum(basket[:, 1] - 100.0, 0.0)
    exact_single_call = np.maximum(identical[:, 1, 0] - 100.0, 0.0)
    np.testing.assert_array_equal(exact_basket_call, exact_single_call)
    with np.testing.assert_raises(ValueError):
        simulate_correlated_gbm(
            *parameters, 1.0, 12, 10, np.array([[1.0, 1.1], [1.1, 1.0]]), np.random.default_rng(1)
        )

    american_call = _call_crr(100.0, 100.0, 0.05, 0.20, 1.0, 1200, True)
    european_call = _call_crr(100.0, 100.0, 0.05, 0.20, 1.0, 1200, False)
    assert abs(american_call - european_call) < 1e-12


def test_independent_lognormal_basket_call_is_not_a_single_lognormal_hinge():
    n_paths = 250_000
    spots = simulate_correlated_gbm(
        np.array([100.0, 100.0]),
        np.array([0.05, 0.05]),
        np.array([0.10, 0.10]),
        np.array([0.20, 0.20]),
        1.0,
        1,
        n_paths,
        np.eye(2),
        np.random.default_rng(1002),
    )[:, 1, :]
    basket_call = np.maximum(np.mean(spots, axis=1) - 100.0, 0.0)
    basket_se = np.std(basket_call, ddof=1) / np.sqrt(n_paths)
    plug_in, _ = lognormal_call_put_hinges(100.0, 100.0, 0.05, 0.10, 0.20, 1.0)
    assert abs(np.mean(basket_call) - float(plug_in)) > 6.0 * basket_se
