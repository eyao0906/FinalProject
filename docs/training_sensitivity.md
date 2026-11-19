# Training-seed sensitivity

## Design

The study in [`results/training_sensitivity/`](../results/training_sensitivity/)
uses all six core scenarios, five independently seeded policy/value training
fits, 20,000 policy-training paths, 20,000 value-training paths, 5,000
validation paths, and five 20,000-path pricing replications per fit. Plain,
linear-CV, and spline-CV estimators share pricing paths within each
replication. Seeds for every stream are recorded. No original core file was
overwritten.

The training fit—not an individual pricing replication—is the top-level
independent unit. `sensitivity_summary.csv` reports between-fit SD/SE and a
five-fit Student-t interval, while separately retaining the mean within-fit
pricing SE. The 25 nested pricing replications are not treated as 25
interchangeable training experiments.

## Findings

1. **Large spline VRFs remain robust across training fits.** Across-fit
   median spline VRFs are approximately 157.0 (vanilla ATM 20%), 171.0
   (vanilla ATM 40%), 149.8 (vanilla ITM), 37.7 (vanilla OTM), 95.6 (Asian
   K=95), and 75.5 (Asian K=115). Between-fit SDs of mean VRF are modest
   relative to those levels except for ATM 40%, where the SD is 10.8.

2. **Linear-control conclusions are also stable but much weaker.**
   Across-fit median linear VRFs range from about 1.93 to 15.73. The Asian
   K=115 case remains the strongest linear-control case.

3. **Training variability is important for some narrow conditional
   intervals.** The original 20,000-path core mean lies inside the
   five-fit sensitivity interval for 15 of 18 scenario/method combinations.
   The exceptions are spline CV for vanilla ITM, Asian K=95, and Asian
   K=115. The discrepancies are small in price units, but demonstrate why a
   narrow single-fit CI must not be presented as total uncertainty.

4. **Between-fit and within-fit uncertainty have different magnitudes.**
   For spline vanilla estimates, between-fit price SDs are about 1.2–2.2
   times the mean within-fit pricing SE; for the Asian K=95 spline the
   between-fit SD is smaller than its mean within-fit SE. This supports
   reporting both sources instead of combining them mechanically.

5. **Vanilla policy gaps remain consistent with lower-bound behavior.**
   Mean spline gaps versus refined monthly Bermudan CRR are negative in all
   four cases: −0.208%, −0.098%, −0.187%, and −0.311% for ATM 20%, ATM 40%,
   ITM, and OTM, respectively. These are empirical policy-approximation gaps;
   a CV does not improve the stopping rule.

The complete fit-level and comparison tables are
[`training_fit_summary.csv`](../results/training_sensitivity/training_fit_summary.csv),
[`sensitivity_summary.csv`](../results/training_sensitivity/sensitivity_summary.csv),
and
[`core_stability_comparison.csv`](../results/training_sensitivity/core_stability_comparison.csv).

## Limits

Five fits provide a useful pilot sensitivity check, not a precise variance
component estimate. It uses the same model family and knot schedule in every
fit, so it does not quantify basis-choice/model-selection uncertainty.
Two-level bootstrap or hierarchical variance-component inference was not
added. Policy approximation error, training uncertainty, and nested pricing
uncertainty remain distinct quantities.
