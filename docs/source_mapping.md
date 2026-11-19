# Source-to-implementation mapping

## Reference and scope

The approved experiment scope is `STAT906_Project_Plan_Ethan.qmd`; assessment
context is `ProjectRequirement.txt`. The primary method is Ehrlichman and
Henderson (2007, hereafter EH), *Adaptive Control Variates for Pricing
Multi-Dimensional American Options*. The supporting policy-pricing reference
is Longstaff and Schwartz (2001, hereafter LS), *Valuing American Options by
Simulation: A Simple Least-Squares Approach*. Both supplied PDF files were
available locally and were text-extracted for review. The old project was
audited at commit `aa4d025d05db285c74c8ef03f6e587884a8f5f6f`; its worktree was
clean.

## Faithful mathematical elements

| Paper location | Mathematical element | Planned implementation |
|---|---|---|
| EH §2, Bermudan value recursion | Markov state, discounted optimal-stopping problem, and exercise-date recursion | `contracts.py` defines monthly Bermudan put payoffs and eligibility; `lsm_policy.py` fits a frozen suboptimal exercise policy. |
| EH §2.1, Eq. (2); LS §2.2 | Backward LSM regression of realized discounted future cashflows on current state, using in-the-money paths | `lsm_policy.py` regresses the one-step-discounted realized future cashflow on an in-the-money training subset. Every path remains in the cashflow recursion so an earlier exercise can replace a later candidate. |
| LS §2.2 and §3 | Apply a fitted stopping rule forward, take the first eligible exercise, and discount its realized payoff to time zero | `FittedLSMPolicy.evaluate` will scan dates in chronological order and return the unique stopping index, payoff, and discounted payoff. |
| EH §2.2, Proposition 2.1, Eq. (4) | A value-function martingale yields a perfect control variate when the value approximation equals the frozen-policy value | `martingale.py` computes the discounted one-step increments and subtracts the martingale stopped at the frozen policy's exercise time. |
| EH §3, Eqs. (6)–(8) | Additive degree-one hinge splines permit analytical conditional expectations of each one-dimensional hinge | `value_fit.py` uses a small training-quantile additive spline; `hinge_expectations.py` evaluates its GBM spot and Asian-average conditional expectations without nested simulation. |
| EH §4.2, Algorithms 1–2 | Separate training from pricing; freeze fitted functions and evaluate the policy and martingale on new paths | The experiment runner uses independent policy-fit, value-fit/validation, and pricing streams and paired pathwise plain/CV outcomes. |
| EH §5.1, Eq. (14) | Arithmetic-average Asian state updated at exercise dates; exclude time zero from the average | `contracts.py` sets `A_1=S_1` and `A_k=((k-1)A_{k-1}+S_k)/k`, with state `(S_k,A_k)`. |
| LS §3; EH §2.1 | Compare an approximate exercise-policy value (lower-bound target) with a correctly matched reference | `benchmarks.py` will provide a monthly-exercise Bermudan CRR reference separately from the continuous-exercise American CRR sanity reference and European Black–Scholes reference. |

## Valid simplifications and adaptations

1. EH's general martingale construction is retained, but the control-function
   family is a restricted additive, degree-one hinge spline with three knots
   selected from training-only quantiles. A low-order linear control-function
   ablation uses the same policy and pricing paths.
2. EH's Phase 1 jointly uses an approximate martingale to improve stopping
   regression (Eq. (11) and Algorithm 1). Here the ordinary LS policy is fit
   first, then held fixed; a separate value-training sample supplies realized
   frozen-policy payoff labels for the CV fit. This isolates the variance
   reduction effect on a common policy and avoids leaking the CV fit into the
   policy comparison.
3. EH §5.1 transforms the Asian state using log spot and log geometric
   average. This study instead uses the approved arithmetic average and
   additive hinges in `(S,A)`. Conditional on the prior state,
   `A_k=( (k-1)A_{k-1}+S_k )/k`; hence an average hinge at `c` is a shifted
   lognormal spot hinge with threshold `k*c-(k-1)A_{k-1}`, scaled by `1/k`.
   This is an analytically valid adaptation for the approved arithmetic
   contract, not the paper's geometric-average transformation.
4. The primary variance-reduction coefficient is fixed at one. Multiple
   evaluation replications reuse a single independently trained policy and
   CV model per scenario, so reported replication variability is conditional
   on those fits. A separate training-seed sensitivity is not included.
5. Same-grid monthly Bermudan CRR is added because the legacy repository's
   CRR and finite-difference routines exercise at every tree step. Tree
   refinement values are a numerical reference, not a proof of convergence.

## Excluded elements

- Full adaptive MARS forward selection/backward pruning, higher-order
  interactions, EH's LDA/projection directions, and its CV-enhanced stopping
  regression are not implemented. Therefore this is not a reproduction of EH
  or its published variance/time-reduction factors.
- EH's martingale-dual upper-bound estimator is excluded. No upper bound or
  exact optimal Asian price is claimed.
- EH's optional two-asset basket experiment is excluded from the core run.
  The required vanilla and arithmetic-average Asian experiments take priority.
- Legacy antithetic inference, historical downloaded prices, jump-to-ruin
  cases, pre-started averages, and old result tables are excluded.

## Legacy-code provenance and audit

The legacy source is under
`Pricing-American-Put-Options-with-Least-Squares-Monte-Carlo/src/LongstaffMethod/`.
`simulators.py` uses `numpy.random.default_rng` and exact-grid lognormal GBM,
but defaults to antithetics and its average helper includes time zero; those
behaviors are not reused for primary inference. `basis.py` supplies candidate
Laguerre/state-basis ideas, but no legacy regression result is reused.

`lsm_engine.py` was not reused: it multiplies cashflows only on paths marked
alive during its backward recursion, and `FittedLSMPolicy.evaluate` scans
backwards and locks later exercises before earlier decisions. Both are
inconsistent with backward realized-cashflow recursion and forward first
exercise. Existing Asian scripts use a pre-started average/lockout and are
not the approved contract. `benchmarks.py` implements continuously
exercisable CRR/FD references, not the same-date Bermudan comparator. These
findings motivate a clean implementation under `stat906_adaptive_cv/`;
no legacy prices or CSV outputs are imported.
