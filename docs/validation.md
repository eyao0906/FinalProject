# Validation record

## Test protocol

The Phase 1 gate verifies backward realized-cashflow replacement, forward
first exercise, correct time-zero eligibility, one discounted payoff per
path, ITM-only regression counts, and convergence/order of a same-date
Bermudan CRR tree against its 1200/2400/4800-step refinements.

The numerical gates verify GBM moments and dividend drift; arithmetic Asian
averages; spot and shifted-average hinge expectations against independent
conditional simulation; finite/rank-aware value fitting; zero-mean
`M_T`/`M_tau` for fixed independent fits; exact zero-control-variate behavior;
and detection of an intentionally broken martingale increment.

## Test and run results

The final focused suite has **20 passed, 0 failed, 0 errors, 0 skipped**.
The machine-readable result is
[`test_results.json`](../results/smoke/test_results.json), with JUnit output
in [`pytest.xml`](../results/smoke/pytest.xml) and captured output in
[`pytest_output.txt`](../results/smoke/pytest_output.txt). The suite covers
the corrected backward LSM recursion and forward first-exercise policy
evaluation, tree alignment/refinement, exact conditional expectations,
martingale centering, value fit diagnostics, and aggregate timing metrics.

The FAST run's numerical checks all pass:
[`validation.json`](../results/smoke/validation.json). This includes
European/Bermudan/continuous-American ordering, a 0.0000554 tree refinement
difference, a 0.0511 policy/reference gap (within its predeclared 0.50
tolerance), finite outputs, and stopped-martingale replication z-scores no
larger than 1.60 for vanilla and 2.25 for Asian.

The required core run's checks all pass:
[`validation.json`](../results/core_20261118/validation.json). Across the
four vanilla cases, 1200-vs-2400-step Bermudan-tree differences range from
0.0000554 to 0.0002963; policy/reference gaps range from 0.00216 to 0.01748.
Across all six scenarios and both CV methods, every pricing replication's
stopped-martingale mean is within six path standard errors; the largest
absolute z-score is 2.87. All reported prices, standard errors, and path
standard deviations are finite.

The timing summary does not use a per-call CPU ratio: the Windows process
clock's short-run readings are coarse. It aggregates `Var(Y)*CPU_plain` and
`Var(Ycv)*CPU_cv` over the paired replications and flags the efficiency
unavailable if either aggregate CPU total is below 0.05 seconds. This keeps
smoke-scale timings from being presented as reliable.
