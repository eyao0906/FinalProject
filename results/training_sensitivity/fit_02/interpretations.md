# Run interpretation: fit_02

Numerical validation status: **PASS**.
This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.

## Per-scenario findings

### asian_put_k115

- At N=20000, plain mean=15.8429 (replication t interval 15.7425 to 15.9434).
  linear_cv: mean=15.8881, median VRF=15.73, mean stopped-martingale estimate=-0.04522, mean total CPU=0.01875s/replication.
  spline_cv: mean=15.8902, median VRF=72.79, mean stopped-martingale estimate=-0.04731, mean total CPU=0.04688s/replication.

### asian_put_k95

- At N=20000, plain mean=2.73052 (replication t interval 2.71162 to 2.74941).
  linear_cv: mean=2.73484, median VRF=2.166, mean stopped-martingale estimate=-0.004324, mean total CPU=0.01875s/replication.
  spline_cv: mean=2.7407, median VRF=97.87, mean stopped-martingale estimate=-0.01018, mean total CPU=0.04688s/replication.

### vanilla_atm_sigma20

- At N=20000, plain mean=2.30077 (replication t interval 2.28427 to 2.31727).
  linear_cv: mean=2.30346, median VRF=2.561, mean stopped-martingale estimate=-0.002688, mean total CPU=0.01875s/replication.
  spline_cv: mean=2.29329, median VRF=159.2, mean stopped-martingale estimate=0.007487, mean total CPU=0.05625s/replication.
- Same-date Bermudan CRR references: 1200 steps=2.2970702, 2400 steps=2.2971256.

### vanilla_atm_sigma40

- At N=20000, plain mean=5.25219 (replication t interval 5.22552 to 5.27887).
  linear_cv: mean=5.27518, median VRF=2.505, mean stopped-martingale estimate=-0.02299, mean total CPU=0.01562s/replication.
  spline_cv: mean=5.28669, median VRF=164.2, mean stopped-martingale estimate=-0.0345, mean total CPU=0.05937s/replication.
- Same-date Bermudan CRR references: 1200 steps=5.2918968, 2400 steps=5.2921543.

### vanilla_itm_spot36_sigma20

- At N=20000, plain mean=4.43729 (replication t interval 4.41311 to 4.46147).
  linear_cv: mean=4.44002, median VRF=3.391, mean stopped-martingale estimate=-0.002728, mean total CPU=0.02187s/replication.
  spline_cv: mean=4.44145, median VRF=146, mean stopped-martingale estimate=-0.004156, mean total CPU=0.06563s/replication.
- Same-date Bermudan CRR references: 1200 steps=4.4505512, 2400 steps=4.4502549.

### vanilla_otm_spot44_sigma20

- At N=20000, plain mean=1.10387 (replication t interval 1.09361 to 1.11412).
  linear_cv: mean=1.10457, median VRF=1.934, mean stopped-martingale estimate=-0.0007065, mean total CPU=0.01875s/replication.
  spline_cv: mean=1.09898, median VRF=34.54, mean stopped-martingale estimate=0.004888, mean total CPU=0.0625s/replication.
- Same-date Bermudan CRR references: 1200 steps=1.1009802, 2400 steps=1.1008922.

## Interpretation limits

- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.
- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.
- A VRF below one is retained and means this fitted control increased path-payoff variance.
- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.
