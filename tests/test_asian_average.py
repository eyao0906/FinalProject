import numpy as np

from stat906cv.contracts import ArithmeticAsianPut, build_states


def test_asian_average_uses_only_observations_after_valuation_time():
    paths = np.array([[100.0, 101.0, 103.0, 99.0, 105.0, 100.0, 110.0]])
    states = build_states(paths, "asian_arithmetic")
    np.testing.assert_allclose(
        states["average"][0, 1:],
        [101.0, 102.0, 101.0, 102.0, 101.6, 103.0],
    )
    assert states["average"][0, 1] == paths[0, 1]
    assert states["average"][0, 1] != np.mean(paths[0, :2])
    contract = ArithmeticAsianPut(100.0, 105.0, 0.06, 0.0, 0.3, 0.5, 6)
    coordinates = contract.state_coordinates(states, 1)
    np.testing.assert_allclose(coordinates["spot"], [101.0 / 105.0])
    np.testing.assert_allclose(coordinates["average"], [101.0 / 105.0])
    assert contract.payoff(states, 0)[0] == 0.0
