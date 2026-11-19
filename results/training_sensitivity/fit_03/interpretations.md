# Run interpretation: fit_03

Numerical validation status: **PASS**.
This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.

## Per-scenario findings

### asian_put_k115

- At N=20000, plain mean=15.9025 (replication t interval 15.8521 to 15.953).
  linear_cv: mean=15.8874, median VRF=16.11, mean stopped-martingale estimate=0.01509, mean total CPU=0.0125s/replication.
  spline_cv: mean=15.8894, median VRF=75.48, mean stopped-martingale estimate=0.01317, mean total CPU=0.05312s/replication.

### asian_put_k95

- At N=20000, plain mean=2.75979 (replication t interval 2.72665 to 2.79293).
  linear_cv: mean=2.7705, median VRF=2.178, mean stopped-martingale estimate=-0.01071, mean total CPU=0.009375s/replication.
  spline_cv: mean=2.74163, median VRF=96.8, mean stopped-martingale estimate=0.01815, mean total CPU=0.05s/replication.

### vanilla_atm_sigma20

- At N=20000, plain mean=2.28858 (replication t interval 2.27453 to 2.30263).
  linear_cv: mean=2.28615, median VRF=2.619, mean stopped-martingale estimate=0.00243, mean total CPU=0.02187s/replication.
  spline_cv: mean=2.29119, median VRF=157, mean stopped-martingale estimate=-0.002606, mean total CPU=0.06875s/replication.
- Same-date Bermudan CRR references: 1200 steps=2.2970702, 2400 steps=2.2971256.

### vanilla_atm_sigma40

- At N=20000, plain mean=5.29453 (replication t interval 5.26471 to 5.32435).
  linear_cv: mean=5.27653, median VRF=2.534, mean stopped-martingale estimate=0.018, mean total CPU=0.02187s/replication.
  spline_cv: mean=5.28867, median VRF=171, mean stopped-martingale estimate=0.005858, mean total CPU=0.0625s/replication.
- Same-date Bermudan CRR references: 1200 steps=5.2918968, 2400 steps=5.2921543.

### vanilla_itm_spot36_sigma20

- At N=20000, plain mean=4.44148 (replication t interval 4.40854 to 4.47441).
  linear_cv: mean=4.43736, median VRF=3.353, mean stopped-martingale estimate=0.004119, mean total CPU=0.01875s/replication.
  spline_cv: mean=4.44384, median VRF=152, mean stopped-martingale estimate=-0.002365, mean total CPU=0.06563s/replication.
- Same-date Bermudan CRR references: 1200 steps=4.4505512, 2400 steps=4.4502549.

### vanilla_otm_spot44_sigma20

- At N=20000, plain mean=1.09938 (replication t interval 1.08482 to 1.11394).
  linear_cv: mean=1.09197, median VRF=1.908, mean stopped-martingale estimate=0.007412, mean total CPU=0.01875s/replication.
  spline_cv: mean=1.09991, median VRF=40.18, mean stopped-martingale estimate=-0.0005226, mean total CPU=0.0625s/replication.
- Same-date Bermudan CRR references: 1200 steps=1.1009802, 2400 steps=1.1008922.

## Interpretation limits

- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.
- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.
- A VRF below one is retained and means this fitted control increased path-payoff variance.
- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.
