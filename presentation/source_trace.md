# Source trace

All project results below are read from committed saved data. The chart builder does not re-run pricing or modify scientific outputs.

| Displayed item | Auditable source and selection | Notes |
|:--|:--|:--|
| Four vanilla and two Asian contracts; path budgets; replication count | `results/core_20261118/config_resolved.yaml`; `results/core_20261118/summary.csv` | Vanilla: ATM at 20%/40%, ITM \(S_0=36\), OTM \(S_0=44\); Asian: \(K=95,115\). |
| 20k policy fit, 20k value fit, 5k validation | `results/core_20261118/config_resolved.yaml` | Independent policy, value-fit, validation, and pricing streams are described in `docs/methods.md`. |
| 26 tests passed | `results/smoke/pytest_output.txt` | Recorded pytest run. |
| 57/57 core numerical checks passed; maximum \(|\text{mean}|/\text{SE}=2.8652\) | `results/core_20261118/validation.json` | `checks` array; all checks passed. |
| Main VRF chart and six-scenario range | `results/core_20261118/summary.csv`; filter `n_paths=20000`, methods `linear_cv` and `spline_cv`, field `median_vrf` | Chart values are sourced directly by `build_assets.py`; VRF is variance ratio, not price accuracy or SE ratio. |
| ATM vanilla point estimates and 95% intervals | `results/core_20261118/summary.csv`; `scenario=vanilla_atm_sigma20`, `n_paths=20000`, methods `plain` and `spline_cv`, fields `mean_price`, `replicate_ci_lower`, `replicate_ci_upper` | Intervals are Student-t across 30 independent pricing replications, conditional on one frozen training fit. |
| Matched monthly Bermudan CRR reference | `results/core_20261118/reference_prices.csv`; `scenario=vanilla_atm_sigma20`, `benchmark=same-grid monthly Bermudan CRR`, `tree_steps=2400` | The CRR benchmark permits exercise on the same 13 monthly dates. |
| Asian estimates and VRFs | `results/core_20261118/summary.csv`; `n_paths=20000`, Asian scenario IDs `asian_put_k95` and `asian_put_k115`, method `spline_cv` | No exact Asian Bermudan price or upper bound is available. |
| CPU-adjusted efficiency chart | `results/core_20261118/summary.csv`; `n_paths=20000`, CV methods, field `aggregate_cpu_adjusted_efficiency` | Includes allocated training costs; hardware-specific Windows timing. |
| Five-training-fit sensitivity range | `results/training_sensitivity/sensitivity_summary.csv`; method `spline_cv`, field `median_vrf_across_fits` | Five independent training fits; separate from the single-fit conditional pricing intervals. |
| Vanilla sensitivity backup | `results/core_20261118/summary.csv`; vanilla rows, both path counts, both CV methods, field `median_vrf` | Two panels show 5,000 and 20,000 pricing paths. |
| Correction illustration backup | `results/core_20261118/figures/martingale_correction_vanilla.png` | Existing audited plot: representative 512-path subset from replication 0 of the saved \(N=5{,}000\) archive; its plotted VRF is not the full-run result. |
| Fixed-policy and Asian-state definitions | `docs/methods.md` | Includes \(\tau^\pi\), \(Y\), \(M_\tau\), Asian average excluding \(S_0\), and conditional hinge expectations. |
| EH theorem, spline, and Asian comparison | Ehrlichman & Henderson (2007), §§2.2 (Proposition 2.1), 3–3.1, and 5.1; cited by DOI in the deck | Project method is a restricted fixed-knot spline CV, not the paper's full adaptive MARS, policy improvement, or dual upper bound. |
| LSM background | Longstaff & Schwartz (2001), cited by DOI in the deck | Supporting reference only; EH is the central paper. |
