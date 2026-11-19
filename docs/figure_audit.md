# Figure audit

| Output | Old defect | Replacement and interpretation |
|---|---|---|
| `vrf_asian_vs_vanilla` | Overlapping points at only two sample sizes; scenario identity unclear. | Six-scenario grouped bars at N=20,000, log VRF scale, direct values, and VRF=1 reference. Main presentation result: spline controls strongly reduce payoff variance. |
| `vrf_vanilla_by_size_volatility` | Connected unrelated moneyness and volatility scenarios. | Two categorical panels: ATM volatility and fixed-volatility moneyness. It tests sensitivity without implying a continuous relation. |
| `price_confidence_intervals` | Common scale obscured intervals for low-priced options. | Six independent x-axis facets with 95% Student-t replication intervals; matched CRR only for vanilla. Shows precision gains without claiming an optimal price. |
| `standard_error_vs_cpu` | Pooled unlike contracts and dollar scales. | Scenario grouped bars of aggregate CPU-adjusted efficiency, reliability-gated and referenced to one. Timing remains approximate and hardware-specific. |
| `exercise_time_histograms` | Only one representative per contract and one replication. | Six scenario panels pooled across 30 20,000-path replications, with maturity, eligibility, and fitted-policy interpretation. |
| `martingale_correction_vanilla` | Overlapping before/after histograms hid the spread change. | Separate payoff-correction, plain, and adjusted panels from the exact 512-path archive, with sample SD, correlation, and sample VRF. Explains the mechanism. |
| `martingale_correction_asian_arithmetic` | Same overlap and unsupported full-run implication. | Separate aligned panels and explicit N=5,000 replication-0 archive provenance. |

All PNGs are exported at 300 DPI with vector PDFs. Figure data are written to
presentation-specific CSVs in `results/core_20261118/tables/` and selected
directly from `summary.csv`, `reference_prices.csv`,
`exercise_diagnostics.csv`, and `representative_paths.npz`.

## Recommended presentation figures

1. `vrf_asian_vs_vanilla`: main evidence that the spline CV reduces variance.
2. `price_confidence_intervals`: precision improvement and remaining
   fixed-policy/reference gap.
3. `martingale_correction_vanilla`: the mechanism behind the control.
4. `exercise_time_histograms` or `standard_error_vs_cpu`: policy behavior or
   hardware-specific computational trade-off, depending on time available.
