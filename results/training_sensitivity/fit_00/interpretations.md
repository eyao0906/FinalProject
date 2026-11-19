# Run interpretation: fit_00

Numerical validation status: **PASS**.
This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.

## Per-scenario findings

### asian_put_k115

- At N=20000, plain mean=15.9003 (replication t interval 15.8294 to 15.9712).
  linear_cv: mean=15.875, median VRF=16.05, mean stopped-martingale estimate=0.02528, mean total CPU=0.01875s/replication.
  spline_cv: mean=15.895, median VRF=76.53, mean stopped-martingale estimate=0.005258, mean total CPU=0.05312s/replication.

### asian_put_k95

- At N=20000, plain mean=2.75063 (replication t interval 2.70437 to 2.79689).
  linear_cv: mean=2.74906, median VRF=2.165, mean stopped-martingale estimate=0.001572, mean total CPU=0.01562s/replication.
  spline_cv: mean=2.74074, median VRF=94.74, mean stopped-martingale estimate=0.009892, mean total CPU=0.05312s/replication.

### vanilla_atm_sigma20

- At N=20000, plain mean=2.30079 (replication t interval 2.27872 to 2.32287).
  linear_cv: mean=2.29471, median VRF=2.632, mean stopped-martingale estimate=0.006089, mean total CPU=0.025s/replication.
  spline_cv: mean=2.29316, median VRF=153.2, mean stopped-martingale estimate=0.007637, mean total CPU=0.07187s/replication.
- Same-date Bermudan CRR references: 1200 steps=2.2970702, 2400 steps=2.2971256.

### vanilla_atm_sigma40

- At N=20000, plain mean=5.28978 (replication t interval 5.23081 to 5.34875).
  linear_cv: mean=5.29119, median VRF=2.501, mean stopped-martingale estimate=-0.001416, mean total CPU=0.02187s/replication.
  spline_cv: mean=5.28698, median VRF=151.6, mean stopped-martingale estimate=0.002801, mean total CPU=0.05625s/replication.
- Same-date Bermudan CRR references: 1200 steps=5.2918968, 2400 steps=5.2921543.

### vanilla_itm_spot36_sigma20

- At N=20000, plain mean=4.43393 (replication t interval 4.40697 to 4.4609).
  linear_cv: mean=4.43761, median VRF=3.434, mean stopped-martingale estimate=-0.003677, mean total CPU=0.01875s/replication.
  spline_cv: mean=4.43969, median VRF=151.8, mean stopped-martingale estimate=-0.005753, mean total CPU=0.06563s/replication.
- Same-date Bermudan CRR references: 1200 steps=4.4505512, 2400 steps=4.4502549.

### vanilla_otm_spot44_sigma20

- At N=20000, plain mean=1.09359 (replication t interval 1.07032 to 1.11687).
  linear_cv: mean=1.09234, median VRF=1.908, mean stopped-martingale estimate=0.001252, mean total CPU=0.01562s/replication.
  spline_cv: mean=1.09604, median VRF=38.03, mean stopped-martingale estimate=-0.002445, mean total CPU=0.05625s/replication.
- Same-date Bermudan CRR references: 1200 steps=1.1009802, 2400 steps=1.1008922.

## Interpretation limits

- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.
- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.
- A VRF below one is retained and means this fitted control increased path-payoff variance.
- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.
