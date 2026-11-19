# Deviations and implementation hurdles

## Planned adaptations (not failures)

- The project plan authorizes a simplified low-dimensional spline control
  function. This implementation uses a training-quantile additive,
  degree-one hinge spline and a linear ablation, not full MARS. It omits
  MARS forward/backward selection, EH's LDA/projection directions, higher
  order interactions, EH's CV-enhanced stopping-rule regression, and the
  dual upper-bound calculation.
- The Asian contract follows the required arithmetic average excluding S0
  and uses exact shifted-lognormal hinge expectations. This differs from
  the log-geometric-average transformation in EH §5.1 but is tractable and
  consistent with the approved scope.
- The optional two-asset basket experiment is not part of the production
  grid. Correlated-GBM prerequisite tests cover PSD and rho=1 behavior; no
  basket prices or basket-CV results are reported.

## Validation failures found and corrected

1. **Spline conditional-expectation coefficient indexing.** The first full
   test run found an `IndexError` at a three-knot value model: expectation
   evaluation advanced its coefficient offset both inside and across the
   knot loop, requesting coefficient index 9 from a seven-coefficient
   one-coordinate spline. The offset is now fixed per coordinate and each
   knot accesses its paired plus/minus coefficients. This was caught before
   any numerical experiment output was interpreted.
2. **Terminal payoff units.** After fixing the index, the independent
   stopped-martingale test found a material nonzero mean for the full
   martingale: for 70,000 pricing paths, vanilla `mean(M_T)=2.01512` versus
   estimated SE `0.02488`; Asian `mean(M_T)=2.59445` versus SE `0.03756`.
   The nonterminal increments were centered; the exact terminal payoff
   conditional expectation had inadvertently been returned in
   strike-normalized units although `h_T` and payoffs were in currency
   units. The terminal expectations now use currency units (Asian's
   conditional expectation additionally divides by the date index).
   Subsequent test runs check both `M_T` and `M_tau` against predeclared
   six-SE tolerances.
3. **Spline collinearity.** Including positive and negative hinges at the
   same knots creates linearly dependent columns (the difference of the
   hinges is linear). This is consistent with the specified additive
   function family, but makes raw coefficient fits non-identifiable.
   The fitter records rank and condition number and uses a small
   intercept-unpenalized ridge correction when rank deficient or
   ill-conditioned. The function values and conditional expectations use
   the same fitted coefficients; no coefficient is silently dropped.

## Inference impact and remaining risks

The two test failures above invalidated the first attempted CV diagnostics;
they were not retained as pricing results and no conclusions were drawn from
them. The final validation document and run artifacts will report only
post-fix results, with the original failures preserved here for audit.
Because the evaluation replicates reuse a single independently trained
policy and value fit, the main intervals are conditional on training. A
separate training-seed study was not run; training-fit variability is
therefore not quantified. Windows process CPU readings are coarse for an
individual short replication. CPU-adjusted efficiency is consequently
calculated after aggregating paired replication costs, and is withheld when
either aggregate total is below 0.05 seconds; the resulting efficiency
figures remain hardware- and timing-method-dependent. No exact Asian
Bermudan benchmark is assumed. The continuous-American CRR price is a sanity
bound for the vanilla put, not its matched Bermudan reference.
