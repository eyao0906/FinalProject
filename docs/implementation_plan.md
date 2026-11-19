# Phase 0 implementation plan

1. **Audit and map.** Preserve the approved scope and reference equations in
   `source_mapping.md`; record the legacy revision and defects before writing
   numerical code.
2. **Repair the stopping-policy layer in the new project.** Implement exact
   monthly GBM and the approved Asian state; fit backward on realized
   one-step-discounted cashflows; evaluate the frozen policy forward; add
   matched-date Bermudan CRR. Gate CV work on recursion, discounting,
   first-exercise, toy-policy, and tree-refinement tests.
3. **Implement and test the EH-inspired CV.** On independent value-training
   paths, construct frozen-policy value labels at every future start date;
   fit linear and training-quantile additive-spline approximations; code
   exact shifted-lognormal hinge expectations; test stopped-martingale means
   and plain/CV agreement on independent paths.
4. **Run FAST smoke before any production run.** Save configuration, seeds,
   test diagnostics, per-replication records, and representative pathwise
   corrections. Treat material validation failures as a stop condition.
5. **Run the required core grid.** Reuse one policy/CV fit per scenario;
   run independent pricing replications at both specified path counts,
   paired across estimators; compare vanilla prices against the same-grid
   Bermudan reference and report Asian values only as frozen-policy estimates.
6. **Analyze and hand off.** Export raw replication summaries, estimates and
   intervals, fit/martingale/exercise diagnostics, benchmark convergence,
   figures, tables, run manifest, findings, and explicit limitations.
   Leave the optional basket out unless both required experiments and their
   validation gates complete.

The expected Python environment is the selected local Python 3.14 interpreter.
If the approved core grid exceeds the available execution budget, retain the
smoke artifacts, record the exact blocker and partial run state, and do not
silently present a smoke run as production results.
