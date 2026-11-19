import numpy as np

from stat906cv.gbm import simulate_correlated_gbm, simulate_gbm


def test_gbm_moments_and_dividend_drift():
    n_paths = 250_000
    rate, dividend, volatility, maturity = 0.06, 0.10, 0.30, 0.5
    spot = 100.0
    paths = simulate_gbm(
        spot, rate, dividend, volatility, maturity, 1, n_paths, np.random.default_rng(814)
    )
    terminal = paths[:, 1]
    expected_mean = spot * np.exp((rate - dividend) * maturity)
    mean_se = np.std(terminal, ddof=1) / np.sqrt(n_paths)
    assert abs(np.mean(terminal) - expected_mean) <= 6.0 * mean_se
    log_returns = np.log(terminal / spot)
    expected_log_mean = (rate - dividend - 0.5 * volatility**2) * maturity
    expected_log_variance = volatility**2 * maturity
    log_mean_se = volatility * np.sqrt(maturity / n_paths)
    variance_se = expected_log_variance * np.sqrt(2.0 / (n_paths - 1))
    assert abs(np.mean(log_returns) - expected_log_mean) <= 6.0 * log_mean_se
    assert abs(np.var(log_returns, ddof=1) - expected_log_variance) <= 6.0 * variance_se


def test_correlated_gbm_covariance_and_psd_boundary():
    correlation = np.array([[1.0, 0.45], [0.45, 1.0]])
    paths = simulate_correlated_gbm(
        np.array([100.0, 100.0]),
        np.array([0.05, 0.05]),
        np.array([0.10, 0.10]),
        np.array([0.20, 0.20]),
        1.0,
        1,
        150_000,
        correlation,
        np.random.default_rng(815),
    )
    log_returns = np.log(paths[:, 1, :] / paths[:, 0, :])
    assert abs(np.corrcoef(log_returns.T)[0, 1] - 0.45) < 0.015
    singular = np.ones((2, 2))
    identical = simulate_correlated_gbm(
        np.array([100.0, 100.0]),
        np.array([0.05, 0.05]),
        np.array([0.10, 0.10]),
        np.array([0.20, 0.20]),
        1.0,
        12,
        1000,
        singular,
        np.random.default_rng(816),
    )
    np.testing.assert_allclose(identical[:, :, 0], identical[:, :, 1], rtol=1e-13, atol=1e-13)
    with np.testing.assert_raises(ValueError):
        simulate_correlated_gbm(
            np.ones(2), np.zeros(2), np.zeros(2), np.ones(2) * 0.2,
            1.0, 1, 10, np.array([[1.0, 1.2], [1.2, 1.0]]), np.random.default_rng(1)
        )
