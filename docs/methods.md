# Methods and estimator definitions

## Risk-neutral dynamics and contracts

Under the risk-neutral measure, the single stock follows

\[
S_{k+1}=S_k\exp\{(r-q-\tfrac12\sigma^2)\Delta+
\sigma\sqrt{\Delta}Z_{k+1}\},\qquad Z_{k+1}\sim N(0,1),
\quad \Delta=T/m .
\]

Thus `E[S_(k+1)|F_k] = S_k exp((r-q) Delta)`. Prices are simulated on the
exact monthly grid with independent standard-normal innovations. There are no
historical market observations or calibrated market quotes in this
experiment.

The vanilla contract is a put with K=40, r=.06, q=0, T=1, and exercise dates
k=0,...,12. Its payoff is `g_k=(K-S_k)+`. Its pricing comparator is a CRR
tree that takes 1200 or 2400 internal steps but permits exercise only at the
same 13 monthly dates. European Black-Scholes and continuously exercisable
CRR prices are lower and upper sanity references, respectively; neither is
the matched Bermudan reference.

For the arithmetic-average Asian put, S0=100, T=.5, six monthly dates, and
the running average is

\[
A_k=\frac{1}{k}\sum_{j=1}^k S_j
=\frac{(k-1)A_{k-1}+S_k}{k},\quad A_1=S_1 .
\]

The time-zero spot is deliberately excluded. The payoff at an allowed date
is `(K-A_k)+`; there is no exercise at time zero. `(S_k,A_k)` is the Markov
state. The two strikes, 95 and 115, are fixed in the resolved configuration.
No exact Asian Bermudan price or upper bound is asserted.

## Bermudan stopping and LSM policy

For a fixed state process and admissible stopping time tau, the policy value
at date k is

\[
L_k^\pi=E[e^{-r(\tau_k-k\Delta)}g_{\tau_k}\mid F_k],
\]

where tau_k means the first exercise selected by the frozen policy when
starting at k. An optimal Bermudan value satisfies the Snell recursion
`V_m=g_m`, `V_k=max(g_k, exp(-r Delta) E[V_(k+1)|F_k])`; the LSM regression
approximates continuation to obtain a feasible, generally suboptimal policy.

The backward policy fit starts from the maturity payoff. At each date
`k=m-1,...,1`, it first forms
`target = exp(-r Delta) * CF_(k+1)` for every training path, regresses that
realized continuation cashflow on current state features using only positive
payoff (in-the-money) paths, and replaces the target by current intrinsic
value on paths chosen to exercise. Every path remains in the recursion:
exercise at an earlier date supersedes any later candidate. If the vanilla
contract allows exercise at time zero, the deterministic immediate payoff is
compared with the average discounted continuation cashflow; no singular
constant-state regression is fit.

Out-of-sample application is forward, not backward. The frozen policy scans
eligible dates in order and records exactly the first exercise, or maturity
if it never exercises earlier. The selected payoff is discounted from its
actual exercise index to time zero. Conditional on the independent training
fit, the mean of this payoff estimates the value of that fixed policy (a
lower bound in expectation on the optimal Bermudan price), not necessarily
the optimal price.

## EH-inspired stopped-martingale control variate

EH (2007), §2.2, Proposition 2.1 and Eq. (4), define for functions h_k of the
Markov state

\[
M_0=0,\qquad
M_k=\sum_{j=1}^k e^{-rt_j}
\{h_j(X_j)-E[h_j(X_j)\mid F_{j-1}]\},\quad t_j=j\Delta .
\]

Each increment is conditionally mean zero, hence M is a martingale. For the
bounded stopping time tau induced by the frozen policy, optional sampling
gives `E[M_tau]=0`. Therefore `Y_cv=Y-M_tau` and
`Y=e^{-r tau}g_tau` have the same expectation conditional on the independent
policy/value training data. If h_k equals the frozen-policy value L_k^pi,
EH Proposition 2.1 shows that the stopped martingale is a perfect control
variate for this policy value. An approximate h can reduce variance when it
tracks the policy value and its correction is suitably correlated with Y;
reduction is not guaranteed. The CV changes sampling variance, not exercise
decisions, and cannot remove policy approximation bias.

The experiment uses coefficient one, with no pricing-sample tuning. It
reports plain LSMC and two CVs on exactly the same pricing paths: a low-order
linear function and the primary restricted additive hinge spline. The policy
fit, value fit, validation data, and pricing paths use disjoint seed streams.
For each fixed scenario, one policy and one pair of value models are reused
across N and independent pricing replications; inference over those
replications is conditional on those fits.

