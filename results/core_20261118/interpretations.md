# Run interpretation: core_20261118

Numerical validation status: **PASS**.
This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.

## Per-scenario findings

### asian_put_k115

- At N=5000, plain mean=15.8929 (replication t interval 15.8291 to 15.9568).
  linear_cv: mean=15.8928, median VRF=16.27, mean stopped-martingale estimate=0.0001566, mean total CPU=0.003385s/replication.
  spline_cv: mean=15.8929, median VRF=76.2, mean stopped-martingale estimate=6.089e-06, mean total CPU=0.01068s/replication.
- At N=20000, plain mean=15.8903 (replication t interval 15.8644 to 15.9162).
  linear_cv: mean=15.8947, median VRF=15.41, mean stopped-martingale estimate=-0.00437, mean total CPU=0.008594s/replication.
  spline_cv: mean=15.896, median VRF=75.27, mean stopped-martingale estimate=-0.005736, mean total CPU=0.04609s/replication.

### asian_put_k95

- At N=5000, plain mean=2.73886 (replication t interval 2.71776 to 2.75997).
  linear_cv: mean=2.73653, median VRF=2.175, mean stopped-martingale estimate=0.002332, mean total CPU=0.002344s/replication.
  spline_cv: mean=2.741, median VRF=94.93, mean stopped-martingale estimate=-0.002142, mean total CPU=0.0112s/replication.
- At N=20000, plain mean=2.74156 (replication t interval 2.7291 to 2.75402).
  linear_cv: mean=2.7445, median VRF=2.161, mean stopped-martingale estimate=-0.002941, mean total CPU=0.009115s/replication.
  spline_cv: mean=2.73967, median VRF=94.36, mean stopped-martingale estimate=0.001887, mean total CPU=0.04766s/replication.

### vanilla_atm_sigma20

- At N=5000, plain mean=2.28855 (replication t interval 2.27656 to 2.30053).
  linear_cv: mean=2.29377, median VRF=2.581, mean stopped-martingale estimate=-0.005221, mean total CPU=0.002865s/replication.
  spline_cv: mean=2.29288, median VRF=151.9, mean stopped-martingale estimate=-0.004337, mean total CPU=0.0138s/replication.
- At N=20000, plain mean=2.29967 (replication t interval 2.29242 to 2.30693).
  linear_cv: mean=2.29292, median VRF=2.609, mean stopped-martingale estimate=0.006759, mean total CPU=0.01328s/replication.
  spline_cv: mean=2.29281, median VRF=152.4, mean stopped-martingale estimate=0.006865, mean total CPU=0.05807s/replication.
- Same-date Bermudan CRR references: 1200 steps=2.2970702, 2400 steps=2.2971256.

### vanilla_atm_sigma40

- At N=5000, plain mean=5.28409 (replication t interval 5.2476 to 5.32058).
  linear_cv: mean=5.27983, median VRF=2.524, mean stopped-martingale estimate=0.004258, mean total CPU=0.003906s/replication.
  spline_cv: mean=5.2857, median VRF=150, mean stopped-martingale estimate=-0.00161, mean total CPU=0.01536s/replication.
- At N=20000, plain mean=5.29589 (replication t interval 5.27989 to 5.3119).
  linear_cv: mean=5.28967, median VRF=2.512, mean stopped-martingale estimate=0.006227, mean total CPU=0.01328s/replication.
  spline_cv: mean=5.28706, median VRF=151.9, mean stopped-martingale estimate=0.008831, mean total CPU=0.05964s/replication.
- Same-date Bermudan CRR references: 1200 steps=5.2918968, 2400 steps=5.2921543.

### vanilla_itm_spot36_sigma20

- At N=5000, plain mean=4.42504 (replication t interval 4.4079 to 4.44218).
  linear_cv: mean=4.43404, median VRF=3.444, mean stopped-martingale estimate=-0.009004, mean total CPU=0.003906s/replication.
  spline_cv: mean=4.43874, median VRF=150.2, mean stopped-martingale estimate=-0.0137, mean total CPU=0.0138s/replication.
- At N=20000, plain mean=4.44051 (replication t interval 4.433 to 4.44803).
  linear_cv: mean=4.43799, median VRF=3.474, mean stopped-martingale estimate=0.002523, mean total CPU=0.0112s/replication.
  spline_cv: mean=4.43915, median VRF=151.4, mean stopped-martingale estimate=0.001368, mean total CPU=0.05755s/replication.
- Same-date Bermudan CRR references: 1200 steps=4.4505512, 2400 steps=4.4502549.

### vanilla_otm_spot44_sigma20

- At N=5000, plain mean=1.10002 (replication t interval 1.0861 to 1.11393).
  linear_cv: mean=1.09988, median VRF=1.928, mean stopped-martingale estimate=0.0001361, mean total CPU=0.002344s/replication.
  spline_cv: mean=1.0958, median VRF=38.75, mean stopped-martingale estimate=0.004215, mean total CPU=0.01432s/replication.
- At N=20000, plain mean=1.09464 (replication t interval 1.08931 to 1.09997).
  linear_cv: mean=1.09538, median VRF=1.925, mean stopped-martingale estimate=-0.0007395, mean total CPU=0.01068s/replication.
  spline_cv: mean=1.09616, median VRF=38.6, mean stopped-martingale estimate=-0.001516, mean total CPU=0.05807s/replication.
- Same-date Bermudan CRR references: 1200 steps=1.1009802, 2400 steps=1.1008922.

## CPU-adjusted efficiency

The aggregate paired-replication CPU-adjusted efficiency at N=20000 is
approximately 18.48x, 19.18x, 18.47x, and 4.32x for the vanilla ATM-20%,
ATM-40%, spot-36, and spot-44 cases, respectively. For the Asian strikes it
is approximately 9.77x (K=95) and 8.10x (K=115). These ratios include
allocated training costs and aggregate the coarse Windows process-clock
measurements across 30 paired replications. Treat them as hardware-specific
indications, not portable timing benchmarks.

## Interpretation limits

- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.
- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.
- A VRF below one is retained and means this fitted control increased path-payoff variance.
- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.
