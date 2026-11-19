# Run manifest

## Reproducible commands

Run these from `stat906_adaptive_cv` in PowerShell, with the project's
editable install available:

```powershell
python scripts\run_tests.py --output results\smoke
python scripts\run_smoke.py --output results\smoke
python scripts\run_core.py --output results\core_20261118
python scripts\make_tables_figures.py results\core_20261118
```

In the recorded Windows session, `python` was not on PATH; the selected
interpreter was invoked directly as
`C:\Users\ethan\AppData\Local\Python\pythoncore-3.14-64\python.exe`.
Dependencies are declared in `pyproject.toml`.

## FAST validation run

- Run ID: `smoke`; output directory: `results/smoke/`.
- Configuration: 2,000 policy-training paths, 2,000 value-training paths,
  1,000 value-validation paths, 3 independent pricing replications of 1,000
  paths for the vanilla ATM 20% volatility and Asian K=95 cases; seed base
  9062026.
- Test result: 20 passed, no failures/errors/skips
  (`test_results.json`, `pytest.xml`).
- Quantitative validation: PASS (`validation.json`).

## Required core run

- Run ID: `core`; output directory: `results/core_20261118/`.
- Configuration: 20,000 policy-training and value-training paths, 5,000
  value-validation paths, 30 independent pricing replications at each of
  5,000 and 20,000 paths; four vanilla cases and two arithmetic-Asian strikes;
  seed base 9062026.
- The six scenarios, exact parameters, tree resolution, knots, and run
  settings are in [`config_resolved.yaml`](../results/core_20261118/config_resolved.yaml).
  Every generated seed is in
  [`seeds.csv`](../results/core_20261118/seeds.csv), including distinct
  policy-fit, value-fit, validation, and pricing streams.
- Environment and audited legacy commit are recorded in
  [`environment.json`](../results/core_20261118/environment.json).
- Quantitative validation: PASS
  ([`validation.json`](../results/core_20261118/validation.json)).
- Raw paired method estimates: 1,080 rows in
  [`per_replication.csv`](../results/core_20261118/per_replication.csv);
  aggregate estimates, confidence intervals, VRFs, costs, and timing status
  are in [`summary.csv`](../results/core_20261118/summary.csv).
- Additional saved outputs: `reference_prices.csv`,
  `policy_model_diagnostics.csv`, `model_diagnostics.csv`,
  `martingale_diagnostics.csv`, `exercise_diagnostics.csv`,
  `representative_paths.npz`, the `tables/` CSVs, six PNG/PDF figure pairs,
  and `interpretations.md`.

The optional two-asset basket experiment was not run. No separate training
seed study, full EH MARS implementation, dual upper bound, or exact
arithmetic-Asian Bermudan benchmark is included.
