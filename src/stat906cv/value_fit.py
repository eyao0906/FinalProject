from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from stat906cv.contracts import ArithmeticAsianPut, BermudanPut, States
from stat906cv.hinge_expectations import (
    lognormal_call_put_hinges,
    scaled_average_hinges,
    scaled_spot_hinges,
)
from stat906cv.lsm_policy import FittedLSMPolicy


Array = np.ndarray
Contract = BermudanPut | ArithmeticAsianPut


def policy_value_labels(states: States, policy: FittedLSMPolicy, contract: Contract) -> Array:
    """Realized frozen-policy payoff in local date-k units for every starting date k."""
    steps = contract.steps
    labels = np.zeros((states["spot"].shape[0], steps + 1), dtype=float)
    labels[:, steps] = contract.payoff(states, steps)
    discount = float(np.exp(-contract.rate * policy.dt))
    for time_index in range(steps - 1, 0, -1):
        exercise = policy.decision(states, time_index)
        labels[:, time_index] = np.where(
            exercise,
            contract.payoff(states, time_index),
            discount * labels[:, time_index + 1],
        )
    return labels


def _features(
    states: States,
    time_index: int,
    contract: Contract,
    kind: str,
    coordinates: tuple[str, ...],
    knots: dict[str, Array],
) -> tuple[Array, list[str]]:
    state = contract.state_coordinates(states, time_index)
    n_paths = states["spot"].shape[0]
    columns = [np.ones(n_paths, dtype=float)]
    names = ["intercept"]
    if kind == "linear":
        for coordinate in coordinates:
            columns.append(state[coordinate])
            names.append(f"linear:{coordinate}")
    else:
        for coordinate in coordinates:
            for knot in knots[coordinate]:
                values = state[coordinate]
                columns.extend((np.maximum(values - knot, 0.0), np.maximum(knot - values, 0.0)))
                names.extend((f"{coordinate}:plus@{knot:.12g}", f"{coordinate}:minus@{knot:.12g}"))
    return np.column_stack(columns), names


@dataclass
class ValueModel:
    time_index: int
    model_kind: str
    contract_kind: str
    strike: float
    coefficient: Array
    coordinates: tuple[str, ...]
    knots: dict[str, Array]
    feature_names: list[str]
    training_mse: float
    validation_mse: float
    condition_number: float
    rank: int
    regularization: float
    n_terms: int
    terminal_exact: bool = False

    def predict(self, states: States, contract: Contract) -> Array:
        if self.terminal_exact:
            return contract.payoff(states, self.time_index)
        design, _ = _features(
            states, self.time_index, contract, self.model_kind, self.coordinates, self.knots
        )
        return design @ self.coefficient

    def expectation(
        self,
        states: States,
        contract: Contract,
        rate: float,
        dividend: float,
        volatility: float,
        dt: float,
    ) -> Array:
        previous_spot = states["spot"][:, self.time_index - 1]
        if self.terminal_exact:
            if isinstance(contract, BermudanPut):
                _, expected_put = lognormal_call_put_hinges(
                    previous_spot, contract.strike, rate, dividend, volatility, dt
                )
                return expected_put
            previous_average = states["average"][:, self.time_index - 1]
            threshold = self.time_index * contract.strike - (
                self.time_index - 1
            ) * previous_average
            _, expected_put = lognormal_call_put_hinges(
                previous_spot, threshold, rate, dividend, volatility, dt
            )
            return expected_put / self.time_index

        result = np.full(previous_spot.shape[0], self.coefficient[0], dtype=float)
        for coordinate_index, coordinate in enumerate(self.coordinates):
            if self.model_kind == "linear":
                slope = self.coefficient[coordinate_index + 1]
                result += slope * _expected_coordinate(
                    states, contract, coordinate, self.time_index, rate, dividend, volatility, dt
                )
                continue
            offset = 1
            for prior_coordinate in self.coordinates[:coordinate_index]:
                offset += 2 * len(self.knots[prior_coordinate])
            for knot_index, knot in enumerate(self.knots[coordinate]):
                plus_beta = self.coefficient[offset + 2 * knot_index]
                minus_beta = self.coefficient[offset + 2 * knot_index + 1]
                if coordinate == "spot":
                    plus, minus = scaled_spot_hinges(
                        previous_spot, float(knot), contract.strike,
                        rate, dividend, volatility, dt,
                    )
                else:
                    plus, minus = scaled_average_hinges(
                        previous_spot,
                        states["average"][:, self.time_index - 1],
                        self.time_index,
                        float(knot),
                        contract.strike,
                        rate,
                        dividend,
                        volatility,
                        dt,
                    )
                result += plus_beta * plus + minus_beta * minus
        return result


def _expected_coordinate(
    states: States,
    contract: Contract,
    coordinate: str,
    time_index: int,
    rate: float,
    dividend: float,
    volatility: float,
    dt: float,
) -> Array:
    expected_spot = states["spot"][:, time_index - 1] * np.exp((rate - dividend) * dt)
    if coordinate == "spot":
        return expected_spot / contract.strike
    expected_average = (
        (time_index - 1) * states["average"][:, time_index - 1] + expected_spot
    ) / (time_index * contract.strike)
    return expected_average