Value-training labels are not terminal payoffs or continuation-only targets.
For each date, a backward realized-policy recursion sets the maturity label
to the payoff, then sets the date-k label to intrinsic value if the frozen
policy exercises at k, or to `exp(-r Delta)` times the realized label at
k+1 otherwise. This constructs realized samples of L_k^pi at every
starting date. The value-fit sample is split by independent simulation into
fit and holdout sets; knots and coefficients use only the fit sample.

## Additive degree-one spline and tractable expectations

For each nonterminal date, the restricted spline is

\[
h_k(x)=a_{k,0}+\sum_{d}\sum_\ell
\{b^+_{k,d,\ell}(x_d-c_{k,d,\ell})_+
b^-_{k,d,\ell}(c_{k,d,\ell}-x_d)_+\}.
\]

Each state coordinate is divided by strike before fitting. Three
training-only quantiles (.25, .50, .75) are used as candidate knots; duplicate
quantiles are removed. A linear additive model is fitted as an ablation.
OLS uses least squares; structurally identical state coordinates at the
first Asian date are reduced to one coordinate, and rank/condition diagnostics
are saved. Rank-deficient or ill-conditioned spline designs receive a small
ridge penalty, leaving the intercept unpenalized; the amount and condition
number are recorded. The terminal h is the exact payoff, not an estimated
regression.

For a spot hinge at threshold H>0, with
\[
d_1=\frac{\log(s/H)+(r-q+\sigma^2/2)\Delta}{\sigma\sqrt{\Delta}},
\quad d_2=d_1-\sigma\sqrt{\Delta},
\]
the undiscounted conditional expectations are

\[
E[(S_{k+1}-H)_+\mid S_k=s]
=s e^{(r-q)\Delta}\Phi(d_1)-H\Phi(d_2),
\]
\[
E[(H-S_{k+1})_+\mid S_k=s]
=H\Phi(-d_2)-s e^{(r-q)\Delta}\Phi(-d_1).
\]

For H<=0 the call expectation is `s exp((r-q) Delta)-H` and the put
expectation is zero. At zero volatility or zero time increment the
conditional expectation is evaluated at the deterministic forward value.
These are undiscounted conditional expectations; the martingale increment
then applies its own `exp(-r t_k)` factor.

For a normalized spot coordinate `S/K`, a knot c corresponds to spot
threshold `Kc`; divide its call/put expectation by K. For a normalized Asian
coordinate `A_k/K`, an average hinge at knot c satisfies

\[
(A_k-cK)_+=\frac{(S_k-H)_+}{k},\qquad
(cK-A_k)_+=\frac{(H-S_k)_+}{k},\quad
H=kcK-(k-1)A_{k-1}.
\]

Thus the corresponding conditional expectations are the same shifted
lognormal spot call/put expectations divided by k (and by K when the
coordinate is normalized). This is an arithmetic-level hinge construction;
EH §5.1 instead uses a log-geometric-average transformation for its Asian
illustration. No nested Monte Carlo is used.

## Uncertainty, efficiency, and interpretation

For each independent pricing replication, the standard error is
`sample_sd(path_payoffs)/sqrt(N)` and the corresponding displayed interval is
the normal 95% path-sample interval. Variance reduction is
`Var(Y)/Var(Y-M_tau)` on paired paths. Across R independent pricing runs,
the summary reports the mean price and a Student-t 95% interval based on the
empirical replication SD. Paired replicate differences compare each CV with
plain LSMC. The two intervals answer different questions.

Marginal pricing CPU/wall time includes simulation and exercise evaluation;
CV marginal time additionally includes conditional expectation work. The
common policy-fit cost and the additional value-fit cost are amortized
equally across all N-by-replication tasks within each scenario. Both marginal
and allocated total costs are exported. The reported CPU-adjusted efficiency
is computed over the R paired replications as the sum of
`Var(Y_i)*total_CPU_plain_i` divided by the sum of
`Var(Ycv_i)*total_CPU_cv_i`; this aggregates the Windows process clock's
coarse per-call readings before computing the fixed-budget ratio. If the
aggregate CPU time is below 0.05 seconds, the efficiency is flagged
unavailable instead of reporting a spurious ratio. Timing is hardware-specific.
