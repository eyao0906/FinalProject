# Run interpretation: fit_04

Numerical validation status: **PASS**.
This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.

## Per-scenario findings

### asian_put_k115

- At N=20000, plain mean=15.8826 (replication t interval 15.8357 to 15.9295).
  linear_cv: mean=15.8949, median VRF=15.32, mean stopped-martingale estimate=-0.01232, mean total CPU=0.01875s/replication.
  spline_cv: mean=15.8909, median VRF=72.5, mean stopped-martingale estimate=-0.008317, mean total CPU=0.04375s/replication.

### asian_put_k95

- At N=20000, plain mean=2.72149 (replication t interval 2.70106 to 2.74191).
  linear_cv: mean=2.72139, median VRF=2.16, mean stopped-martingale estimate=9.495e-05, mean total CPU=0.01562s/replication.
  spline_cv: mean=2.74069, median VRF=93.86, mean stopped-martingale estimate=-0.0192, mean total CPU=0.04688s/replication.

### vanilla_atm_sigma20

- At N=20000, plain mean=2.28787 (replication t interval 2.27408 to 2.30166).
  linear_cv: mean=2.29687, median VRF=2.517, mean stopped-martingale estimate=-0.009001, mean total CPU=0.025s/replication.
  spline_cv: mean=2.29335, median VRF=156.6, mean stopped-martingale estimate=-0.005476, mean total CPU=0.06875s/replication.
- Same-date Bermudan CRR references: 1200 steps=2.2970702, 2400 steps=2.2971256.

### vanilla_atm_sigma40

- At N=20000, plain mean=5.27274 (replication t interval 5.22444 to 5.32105).
  linear_cv: mean=5.26574, median VRF=2.596, mean stopped-martingale estimate=0.007008, mean total CPU=0.01875s/replication.
  spline_cv: mean=5.28768, median VRF=178, mean stopped-martingale estimate=-0.01494, mean total CPU=0.06563s/replication.
- Same-date Bermudan CRR references: 1200 steps=5.2918968, 2400 steps=5.2921543.

### vanilla_itm_spot36_sigma20

- At N=20000, plain mean=4.42791 (replication t interval 4.40133 to 4.4545).
  linear_cv: mean=4.4516, median VRF=3.341, mean stopped-martingale estimate=-0.02369, mean total CPU=0.02187s/replication.
  spline_cv: mean=4.4427, median VRF=149.8, mean stopped-martingale estimate=-0.01479, mean total CPU=0.06875s/replication.
- Same-date Bermudan CRR references: 1200 steps=4.4505512, 2400 steps=4.4502549.

### vanilla_otm_spot44_sigma20

- At N=20000, plain mean=1.10718 (replication t interval 1.08907 to 1.12529).
  linear_cv: mean=1.09843, median VRF=1.942, mean stopped-martingale estimate=0.008749, mean total CPU=0.01875s/replication.
  spline_cv: mean=1.09619, median VRF=36.42, mean stopped-martingale estimate=0.01099, mean total CPU=0.05937s/replication.
- Same-date Bermudan CRR references: 1200 steps=1.1009802, 2400 steps=1.1008922.

## Interpretation limits

- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.
- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.
- A VRF below one is retained and means this fitted control increased path-payoff variance.
- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.
