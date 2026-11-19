from __future__ import annotations

import numpy as np


Array = np.ndarray


def _validate_gbm_inputs(
    spot: float, rate: float, dividend: float, volatility: float, maturity: float, steps: int, n_paths: int
) -> None:
    if spot <= 0.0:
        raise ValueError("spot must be positive")
    if volatility < 0.0:
        raise ValueError("volatility must be nonnegative")
    if maturity <= 0.0 or steps < 1 or n_paths < 1:
        raise ValueError("maturity, steps, and n_paths must be positive")
    if not np.all(np.isfinite([spot, rate, dividend, volatility, maturity])):
        raise ValueError("GBM parameters must be finite")


def simulate_gbm(
    spot: float,
    rate: float,
    dividend: float,
    volatility: float,
    maturity: float,
    steps: int,
    n_paths: int,
    rng: np.random.Generator,
) -> Array:
    """Simulate exact-grid risk-neutral lognormal GBM using a caller-owned RNG."""
    _validate_gbm_inputs(spot, rate, dividend, volatility, maturity, steps, n_paths)
    dt = maturity / steps
    shocks = rng.standard_normal((n_paths, steps))
    increments = (rate - dividend - 0.5 * volatility**2) * dt
    increments = increments + volatility * np.sqrt(dt) * shocks
    log_paths = np.column_stack((np.zeros(n_paths), np.cumsum(increments, axis=1)))
    return spot * np.exp(log_paths)


def simulate_correlated_gbm(
    spots: Array,
    rates: Array,
    dividends: Array,
    volatilities: Array,
    maturity: float,
    steps: int,
    n_paths: int,
    correlation: Array,
    rng: np.random.Generator,
) -> Array:
    """Simulate correlated GBMs; an eigen square root also supports PSD matrices."""
    spots = np.asarray(spots, dtype=float)
    rates = np.asarray(rates, dtype=float)
    dividends = np.asarray(dividends, dtype=float)
    volatilities = np.asarray(volatilities, dtype=float)
    correlation = np.asarray(correlation, dtype=float)
    dimension = spots.size
    if any(v.shape != (dimension,) for v in (rates, dividends, volatilities)):
        raise ValueError("spots, rates, dividends, and volatilities must have equal 1D shape")
    if correlation.shape != (dimension, dimension):
        raise ValueError("correlation shape does not match the number of assets")
    if not np.allclose(correlation, correlation.T, atol=1e-12):
        raise ValueError("correlation matrix must be symmetric")
    if not np.allclose(np.diag(correlation), 1.0, atol=1e-12):
        raise ValueError("correlation matrix must have unit diagonal")
    eigenvalues, eigenvectors = np.linalg.eigh(correlation)
    if eigenvalues.min() < -1e-12:
        raise ValueError("correlation matrix must be positive semidefinite")
    if np.any(spots <= 0.0) or np.any(volatilities < 0.0):
        raise ValueError("spots must be positive and volatilities nonnegative")
    if maturity <= 0.0 or steps < 1 or n_paths < 1:
        raise ValueError("maturity, steps, and n_paths must be positive")
    factor = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0.0)))
    normals = rng.standard_normal((n_paths, steps, dimension))
    correlated = normals @ factor.T
    dt = maturity / steps
    drift = (rates - dividends - 0.5 * volatilities**2) * dt
    increments = drift[None, None, :] + np.sqrt(dt) * correlated * volatilities[None, None, :]
    log_paths = np.concatenate(
        (np.zeros((n_paths, 1, dimension)), np.cumsum(increments, axis=1)), axis=1
    )
    return spots[None, None, :] * np.exp(log_paths)