def _active_coordinates(states: States, contract: Contract, time_index: int) -> tuple[str, ...]:
    coordinates = contract.state_coordinates(states, time_index)
    names = list(coordinates)
    active = [names[0]]
    for name in names[1:]:
        if not np.allclose(coordinates[name], coordinates[active[0]], rtol=0.0, atol=1e-12):
            active.append(name)
    return tuple(active)


def _fit_model(
    model_kind: str,
    time_index: int,
    train_states: States,
    train_labels: Array,
    validation_states: States,
    validation_labels: Array,
    contract: Contract,
    knots_quantiles: tuple[float, ...],
) -> ValueModel:
    coordinates = _active_coordinates(train_states, contract, time_index)
    knots = {
        coordinate: (
            np.quantile(
                contract.state_coordinates(train_states, time_index)[coordinate], knots_quantiles
            )
            if model_kind == "spline"
            else np.empty(0)
        )
        for coordinate in coordinates
    }
    for coordinate, values in knots.items():
        knots[coordinate] = np.unique(values.astype(float))
    design, feature_names = _features(train_states, time_index, contract, model_kind, coordinates, knots)
    coefficients, _, rank, singular_values = np.linalg.lstsq(design, train_labels, rcond=None)
    condition = (
        float(singular_values[0] / singular_values[-1])
        if singular_values.size and singular_values[-1] > 0.0
        else float("inf")
    )
    regularization = 0.0
    if rank < design.shape[1] or condition > 1e10:
        gram = design.T @ design
        regularization = 1e-8 * max(float(np.trace(gram)) / max(gram.shape[0], 1), 1.0)
        penalty = np.eye(gram.shape[0]) * regularization
        penalty[0, 0] = 0.0
        coefficients = np.linalg.solve(gram + penalty, design.T @ train_labels)
    training_residual = design @ coefficients - train_labels
    validation_design, _ = _features(
        validation_states, time_index, contract, model_kind, coordinates, knots
    )
    validation_residual = validation_design @ coefficients - validation_labels
    return ValueModel(
        time_index=time_index,
        model_kind=model_kind,
        contract_kind=contract.kind,
        strike=contract.strike,
        coefficient=coefficients,
        coordinates=coordinates,
        knots=knots,
        feature_names=feature_names,
        training_mse=float(np.mean(training_residual**2)),
        validation_mse=float(np.mean(validation_residual**2)),
        condition_number=condition,
        rank=int(rank),
        regularization=regularization,
        n_terms=design.shape[1] - 1,
    )


def fit_value_models(
    train_states: States,
    validation_states: States,
    policy: FittedLSMPolicy,
    contract: Contract,
    knots_quantiles: tuple[float, ...],
) -> tuple[dict[str, dict[int, ValueModel]], list[dict[str, object]]]:
    train_labels = policy_value_labels(train_states, policy, contract)
    validation_labels = policy_value_labels(validation_states, policy, contract)
    all_models: dict[str, dict[int, ValueModel]] = {"linear": {}, "spline": {}}
    diagnostics: list[dict[str, object]] = []
    for model_kind in all_models:
        for time_index in range(1, contract.steps + 1):
            if time_index == contract.steps:
                coordinates = ("spot",) if isinstance(contract, BermudanPut) else ("average",)
                exact = ValueModel(
                    time_index=time_index,
                    model_kind="terminal_exact",
                    contract_kind=contract.kind,
                    strike=contract.strike,
                    coefficient=np.array([1.0]),
                    coordinates=coordinates,
                    knots={},
                    feature_names=["known_terminal_payoff"],
                    training_mse=0.0,
                    validation_mse=0.0,
                    condition_number=1.0,
                    rank=1,
                    regularization=0.0,
                    n_terms=1,
                    terminal_exact=True,
                )
                model = exact
            else:
                model = _fit_model(
                    model_kind,
                    time_index,
                    train_states,
                    train_labels[:, time_index],
                    validation_states,
                    validation_labels[:, time_index],
                    contract,
                    knots_quantiles,
                )
            all_models[model_kind][time_index] = model
            diagnostics.append(
                {
                    "time_index": time_index,
                    "model": model_kind,
                    "coordinates": list(model.coordinates),
                    "knots": {name: values.tolist() for name, values in model.knots.items()},
                    "coefficients": model.coefficient.tolist(),
                    "feature_names": model.feature_names,
                    "training_mse": model.training_mse,
                    "validation_mse": model.validation_mse,
                    "condition_number": model.condition_number,
                    "rank": model.rank,
                    "n_features": len(model.coefficient),
                    "regularization": model.regularization,
                    "n_terms": model.n_terms,
                    "terminal_exact": model.terminal_exact,
                }
            )
    return all_models, diagnostics
