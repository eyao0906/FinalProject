# Run interpretation: fit_01

Numerical validation status: **PASS**.
This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.

## Per-scenario findings

### asian_put_k115

- At N=20000, plain mean=15.8095 (replication t interval 15.7064 to 15.9127).
  linear_cv: mean=15.8908, median VRF=15.45, mean stopped-martingale estimate=-0.08123, mean total CPU=0.0125s/replication.
  spline_cv: mean=15.8897, median VRF=76.13, mean stopped-martingale estimate=-0.0802, mean total CPU=0.05312s/replication.

### asian_put_k95

- At N=20000, plain mean=2.75771 (replication t interval 2.72231 to 2.79312).
  linear_cv: mean=2.75031, median VRF=2.165, mean stopped-martingale estimate=0.007409, mean total CPU=0.009375s/replication.
  spline_cv: mean=2.7417, median VRF=95.63, mean stopped-martingale estimate=0.01602, mean total CPU=0.05s/replication.

### vanilla_atm_sigma20

- At N=20000, plain mean=2.30574 (replication t interval 2.26566 to 2.34582).
  linear_cv: mean=2.29437, median VRF=2.619, mean stopped-martingale estimate=0.01137, mean total CPU=0.01875s/replication.
  spline_cv: mean=2.29081, median VRF=164.6, mean stopped-martingale estimate=0.01493, mean total CPU=0.05937s/replication.
- Same-date Bermudan CRR references: 1200 steps=2.2970702, 2400 steps=2.2971256.

### vanilla_atm_sigma40

- At N=20000, plain mean=5.30831 (replication t interval 5.26549 to 5.35112).
  linear_cv: mean=5.30234, median VRF=2.492, mean stopped-martingale estimate=0.005969, mean total CPU=0.0125s/replication.
  spline_cv: mean=5.28484, median VRF=175.7, mean stopped-martingale estimate=0.02346, mean total CPU=0.05312s/replication.
- Same-date Bermudan CRR references: 1200 steps=5.2918968, 2400 steps=5.2921543.

### vanilla_itm_spot36_sigma20

- At N=20000, plain mean=4.4501 (replication t interval 4.42902 to 4.47118).
  linear_cv: mean=4.44798, median VRF=3.42, mean stopped-martingale estimate=0.002126, mean total CPU=0.02187s/replication.
  spline_cv: mean=4.44195, median VRF=146.6, mean stopped-martingale estimate=0.008148, mean total CPU=0.06563s/replication.
- Same-date Bermudan CRR references: 1200 steps=4.4505512, 2400 steps=4.4502549.

### vanilla_otm_spot44_sigma20

- At N=20000, plain mean=1.09499 (replication t interval 1.0764 to 1.11358).
  linear_cv: mean=1.09342, median VRF=1.94, mean stopped-martingale estimate=0.001576, mean total CPU=0.02813s/replication.
  spline_cv: mean=1.09625, median VRF=37.65, mean stopped-martingale estimate=-0.001259, mean total CPU=0.07187s/replication.
- Same-date Bermudan CRR references: 1200 steps=1.1009802, 2400 steps=1.1008922.

## Interpretation limits

- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.
- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.
- A VRF below one is retained and means this fitted control increased path-payoff variance.
- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.
