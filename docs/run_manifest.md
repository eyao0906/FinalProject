# Run manifest

The correction branch was created from committed `main` at
`09b05e4b4182303e043f239565537c25830c75c1`. The original core numerical CSVs
are retained and were compared automatically against that source commit.

## Reproducible commands

Run these from the repository root in PowerShell, with the project's
editable install available:

```powershell
python scripts\run_tests.py --output results\smoke
python scripts\run_smoke.py --output results\smoke
python scripts\run_core.py --output results\core_20261118
python scripts\revalidate_results.py results\core_20261118
python scripts\run_training_sensitivity.py
python scripts\make_tables_figures.py results\core_20261118
python scripts\verify_numerical_integrity.py --reference-ref main
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
- `validation_original.json` preserves the original loose criterion for
  audit; `validation.json` and `validation_corrected.json` contain the
  corrected saved-data calculations.

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

## Training-fit sensitivity run

- Output directory: `results/training_sensitivity/`.
- Five independent training fits at the original 20,000 policy-training and
  20,000 value-training sizes; five 20,000-path pricing replications per fit.
- All six scenarios are included and every seed is retained in the root
  `seeds.csv` as well as each `fit_XX/seeds.csv`.
- Each fit has its own resolved configuration, validation JSON, raw
  replications, policy/value diagnostics, and summary. Root aggregates are
  `training_fit_summary.csv`, `sensitivity_summary.csv`, and
  `core_stability_comparison.csv`.
- Training fits, not nested pricing replications, are the top-level units in
  the reported between-fit statistics.

The optional two-asset basket experiment was not run. No separate training
seed study, full EH MARS implementation, dual upper bound, or exact
arithmetic-Asian Bermudan benchmark is included.
