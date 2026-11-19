# STAT 906: Martingale control variates for Bermudan option pricing

This project compares an ordinary least-squares Monte Carlo (LSMC) exercise
policy with a fixed-policy-value martingale control variate for (1) a vanilla
Bermudan put under risk-neutral GBM and (2) an arithmetic-average Bermudan
Asian put. The CV is inspired by Ehrlichman and Henderson (2007), but uses a
restricted additive hinge spline, is fitted separately after the LSM policy,
and does **not** implement full MARS, LDA-MARS, the CV-enhanced stopping
regression, or the martingale-dual upper bound.

The reported estimator targets the value of the *same frozen exercise
policy*. It is not, in general, an unbiased estimate of the optimal Bermudan
price. A good CV reduces Monte Carlo sampling variance; it does not repair
policy approximation bias, and a variance-reduction factor below one is a
valid result.

## Reproduce

From this directory, in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts/run_tests.py --output results/smoke
python scripts/run_smoke.py --output results/smoke
python -m stat906cv.experiments --config configs/core.yaml --output results/core
python scripts/make_tables_figures.py results/core
```

The smoke run must pass its saved numerical validation checks before the core
run is interpreted. The full core grid uses independent policy-fit,
value-fit/validation, and pricing streams; 30 independent pricing
replications at each required path count; common paths for paired estimator
comparisons within a replication; and one frozen fit per scenario. Wall-clock
times depend on hardware and should not be compared directly with EH's R
implementation.

Run `python -m stat906cv.experiments --help` for CLI options. Configurations,
resolved seeds, environment metadata, raw replication results, diagnostics,
figures, and interpretation notes are saved below the chosen result
directory. Detailed equations, source mapping, validation, and deviations are
in `docs/`. The completed core-run analysis is in
[`docs/results_interpretation.md`](docs/results_interpretation.md), with
execution details in [`docs/run_manifest.md`](docs/run_manifest.md).
