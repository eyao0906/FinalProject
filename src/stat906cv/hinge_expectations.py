from __future__ import annotations

import numpy as np
from scipy.special import ndtr


Array = np.ndarray


def lognormal_call_put_hinges(
    current_spot: Array | float,
    threshold: Array | float,
    rate: float,
    dividend: float,
    volatility: float,
    dt: float,
) -> tuple[Array, Array]:
    """Return undiscounted E[(S_next-H)+] and E[(H-S_next)+] under GBM."""
    spot, strike = np.broadcast_arrays(
        np.asarray(current_spot, dtype=float), np.asarray(threshold, dtype=float)
    )
    if np.any(spot < 0.0) or volatility < 0.0 or dt < 0.0:
        raise ValueError("spot, volatility, and dt must be nonnegative")
    forward = spot * np.exp((rate - dividend) * dt)
    call = np.empty_like(forward)
    put = np.empty_like(forward)
    nonpositive_threshold = strike <= 0.0
    call[nonpositive_threshold] = forward[nonpositive_threshold] - strike[nonpositive_threshold]
    put[nonpositive_threshold] = 0.0
    positive = ~nonpositive_threshold
    deterministic = positive & ((volatility == 0.0) | (dt == 0.0) | (spot == 0.0))
    if np.any(deterministic):
        call[deterministic] = np.maximum(forward[deterministic] - strike[deterministic], 0.0)
        put[deterministic] = np.maximum(strike[deterministic] - forward[deterministic], 0.0)
    stochastic = positive & ~deterministic
    if np.any(stochastic):
        variance_root = volatility * np.sqrt(dt)
        log_moneyness = np.log(spot[stochastic] / strike[stochastic])
        d1 = (log_moneyness + (rate - dividend + 0.5 * volatility**2) * dt) / variance_root
        d2 = d1 - variance_root
        call[stochastic] = (
            forward[stochastic] * ndtr(d1) - strike[stochastic] * ndtr(d2)
        )
        put[stochastic] = (
            strike[stochastic] * ndtr(-d2) - forward[stochastic] * ndtr(-d1)
        )
    return call, put


def scaled_spot_hinges(
    current_spot: Array,
    normalized_threshold: float,
    strike_scale: float,
    rate: float,
    dividend: float,
    volatility: float,
    dt: float,
) -> tuple[Array, Array]:
    call, put = lognormal_call_put_hinges(
        current_spot,
        normalized_threshold * strike_scale,
        rate,
        dividend,
        volatility,
        dt,
    )
    return call / strike_scale, put / strike_scale


def scaled_average_hinges(
    previous_spot: Array,
    previous_average: Array,
    time_index: int,
    normalized_threshold: float,
    strike_scale: float,
    rate: float,
    dividend: float,
    volatility: float,
    dt: float,
) -> tuple[Array, Array]:
    if time_index < 1:
        raise ValueError("the arithmetic average is defined from time index 1")
    threshold = time_index * normalized_threshold * strike_scale - (time_index - 1) * previous_average
    call, put = lognormal_call_put_hinges(
        previous_spot, threshold, rate, dividend, volatility, dt
    )
    return call / (time_index * strike_scale), put / (time_index * strike_scale)
