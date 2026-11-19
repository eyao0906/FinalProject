from __future__ import annotations

import numpy as np

from stat906cv.contracts import ArithmeticAsianPut, BermudanPut, States
from stat906cv.lsm_policy import PolicyEvaluation
from stat906cv.value_fit import ValueModel


Array = np.ndarray


def martingale_correction(
    states: States,
    evaluation: PolicyEvaluation,
    models: dict[int, ValueModel],
    contract: BermudanPut | ArithmeticAsianPut,
) -> tuple[Array, Array, Array]:
    """Return per-date increments, full martingale path, and the stopped value M_tau."""
    n_paths = states["spot"].shape[0]
    steps = contract.steps
    dt = contract.maturity / steps
    increments = np.zeros((n_paths, steps), dtype=float)
    for time_index in range(1, steps + 1):
        model = models[time_index]
        fitted = model.predict(states, contract)
        conditional = model.expectation(
            states,
            contract,
            contract.rate,
            contract.dividend,
            contract.volatility,
            dt,
        )
        increments[:, time_index - 1] = np.exp(-contract.rate * time_index * dt) * (
            fitted - conditional
        )
    martingale_path = np.column_stack(
        (np.zeros(n_paths), np.cumsum(increments, axis=1))
    )
    stopped = martingale_path[np.arange(n_paths), evaluation.stopping_indices]
    return increments, martingale_path, stopped


def apply_control_variate(
    evaluation: PolicyEvaluation, stopped_martingale: Array, coefficient: float = 1.0
) -> Array:
    if coefficient != 1.0:
        raise ValueError("the primary estimator fixes the martingale coefficient at one")
    return evaluation.discounted_payoffs - stopped_martingale
