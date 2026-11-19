from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from stat906cv.contracts import ArithmeticAsianPut, BermudanPut, States


Array = np.ndarray
Contract = BermudanPut | ArithmeticAsianPut


@dataclass
class RegressionDiagnostic:
    time_index: int
    n_regression_paths: int
    rank: int
    n_features: int
    condition_number: float
    coefficients: Array


@dataclass
class PolicyEvaluation:
    stopping_indices: Array
    stopping_payoffs: Array
    discounted_payoffs: Array

    @property
    def price(self) -> float:
        return float(np.mean(self.discounted_payoffs))

    @property
    def standard_error(self) -> float:
        if self.discounted_payoffs.size < 2:
            return float("nan")
        return float(np.std(self.discounted_payoffs, ddof=1) / np.sqrt(self.discounted_payoffs.size))


def policy_basis(contract: Contract, states: States, time_index: int) -> Array:
    coordinates = contract.state_coordinates(states, time_index)
    if isinstance(contract, BermudanPut):
        x = coordinates["spot"]
        return np.column_stack((np.ones_like(x), x, x * x))
    spot = coordinates["spot"]
    average = coordinates["average"]
    return np.column_stack(
        (np.ones_like(spot), spot, average, spot * spot, average * average, spot * average)
    )


def _fit_ols(x: Array, y: Array) -> tuple[Array, int, float]:
    coefficients, _, rank, singular_values = np.linalg.lstsq(x, y, rcond=None)
    condition = (
        float(singular_values[0] / singular_values[-1])
        if singular_values.size and singular_values[-1] > 0.0
        else float("inf")
    )
    return coefficients, int(rank), condition


def backward_cashflow_step(
    next_date_cashflow: Array, intrinsic: Array, discount: float, exercise: Array
) -> Array:
    """One realized-cashflow recursion step; every path remains eligible to replace later exercise."""
    continuation_target = discount * next_date_cashflow
    return np.where(exercise, intrinsic, continuation_target)


@dataclass
class FittedLSMPolicy:
    contract: Contract
    dt: float
    regression_map: dict[int, Array]
    t0_exercise: bool

    def decision(self, states: States, time_index: int) -> Array:
        n_paths = states["spot"].shape[0]
        if not self.contract.eligible(time_index):
            return np.zeros(n_paths, dtype=bool)
        intrinsic = self.contract.payoff(states, time_index)
        if time_index == 0:
            return np.full(n_paths, self.t0_exercise, dtype=bool)
        beta = self.regression_map.get(time_index)
        if beta is None:
            return np.zeros(n_paths, dtype=bool)
        continuation = policy_basis(self.contract, states, time_index) @ beta
        return (intrinsic > 0.0) & (intrinsic >= continuation)

    def evaluate(self, states: States, rate: float | None = None) -> PolicyEvaluation:
        n_paths = states["spot"].shape[0]
        steps = states["spot"].shape[1] - 1
        stopping_indices = np.full(n_paths, steps, dtype=int)
        active = np.ones(n_paths, dtype=bool)
        stopping_payoffs = self.contract.payoff(states, steps).copy()
        if self.contract.eligible(0) and self.t0_exercise:
            stopping_indices[:] = 0
            stopping_payoffs[:] = self.contract.payoff(states, 0)
            active[:] = False
        for time_index in range(1, steps):
            if not np.any(active):
                break
            exercise = active & self.decision(states, time_index)
            if np.any(exercise):
                stopping_indices[exercise] = time_index
                stopping_payoffs[exercise] = self.contract.payoff(states, time_index)[exercise]
                active[exercise] = False
        discount_rate = self.contract.rate if rate is None else rate
        discounted = np.exp(-discount_rate * self.dt * stopping_indices) * stopping_payoffs
        return PolicyEvaluation(stopping_indices, stopping_payoffs, discounted)


@dataclass
class PolicyFit:
    policy: FittedLSMPolicy
    diagnostics: list[RegressionDiagnostic]
    training_cashflows: Array
    training_stopping_indices: Array
    training_price: float


def fit_lsm_policy(
    states: States,
    contract: Contract,
    minimum_regression_paths: int = 200,
) -> PolicyFit:
    n_paths = states["spot"].shape[0]
    steps = states["spot"].shape[1] - 1
    dt = contract.maturity / steps
    discount = float(np.exp(-contract.rate * dt))
    cashflow = contract.payoff(states, steps).copy()
    stopping = np.full(n_paths, steps, dtype=int)
    regression_map: dict[int, Array] = {}
    diagnostics: list[RegressionDiagnostic] = []

    for time_index in range(steps - 1, 0, -1):
        intrinsic = contract.payoff(states, time_index)
        itm = intrinsic > 0.0
        beta: Array | None = None
        if contract.eligible(time_index) and int(itm.sum()) >= minimum_regression_paths:
            design = policy_basis(contract, states, time_index)
            beta, rank, condition = _fit_ols(design[itm], discount * cashflow[itm])
            regression_map[time_index] = beta
            diagnostics.append(
                RegressionDiagnostic(
                    time_index=time_index,
                    n_regression_paths=int(itm.sum()),
                    rank=rank,
                    n_features=design.shape[1],
                    condition_number=condition,
                    coefficients=beta,
                )
            )
        exercise = np.zeros(n_paths, dtype=bool)
        if beta is not None:
            exercise = itm & (intrinsic >= policy_basis(contract, states, time_index) @ beta)
        cashflow = backward_cashflow_step(cashflow, intrinsic, discount, exercise)
        stopping[exercise] = time_index

    t0_exercise = False
    if contract.eligible(0):
        intrinsic0 = contract.payoff(states, 0)
        continuation0 = discount * float(np.mean(cashflow))
        immediate0 = float(np.mean(intrinsic0))
        t0_exercise = immediate0 > 0.0 and immediate0 >= continuation0
        if t0_exercise:
            cashflow = intrinsic0.copy()
            stopping[:] = 0

    policy = FittedLSMPolicy(contract, dt, regression_map, t0_exercise)
    selected_payoffs = contract.payoff(states, steps).copy()
    for time_index in range(steps):
        selected = stopping == time_index
        if np.any(selected):
            selected_payoffs[selected] = contract.payoff(states, time_index)[selected]
    discounted = np.exp(-contract.rate * dt * stopping) * selected_payoffs
    return PolicyFit(
        policy=policy,
        diagnostics=sorted(diagnostics, key=lambda row: row.time_index),
        training_cashflows=discounted,
        training_stopping_indices=stopping,
        training_price=float(np.mean(discounted)),
    )
