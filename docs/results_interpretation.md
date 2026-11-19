# Core results interpretation

## What was estimated

The core grid contains four vanilla and two arithmetic-average Asian
Bermudan-put cases, two pricing sizes (5,000 and 20,000), and 30 independent
pricing replications per size. Each replication compares plain LSMC, a
linear control, and the primary restricted spline control on paired paths:
1,080 method/replication rows total. Policy and value fits are frozen per
scenario and use separate training/validation streams from pricing. Thus
replication intervals quantify pricing-sample uncertainty conditional on
those fitted models, not total uncertainty over retraining.

The t intervals below are across the 30 replication prices. The separate
pathwise intervals in the raw rows quantify Monte Carlo error within an
individual replication. The CV is designed to estimate the value of the
same frozen policy; it does not change exercise decisions or remove policy
approximation bias.

## Main findings

1. **The vanilla benchmark is aligned and stable.** The 1200/2400-step
   monthly-exercise CRR estimates differ by at most 0.00030 in all four
   vanilla cases. For the ATM 20% case, the matched Bermudan reference is
   2.297070/2.297126; European Black–Scholes is 2.066401 and the continuous
   American tree is 2.319328/2.319453. The ordering is consistent with the
   contracts and the tree refinement gate passes.

2. **The vanilla LSMC estimates are close to the matched reference.** At
   20,000 pricing paths, the spline-CV mean prices (with 95% replication
   intervals) are: ATM, sigma 20%: 2.29281 [2.29213, 2.29349]; ATM,
   sigma 40%: 5.28706 [5.28600, 5.28812]; spot 36: 4.43915
   [4.43862, 4.43967]; and spot 44: 1.09616 [1.09534, 1.09697]. These are
   fixed-policy values, not asserted optimal prices. Every core policy/
   reference diagnostic passes its predeclared tolerance; the largest
   observed absolute gap is 0.01748.

3. **Vanilla spline CVs substantially reduce path variance.** At N=20,000,
   the median variance-reduction factors are 152.42, 151.85, 151.45, and
   38.60 for ATM sigma 20%, ATM sigma 40%, spot 36, and spot 44,
   respectively. The linear ablation is much weaker (median VRF about
   1.93–3.47). The lower OTM reduction is a material moneyness sensitivity,
   not a failed run.

4. **The Asian results have no exact-price benchmark in this study.** At
   N=20,000, for strike 95 the plain, linear-CV, and spline-CV means are
   2.74156 [2.72910, 2.75402], 2.74450 [2.73619, 2.75281], and 2.73967
   [2.73833, 2.74101]. For strike 115 they are 15.89030 [15.86441,
   15.91619], 15.89467 [15.88908, 15.90026], and 15.89604 [15.89255,
   15.89952]. Report these only as estimated values of their respective
   frozen LSM policies; no exact Bermudan Asian value or optimality claim is
   available.

5. **The spline is consistently stronger than the linear ablation for the
   Asian cases.** At N=20,000, median VRF is 94.36 for K=95 and 75.27 for
   K=115, versus 2.16 and 15.41 for the linear control. The difference
   between strikes shows that even the linear control is contract-dependent.

6. **Price estimates remain statistically compatible across estimators.**
   Paired 95% t intervals for spline-minus-plain replication-price
   differences include zero in the named examples: vanilla ATM sigma 20%,
   -0.00686 [-0.01403, 0.00030]; Asian K=95, -0.00189 [-0.01466,
   0.01088]; Asian K=115, +0.00574 [-0.02067, 0.03214]. This is expected
   because the martingale correction is centered conditional on independent
   training; the CV changes variance, not the target expectation. These
   finite-replication intervals are not proof of unbiasedness.

7. **Stopped-martingale diagnostics pass.** All core independent
   replication means are within six estimated path standard errors. The
   maximum absolute z-score across vanilla and Asian cases is 2.87. The
   corresponding means, standard deviations, correlations, and per-rep
   diagnostics are in `martingale_diagnostics.csv`; an aggregate validation
   is in `validation.json`.

8. **CPU-adjusted efficiency remains favorable for the spline at 20,000
   paths, after accounting for its extra work.** This is the aggregate
   paired-replication ratio
   `sum(Var(Y_i)*CPU_plain_i) / sum(Var(Ycv_i)*CPU_cv_i)`, including allocated
   training costs. It is approximately 18.48x, 19.18x, 18.47x, and 4.32x for
   the four vanilla scenarios, and 9.77x (K=95) and 8.10x (K=115) for Asian.
   The linear controls range from 1.18x to 2.18x. These timing ratios are
   hardware-specific and indicative: the Windows process clock is coarse
   for individual short calls, so costs are aggregated across 30 paired
   replications and a 0.05-second aggregate floor is enforced. Do not treat
   them as portable benchmarks.

## Files and figures

- [`summary.csv`](../results/core_20261118/summary.csv): means, replication
  intervals, paired differences, VRFs, timing costs, and aggregate
  CPU-efficiency status.
- [`per_replication.csv`](../results/core_20261118/per_replication.csv):
  unaggregated paired estimates.
- [`reference_prices.csv`](../results/core_20261118/reference_prices.csv):
  matched Bermudan, European, and continuous-American references.
- [`tables/`](../results/core_20261118/tables/): presentation-oriented
  estimator, VRF, and martingale tables.
- [`figures/price_confidence_intervals.png`](../results/core_20261118/figures/price_confidence_intervals.png),
  [`figures/vrf_vanilla_by_size_volatility.png`](../results/core_20261118/figures/vrf_vanilla_by_size_volatility.png),
  [`figures/vrf_asian_vs_vanilla.png`](../results/core_20261118/figures/vrf_asian_vs_vanilla.png),
  [`figures/standard_error_vs_cpu.png`](../results/core_20261118/figures/standard_error_vs_cpu.png),
  [`figures/exercise_time_histograms.png`](../results/core_20261118/figures/exercise_time_histograms.png),
  and the two `martingale_correction_*.png` files.

## Limitations for the report

This is not a full reproduction of Ehrlichman and Henderson's adaptive
MARS/LDA-MARS method: it uses an additive degree-one hinge spline with
training-quantile knots. The Asian state is arithmetic and excludes S0, as
approved, rather than the paper's log-geometric transformation. The optional
basket experiment, EH CV-enhanced stopping regression, dual upper bound,
exact Asian benchmark, and independent training-seed sensitivity were not
run. The first two test-discovered defects and their fixes are documented in
[`deviations_and_hurdles.md`](deviations_and_hurdles.md).
