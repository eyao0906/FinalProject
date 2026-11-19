# Run interpretation: smoke

Numerical validation status: **PASS**.
This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.

## Per-scenario findings

### asian_put_k95

- At N=1000, plain mean=2.79485 (replication t interval 2.32395 to 3.26575).
  linear_cv: mean=2.71359, median VRF=2.263, mean stopped-martingale estimate=0.08126, mean total CPU=0.005208s/replication.
  spline_cv: mean=2.73873, median VRF=75.81, mean stopped-martingale estimate=0.05612, mean total CPU=0.005208s/replication.

### vanilla_atm_sigma20

- At N=1000, plain mean=2.34819 (replication t interval 2.07572 to 2.62066).
  linear_cv: mean=2.29572, median VRF=2.753, mean stopped-martingale estimate=0.05247, mean total CPU=0s/replication.
  spline_cv: mean=2.28402, median VRF=95.96, mean stopped-martingale estimate=0.06417, mean total CPU=0s/replication.
- Same-date Bermudan CRR references: 1200 steps=2.2970702, 2400 steps=2.2971256.

## Interpretation limits

- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.
- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.
- A VRF below one is retained and means this fitted control increased path-payoff variance.
- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.
