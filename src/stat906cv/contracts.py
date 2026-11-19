from __future__ import annotations

from dataclasses import dataclass

import numpy as np


Array = np.ndarray
States = dict[str, Array]


@dataclass(frozen=True)
class BermudanPut:
    spot0: float
    strike: float
    rate: float
    dividend: float
    volatility: float
    maturity: float
    steps: int
    allow_initial_exercise: bool = True
    kind: str = "vanilla"

    def payoff(self, states: States, time_index: int) -> Array:
        return np.maximum(self.strike - states["spot"][:, time_index], 0.0)

    def eligible(self, time_index: int) -> bool:
        return self.allow_initial_exercise or time_index > 0

    def state_coordinates(self, states: States, time_index: int) -> dict[str, Array]:
        return {"spot": states["spot"][:, time_index] / self.strike}


@dataclass(frozen=True)
class ArithmeticAsianPut:
    spot0: float
    strike: float
    rate: float
    dividend: float
    volatility: float
    maturity: float
    steps: int
    allow_initial_exercise: bool = False
    kind: str = "asian_arithmetic"

    def payoff(self, states: States, time_index: int) -> Array:
        if time_index == 0:
            return np.zeros(states["spot"].shape[0], dtype=float)
        return np.maximum(self.strike - states["average"][:, time_index], 0.0)

    def eligible(self, time_index: int) -> bool:
        return time_index > 0

    def state_coordinates(self, states: States, time_index: int) -> dict[str, Array]:
        if time_index == 0:
            raise ValueError("the arithmetic Asian state is defined only from exercise date 1")
        return {
            "spot": states["spot"][:, time_index] / self.strike,
            "average": states["average"][:, time_index] / self.strike,
        }


def make_contract(config: dict[str, object], kind: str) -> BermudanPut | ArithmeticAsianPut:
    cls = BermudanPut if kind == "vanilla" else ArithmeticAsianPut
    return cls(
        spot0=float(config["spot"]),
        strike=float(config["strike"]),
        rate=float(config["rate"]),
        dividend=float(config["dividend"]),
        volatility=float(config["volatility"]),
        maturity=float(config["maturity"]),
        steps=int(config["steps"]),
    )


def build_states(spot_paths: Array, kind: str) -> States:
    spot_paths = np.asarray(spot_paths, dtype=float)
    states: States = {"spot": spot_paths}
    if kind == "asian_arithmetic":
        average = np.zeros_like(spot_paths)
        average[:, 1:] = np.cumsum(spot_paths[:, 1:], axis=1) / np.arange(
            1, spot_paths.shape[1], dtype=float
        )[None, :]
        states["average"] = average
    return states
