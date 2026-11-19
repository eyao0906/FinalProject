from __future__ import annotations

import math

import numpy as np
from scipy.special import ndtr


def black_scholes_put(spot: float, strike: float, rate: float, dividend: float, volatility: float, maturity: float) -> float:
    if maturity <= 0.0:
        return max(strike - spot, 0.0)
    if volatility <= 0.0:
        return max(strike * math.exp(-rate * maturity) - spot * math.exp(-dividend * maturity), 0.0)
    root_t = math.sqrt(maturity)
    d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * volatility**2) * maturity) / (
        volatility * root_t
    )
    d2 = d1 - volatility * root_t
    return float(
        strike * math.exp(-rate * maturity) * ndtr(-d2)
        - spot * math.exp(-dividend * maturity) * ndtr(-d1)
    )


def crr_put(
    spot: float,
    strike: float,
    rate: float,
    dividend: float,
    volatility: float,
    maturity: float,
    tree_steps: int,
    bermudan_dates: int | None = None,
) -> float:
    """CRR put tree with exercise at every step, or on aligned Bermudan dates only."""
    if tree_steps < 1 or maturity <= 0.0 or volatility <= 0.0:
        raise ValueError("tree_steps, maturity, and volatility must be positive")
    if bermudan_dates is not None and (bermudan_dates < 1 or tree_steps % bermudan_dates):
        raise ValueError("tree_steps must be divisible by the number of Bermudan intervals")
    dt = maturity / tree_steps
    up = math.exp(volatility * math.sqrt(dt))
    down = 1.0 / up
    probability = (math.exp((rate - dividend) * dt) - down) / (up - down)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("CRR risk-neutral probability is outside [0, 1]")
    discount = math.exp(-rate * dt)
    indices = np.arange(tree_steps + 1)
    stock = spot * np.power(up, indices) * np.power(down, tree_steps - indices)
    value = np.maximum(strike - stock, 0.0)
    stride = None if bermudan_dates is None else tree_steps // bermudan_dates
    for time_index in range(tree_steps - 1, -1, -1):
        value = discount * (probability * value[1:] + (1.0 - probability) * value[:-1])
        if stride is None or time_index % stride == 0:
            node_index = np.arange(time_index + 1)
            stock = spot * np.power(up, node_index) * np.power(down, time_index - node_index)
            value = np.maximum(value, np.maximum(strike - stock, 0.0))
    return float(value[0])


def bermudan_put_crr(
    spot: float,
    strike: float,
    rate: float,
    dividend: float,
    volatility: float,
    maturity: float,
    exercise_dates: int,
    tree_steps: int,
) -> float:
    return crr_put(
        spot, strike, rate, dividend, volatility, maturity, tree_steps, bermudan_dates=exercise_dates
    )


def american_put_crr(
    spot: float, strike: float, rate: float, dividend: float, volatility: float, maturity: float, tree_steps: int
) -> float:
    return crr_put(spot, strike, rate, dividend, volatility, maturity, tree_steps)
