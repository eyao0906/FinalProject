from stat906cv.benchmarks import (
    american_put_crr,
    bermudan_put_crr,
    black_scholes_put,
)


def test_same_grid_bermudan_tree_refinement_and_price_ordering():
    prices = [
        bermudan_put_crr(40.0, 40.0, 0.06, 0.0, 0.2, 1.0, 12, steps)
        for steps in (1200, 2400, 4800)
    ]
    european = black_scholes_put(40.0, 40.0, 0.06, 0.0, 0.2, 1.0)
    continuous = [
        american_put_crr(40.0, 40.0, 0.06, 0.0, 0.2, 1.0, steps)
        for steps in (1200, 2400, 4800)
    ]
    assert abs(prices[1] - prices[0]) < 0.02
    assert abs(prices[2] - prices[1]) < 0.02
    assert european <= min(prices)
    assert max(prices) <= min(continuous) + 2e-3
    assert prices[-1] <= continuous[-1] + 2e-3
