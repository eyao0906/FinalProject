from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import scipy
import yaml

from stat906cv.benchmarks import american_put_crr, bermudan_put_crr, black_scholes_put
from stat906cv.contracts import ArithmeticAsianPut, BermudanPut, build_states, make_contract
from stat906cv.gbm import simulate_gbm
from stat906cv.lsm_policy import PolicyFit, fit_lsm_policy
from stat906cv.martingale import apply_control_variate, martingale_correction
from stat906cv.plots import make_figures
from stat906cv.statistics import summarize_replications
from stat906cv.value_fit import ValueModel, fit_value_models


METHODS = ("plain", "linear_cv", "spline_cv")
ROLES = {"policy_fit": 11, "value_fit": 21, "value_validation": 22, "pricing": 31}
CPU_TIMING_FLOOR_SECONDS = 0.05


def _seed(base_seed: int, scenario_index: int, role: str, replicate: int = 0, size_index: int = 0) -> int:
    sequence = np.random.SeedSequence(
        [base_seed, scenario_index, ROLES[role], replicate, size_index]
    )
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def _timer() -> tuple[float, float]:
    return time.process_time(), time.perf_counter()


def _elapsed(start: tuple[float, float]) -> tuple[float, float]:
    return time.process_time() - start[0], time.perf_counter() - start[1]


def _simulate_states(contract: BermudanPut | ArithmeticAsianPut, n_paths: int, seed: int) -> dict[str, np.ndarray]:
    spot_paths = simulate_gbm(
        contract.spot0,
        contract.rate,
        contract.dividend,
        contract.volatility,
        contract.maturity,
        contract.steps,
        n_paths,
        np.random.default_rng(seed),
    )
    return build_states(spot_paths, contract.kind)


def _fit_scenario(
    config: dict[str, Any],
    scenario: dict[str, Any],
    contract_kind: str,
    scenario_index: int,
    seed_rows: list[dict[str, Any]],
) -> tuple[Any, PolicyFit, dict[str, dict[int, ValueModel]], list[dict[str, Any]], dict[str, float]]:
    contract = make_contract(scenario, contract_kind)
    seed_policy = _seed(int(config["base_seed"]), scenario_index, "policy_fit")
    seed_value = _seed(int(config["base_seed"]), scenario_index, "value_fit")
    seed_validation = _seed(int(config["base_seed"]), scenario_index, "value_validation")
    seed_rows.extend(
        [
            {"scenario": scenario["id"], "role": "policy_fit", "replicate": 0, "n_paths": config["policy_training"], "seed": seed_policy},
            {"scenario": scenario["id"], "role": "value_fit", "replicate": 0, "n_paths": config["value_training"], "seed": seed_value},
            {"scenario": scenario["id"], "role": "value_validation", "replicate": 0, "n_paths": config["value_validation"], "seed": seed_validation},
        ]
    )
    fit_start = _timer()
    policy_states = _simulate_states(contract, int(config["policy_training"]), seed_policy)
    policy_fit = fit_lsm_policy(
        policy_states, contract, minimum_regression_paths=int(config["minimum_regression_paths"])
    )
    policy_cpu, policy_wall = _elapsed(fit_start)

    value_start = _timer()
    train_states = _simulate_states(contract, int(config["value_training"]), seed_value)
    validation_states = _simulate_states(contract, int(config["value_validation"]), seed_validation)
    models, model_diagnostics = fit_value_models(
        train_states,
        validation_states,
        policy_fit.policy,
        contract,
        tuple(float(q) for q in config["knots_quantiles"]),
    )
    value_cpu, value_wall = _elapsed(value_start)
    for diagnostic in model_diagnostics:
        diagnostic.update(
            {
                "scenario": scenario["id"],
                "contract": contract.kind,
                "model_fit_cpu_seconds": value_cpu,
                "model_fit_wall_seconds": value_wall,
                "policy_training_paths": int(config["policy_training"]),
                "value_training_paths": int(config["value_training"]),
                "value_validation_paths": int(config["value_validation"]),
            }
        )
    timings = {
        "policy_fit_cpu_seconds": policy_cpu,
        "policy_fit_wall_seconds": policy_wall,
        "value_fit_cpu_seconds": value_cpu,
        "value_fit_wall_seconds": value_wall,
    }
    return contract, policy_fit, models, model_diagnostics, timings


def _vanilla_references(contract: BermudanPut, tree_steps: list[int]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = [
        {
            "scenario": "",
            "benchmark": "European Black-Scholes put",
            "tree_steps": 0,
            "price": black_scholes_put(
                contract.spot0, contract.strike, contract.rate, contract.dividend,
                contract.volatility, contract.maturity,
            ),
            "exercise_grid": "maturity only",
        }
    ]
    for steps in tree_steps:
        refs.append(
            {
                "scenario": "",
                "benchmark": "same-grid monthly Bermudan CRR",
                "tree_steps": steps,
                "price": bermudan_put_crr(
                    contract.spot0, contract.strike, contract.rate, contract.dividend,
                    contract.volatility, contract.maturity, contract.steps, int(steps),
                ),
                "exercise_grid": f"0..{contract.steps}, stride={steps // contract.steps}",
            }
        )
        refs.append(
            {
                "scenario": "",
                "benchmark": "continuous-exercise American CRR sanity reference",
                "tree_steps": steps,
                "price": american_put_crr(
                    contract.spot0, contract.strike, contract.rate, contract.dividend,
                    contract.volatility, contract.maturity, int(steps),
                ),
                "exercise_grid": f"0..{steps}",
            }
        )
    for row in refs:
        row["scenario"] = ""
    return refs


def martingale_validation_checks(replications: pd.DataFrame) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    cv_replications = replications[replications["method"] != "plain"]
    columns = ["scenario", "method", "n_paths"]
    for keys, group in cv_replications.groupby(columns, sort=True):
        scenario, method, n_paths = keys
        martingale_se = (
            pd.to_numeric(group["martingale_sd"], errors="coerce")
            / np.sqrt(pd.to_numeric(group["n_paths"], errors="coerce"))
        )
        valid = (
            np.isfinite(martingale_se)
            & (martingale_se > 0)
            & np.isfinite(group["mean_martingale"].to_numpy(dtype=float))
        )
        if valid.any():
            z_scores = (
                np.abs(group.loc[valid, "mean_martingale"].to_numpy(dtype=float))
                / martingale_se.loc[valid].to_numpy(dtype=float)
            )
            max_z = float(np.max(z_scores))
            mean_martingale = float(group.loc[valid, "mean_martingale"].mean())
            passed = bool(max_z <= 6.0 and valid.all())
        else:
            max_z = float("nan")
            mean_martingale = float("nan")
            passed = False
        checks.append(
            {
                "scenario": scenario,
                "method": method,
                "n_paths": int(n_paths),
                "check": f"stopped_martingale_mean_{method}",
                "value": {
                    "max_abs_mean_over_se": max_z,
                    "mean_across_replications": mean_martingale,
                    "valid_replications": int(valid.sum()),
                    "replications": int(len(group)),
                },
                "passed": passed,
                "tolerance": (
                    "each replication has finite positive martingale SE and "
                    "|mean(M_tau)| <= 6 estimated path standard errors; "
                    "this is a numerical screening diagnostic, not a proof of "
                    "unbiasedness"
                ),
            }
        )
    return checks


def benchmark_comparison_table(
    summary: pd.DataFrame, references: pd.DataFrame
) -> pd.DataFrame:
    crr = references[
        references["benchmark"] == "same-grid monthly Bermudan CRR"
    ]
    crr_values = (
        crr.groupby("scenario")["price"]
        .agg(reference_price="last", tree_refinement_difference=lambda x: abs(x.iloc[-1] - x.iloc[0]))
        .reset_index()
    )
    vanilla = summary[summary["contract"] == "vanilla"].copy()
    comparison = vanilla.merge(crr_values, on="scenario", how="left", validate="many_to_one")
    comparison["gap"] = comparison["mean_price"] - comparison["reference_price"]
    comparison["relative_gap_percent"] = (
        100.0 * comparison["gap"] / comparison["reference_price"]
    )
    comparison["replicate_se"] = comparison["replicate_sd"] / np.sqrt(
        comparison["replications"]
    )
    comparison["replicate_half_width"] = (
        comparison["replicate_ci_upper"] - comparison["replicate_ci_lower"]
    ) / 2.0
    comparison["lower_bound_violation_margin"] = (
        comparison["gap"]
        - comparison["replicate_half_width"]
        - comparison["tree_refinement_difference"]
    )
    comparison["possible_lower_bound_violation"] = (
        comparison["lower_bound_violation_margin"] > 0
    )
    return comparison


def benchmark_validation_checks(
    summary: pd.DataFrame, references: pd.DataFrame, benchmark_tolerance: float = 2e-3
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    comparison = benchmark_comparison_table(summary, references)
    for row in comparison.itertuples(index=False):
        checks.append(
            {
                "scenario": row.scenario,
                "n_paths": int(row.n_paths),
                "method": row.method,
                "check": "fixed_policy_reference_comparison",
                "value": {
                    "gap": float(row.gap),
                    "relative_gap_percent": float(row.relative_gap_percent),
                    "replicate_se": float(row.replicate_se),
                    "replicate_ci_lower": float(row.replicate_ci_lower),
                    "replicate_ci_upper": float(row.replicate_ci_upper),
                    "reference_price": float(row.reference_price),
                    "tree_refinement_difference": float(
                        row.tree_refinement_difference
                    ),
                    "possible_lower_bound_violation": bool(
                        row.possible_lower_bound_violation
                    ),
                },
                "passed": bool(not row.possible_lower_bound_violation),
                "tolerance": (
                    "positive gap must not exceed its across-replication 95% CI "
                    "half-width plus CRR refinement difference; gap magnitude "
                    "is an empirical policy-approximation finding"
                ),
            }
        )
    european = references[references["benchmark"] == "European Black-Scholes put"]
    crr = references[references["benchmark"] == "same-grid monthly Bermudan CRR"]
    american = references[
        references["benchmark"]
        == "continuous-exercise American CRR sanity reference"
    ]
    for scenario in crr["scenario"].drop_duplicates():
        e = float(european.loc[european["scenario"] == scenario, "price"].iloc[0])
        b = crr.loc[crr["scenario"] == scenario, "price"].to_numpy(dtype=float)
        a = american.loc[american["scenario"] == scenario, "price"].to_numpy(dtype=float)
        checks.append(
            {
                "scenario": scenario,
                "check": "benchmark_ordering",
                "value": {
                    "european": e,
                    "bermudan_refined": b.tolist(),
                    "continuous_american": a.tolist(),
                },
                "passed": bool(
                    e <= float(np.min(b)) + benchmark_tolerance
                    and float(np.max(b)) <= float(np.min(a)) + benchmark_tolerance
                ),
                "tolerance": (
                    "European <= matched Bermudan CRR <= continuous-American "
                    f"allowing {benchmark_tolerance:g} numerical tolerance"
                ),
            }
        )
        tree_difference = float(np.max(np.abs(b - b[-1])))
        checks.append(
            {
                "scenario": scenario,
                "check": "bermudan_tree_refinement",
                "value": tree_difference,
                "passed": bool(tree_difference <= 0.02),
                "tolerance": "maximum CRR refinement difference <= 0.02",
            }
        )
    return checks


def revalidate_saved_results(result_dir: Path) -> dict[str, Any]:
    result_dir = Path(result_dir)
    replications = pd.read_csv(result_dir / "per_replication.csv")
    summary = summarize_replications(replications)
    references = pd.read_csv(result_dir / "reference_prices.csv")
    checks = benchmark_validation_checks(summary, references)
    checks.extend(martingale_validation_checks(replications))
    finite_result = bool(
        np.all(np.isfinite(replications[["price", "standard_error", "path_payoff_sd"]].to_numpy()))
    )
    checks.append(
        {
            "scenario": "all",
            "check": "finite_pricing_outputs",
            "value": finite_result,
            "passed": finite_result,
            "tolerance": "all prices, standard errors, and path payoff SDs finite",
        }
    )
    comparison = benchmark_comparison_table(summary, references)
    comparison.to_csv(
        result_dir / "tables" / "benchmark_comparison.csv", index=False
    )
    original_validation = result_dir / "validation.json"
    archived_validation = result_dir / "validation_original.json"
    if original_validation.exists() and not archived_validation.exists():
        archived_validation.write_text(
            original_validation.read_text(encoding="utf-8"), encoding="utf-8"
        )
    config_path = result_dir / "config_resolved.yaml"
    run_id = yaml.safe_load(config_path.read_text(encoding="utf-8"))["run_id"]
    validation = {
        "run_id": run_id,
        "validation_scope": "Corrected saved-data numerical validation; original pricing rows are unchanged.",
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }
    serialized = json.dumps(validation, indent=2)
    (result_dir / "validation.json").write_text(serialized, encoding="utf-8")
    (result_dir / "validation_corrected.json").write_text(serialized, encoding="utf-8")
    return validation


def _base_row(
    scenario: dict[str, Any],
    contract: BermudanPut | ArithmeticAsianPut,
    method: str,
    n_paths: int,
    replicate: int,
    seed: int,
) -> dict[str, Any]:
    return {
        "scenario": scenario["id"],
        "contract": contract.kind,
        "spot": contract.spot0,
        "strike": contract.strike,
        "rate": contract.rate,
        "dividend": contract.dividend,
        "volatility": contract.volatility,
        "maturity": contract.maturity,
        "steps": contract.steps,
        "exercise_dates": list(range(contract.steps + 1)) if contract.allow_initial_exercise else list(range(1, contract.steps + 1)),
        "method": method,
        "n_paths": n_paths,
        "replicate": replicate,
        "pricing_seed": seed,
    }


def run_experiment(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(exist_ok=True)
    (output_dir / "tables").mkdir(exist_ok=True)
    (output_dir / "config_resolved.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    environment = {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "process_time_resolution_seconds": time.get_clock_info("process_time").resolution,
        "wall_time_resolution_seconds": time.get_clock_info("perf_counter").resolution,
        "cpu_timing_reliability_floor_seconds": CPU_TIMING_FLOOR_SECONDS,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "matplotlib": matplotlib.__version__,
        "pyyaml": yaml.__version__,
        "run_id": config["run_id"],
        "legacy_repository_sha_audited": "aa4d025d05db285c74c8ef03f6e587884a8f5f6f",
    }
    (output_dir / "environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )

    seed_rows: list[dict[str, Any]] = []
    rep_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    policy_model_rows: list[dict[str, Any]] = []
    martingale_rows: list[dict[str, Any]] = []
    exercise_rows: list[dict[str, Any]] = []
    reference_rows: list[dict[str, Any]] = []
    representative: dict[str, np.ndarray] = {}
    validation_checks: list[dict[str, Any]] = []
    scenarios = [("vanilla", item) for item in config["vanilla"]]
    scenarios.extend(("asian_arithmetic", item) for item in config["asian"])

    for scenario_index, (contract_type, scenario) in enumerate(scenarios):
        contract, policy_fit, models, diagnostics, timings = _fit_scenario(
            config, scenario, contract_type, scenario_index, seed_rows
        )
        policy_model_rows.extend(
            {
                "scenario": scenario["id"],
                "time_index": row.time_index,
                "n_regression_paths": row.n_regression_paths,
                "rank": row.rank,
                "n_features": row.n_features,
                "condition_number": row.condition_number,
                "coefficients": row.coefficients.tolist(),
                "policy_training_price": policy_fit.training_price,
            }
            for row in policy_fit.diagnostics
        )
        model_rows.extend([{**row, "scenario": scenario["id"]} for row in diagnostics])
        if isinstance(contract, BermudanPut):
            references = _vanilla_references(contract, [int(x) for x in config["tree_steps"]])
            for row in references:
                row["scenario"] = scenario["id"]
            reference_rows.extend(references)
        for model_row in diagnostics:
            if not np.isfinite(model_row["training_mse"]) or not np.isfinite(model_row["validation_mse"]):
                validation_checks.append(
                    {
                        "scenario": scenario["id"],
                        "check": f"finite_value_fit_{model_row['model']}_{model_row['time_index']}",
                        "value": [model_row["training_mse"], model_row["validation_mse"]],
                        "passed": False,
                        "tolerance": "finite fit diagnostics",
                    }
                )

        for size_index, n_paths_raw in enumerate(config["pricing_sizes"]):
            n_paths = int(n_paths_raw)
            for replicate in range(int(config["pricing_replications"])):
                seed = _seed(
                    int(config["base_seed"]), scenario_index, "pricing", replicate, size_index
                )
                seed_rows.append(
                    {
                        "scenario": scenario["id"],
                        "role": "pricing",
                        "replicate": replicate,
                        "n_paths": n_paths,
                        "seed": seed,
                    }
                )
                pricing_start = _timer()
                pricing_states = _simulate_states(contract, n_paths, seed)
                evaluation = policy_fit.policy.evaluate(pricing_states)
                common_cpu, common_wall = _elapsed(pricing_start)

                plain_values = evaluation.discounted_payoffs
                plain_sd = float(np.std(plain_values, ddof=1))
                exercise_frequency = float(np.mean(evaluation.stopping_indices < contract.steps))
                mean_exercise_time = float(
                    np.mean(evaluation.stopping_indices) * contract.maturity / contract.steps
                )
                outputs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]] = {
                    "plain": (plain_values, np.zeros_like(plain_values), np.zeros_like(plain_values), None, None)
                }
                model_cost: dict[str, tuple[float, float]] = {}
                for model_kind, method in (("linear", "linear_cv"), ("spline", "spline_cv")):
                    cv_start = _timer()
                    increments, martingale_path, stopped = martingale_correction(
                        pricing_states, evaluation, models[model_kind], contract
                    )
                    adjusted = apply_control_variate(evaluation, stopped)
                    cv_cpu, cv_wall = _elapsed(cv_start)
                    outputs[method] = (adjusted, stopped, increments, martingale_path, None)
                    model_cost[method] = (cv_cpu, cv_wall)
                    for date in range(1, contract.steps + 1):
                        martingale_rows.append(
                            {
                                "scenario": scenario["id"],
                                "contract": contract.kind,
                                "n_paths": n_paths,
                                "replicate": replicate,
                                "method": method,
                                "time_index": date,
                                "mean_increment": float(np.mean(increments[:, date - 1])),
                                "sd_increment": float(np.std(increments[:, date - 1], ddof=1)),
                                "mean_martingale_terminal": float(np.mean(martingale_path[:, -1])),
                                "mean_martingale_stopped": float(np.mean(stopped)),
                                "sd_martingale_stopped": float(np.std(stopped, ddof=1)),
                                "corr_y_martingale_stopped": float(
                                    np.corrcoef(plain_values, stopped)[0, 1]
                                    if plain_sd > 0 and np.std(stopped, ddof=1) > 0 else np.nan
                                ),
                            }
                        )

                for method in METHODS:
                    values, correction, increments, _, _ = outputs[method]
                    sd = float(np.std(values, ddof=1))
                    variance = float(np.var(values, ddof=1))
                    vrf = 1.0 if method == "plain" else (
                        float(np.var(plain_values, ddof=1) / variance) if variance > 0.0 else float("inf")
                    )
                    se_reduction = 1.0 if method == "plain" else (
                        plain_sd / sd if sd > 0.0 else float("inf")
                    )
                    allocated_policy = timings["policy_fit_cpu_seconds"] / (
                        int(config["pricing_replications"]) * len(config["pricing_sizes"])
                    )
                    allocated_cv = (
                        timings["value_fit_cpu_seconds"] / (
                            int(config["pricing_replications"]) * len(config["pricing_sizes"])
                        )
                        if method != "plain" else 0.0
                    )
                    marginal_cpu = common_cpu + model_cost.get(method, (0.0, 0.0))[0]
                    marginal_wall = common_wall + model_cost.get(method, (0.0, 0.0))[1]
                    total_cpu = allocated_policy + allocated_cv + marginal_cpu
                    total_wall = (
                        timings["policy_fit_wall_seconds"] + timings["value_fit_wall_seconds"] * (method != "plain")
                    ) / (int(config["pricing_replications"]) * len(config["pricing_sizes"])) + marginal_wall
                    plain_total_cpu = allocated_policy + common_cpu
                    cpu_timing_reliable = min(plain_total_cpu, total_cpu) >= CPU_TIMING_FLOOR_SECONDS
                    cpu_efficiency = (
                        1.0 if method == "plain" else
                        float(np.var(plain_values, ddof=1) * plain_total_cpu
                              / (variance * total_cpu))
                        if variance > 0.0 and total_cpu > 0.0 else float("nan")
                    ) if cpu_timing_reliable else float("nan")
                    row = _base_row(scenario, contract, method, n_paths, replicate, seed)
                    row.update(
                        {
                            "price": float(np.mean(values)),
                            "path_payoff_sd": sd,
                            "standard_error": sd / np.sqrt(n_paths),
                            "ci_lower": float(np.mean(values) - 1.96 * sd / np.sqrt(n_paths)),
                            "ci_upper": float(np.mean(values) + 1.96 * sd / np.sqrt(n_paths)),
                            "mean_martingale": float(np.mean(correction)),
                            "martingale_sd": float(np.std(correction, ddof=1)),
                            "mean_increment": (
                                float(np.mean(increments)) if method != "plain" else 0.0
                            ),
                            "increment_sd": (
                                float(np.std(increments, ddof=1)) if method != "plain" else 0.0
                            ),
                            "y_martingale_correlation": (
                                float(np.corrcoef(plain_values, correction)[0, 1])
                                if method != "plain" and np.std(correction, ddof=1) > 0 else np.nan
                            ),
                            "exercise_frequency": exercise_frequency,
                            "mean_exercise_time": mean_exercise_time,
                            "variance_reduction_factor": vrf,
                            "se_reduction": se_reduction,
                            "cpu_adjusted_efficiency": cpu_efficiency,
                            "cpu_timing_reliable": cpu_timing_reliable,
                            "variance_reduction_defined": bool(
                                method == "plain"
                                or variance > np.finfo(float).tiny
                                and np.var(plain_values, ddof=1) > np.finfo(float).tiny
                            ),
                            "policy_fit_cpu_seconds": timings["policy_fit_cpu_seconds"],
                            "value_fit_cpu_seconds": timings["value_fit_cpu_seconds"],
                            "marginal_cpu_seconds": marginal_cpu,
                            "marginal_wall_seconds": marginal_wall,
                            "allocated_policy_fit_cpu_seconds": allocated_policy,
                            "allocated_value_fit_cpu_seconds": allocated_cv,
                            "total_cpu_seconds": total_cpu,
                            "total_wall_seconds": total_wall,
                            "policy_training_price": policy_fit.training_price,
                        }
                    )
                    rep_rows.append(row)

                for time_index in range(contract.steps + 1):
                    count = int(np.sum(evaluation.stopping_indices == time_index))
                    exercise_rows.append(
                        {
                            "scenario": scenario["id"],
                            "contract": contract.kind,
                            "n_paths": n_paths,
                            "replicate": replicate,
                            "time_index": time_index,
                            "time": time_index * contract.maturity / contract.steps,
                            "count": count,
                            "frequency": count / n_paths,
                        }
                    )
                if replicate == 0 and size_index == 0:
                    limit = min(512, n_paths)
                    prefix = "vanilla" if isinstance(contract, BermudanPut) else "asian"
                    sid = scenario["id"]
                    representative[f"{prefix}_Y_{sid}"] = plain_values[:limit]
                    representative[f"{prefix}_tau_{sid}"] = evaluation.stopping_indices[:limit]
                    representative[f"{prefix}_paths_spot_{sid}"] = pricing_states["spot"][:limit]
                    if "average" in pricing_states:
                        representative[f"{prefix}_paths_average_{sid}"] = pricing_states["average"][:limit]
                    for model_kind, method in (("linear", "linear_cv"), ("spline", "spline_cv")):
                        adjusted, stopped, increments, _, _ = outputs[method]
                        representative[f"{prefix}_M_{model_kind}_{sid}"] = stopped[:limit]
                        representative[f"{prefix}_Ycv_{model_kind}_{sid}"] = adjusted[:limit]
                        representative[f"{prefix}_increments_{model_kind}_{sid}"] = increments[:limit]

    replications = pd.DataFrame(rep_rows)
    summary = summarize_replications(replications)
    replications.to_csv(output_dir / "per_replication.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    pd.DataFrame(seed_rows).to_csv(output_dir / "seeds.csv", index=False)
    pd.DataFrame(model_rows).to_csv(output_dir / "model_diagnostics.csv", index=False)
    pd.DataFrame(policy_model_rows).to_csv(output_dir / "policy_model_diagnostics.csv", index=False)
    pd.DataFrame(martingale_rows).to_csv(output_dir / "martingale_diagnostics.csv", index=False)
    pd.DataFrame(exercise_rows).to_csv(output_dir / "exercise_diagnostics.csv", index=False)
    pd.DataFrame(reference_rows).to_csv(output_dir / "reference_prices.csv", index=False)
    if representative:
        np.savez_compressed(output_dir / "representative_paths.npz", **representative)

    reference_frame = pd.DataFrame(reference_rows)
    validation_checks.extend(benchmark_validation_checks(summary, reference_frame))
    benchmark_comparison_table(summary, reference_frame).to_csv(
        output_dir / "tables" / "benchmark_comparison.csv", index=False
    )
    validation_checks.extend(martingale_validation_checks(replications))
    finite_result = bool(
        np.all(np.isfinite(replications[["price", "standard_error", "path_payoff_sd"]].to_numpy()))
    )
    validation_checks.append(
        {
            "scenario": "all",
            "check": "finite_pricing_outputs",
            "value": finite_result,
            "passed": finite_result,
            "tolerance": "all prices, standard errors, and path payoff SDs finite",
        }
    )
    validation = {
        "run_id": config["run_id"],
        "validation_scope": "Numerical smoke/run diagnostics; pytest results are recorded separately by the invoking command.",
        "checks": validation_checks,
        "passed": all(check["passed"] for check in validation_checks),
    }
    (output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    if bool(config.get("generate_figures", True)):
        make_figures(output_dir)
    _write_run_interpretation(output_dir, summary, reference_rows, validation)
    print(summary.round(6).to_string(index=False))
    print(f"Validation: {'PASS' if validation['passed'] else 'FAIL'} ({output_dir / 'validation.json'})")
    return validation


def _write_run_interpretation(
    output_dir: Path,
    summary: pd.DataFrame,
    references: list[dict[str, Any]],
    validation: dict[str, Any],
) -> None:
    lines = [
        f"# Run interpretation: {output_dir.name}",
        "",
        f"Numerical validation status: **{'PASS' if validation['passed'] else 'FAIL'}**.",
        "This is a fixed-policy-value study; it does not identify an exact American/Asian optimum.",
        "",
        "## Per-scenario findings",
        "",
    ]
    for scenario in summary["scenario"].drop_duplicates():
        case = summary[summary["scenario"] == scenario]
        lines.append(f"### {scenario}")
        lines.append("")
        for n_paths in case["n_paths"].unique():
            sized = case[case["n_paths"] == n_paths].set_index("method")
            plain = sized.loc["plain"]
            lines.append(
                f"- At N={n_paths}, plain mean={plain['mean_price']:.6g} "
                f"(replication t interval {plain['replicate_ci_lower']:.6g} to "
                f"{plain['replicate_ci_upper']:.6g})."
            )
            for method in ("linear_cv", "spline_cv"):
                row = sized.loc[method]
                lines.append(
                    f"  {method}: mean={row['mean_price']:.6g}, median VRF="
                    f"{row['median_vrf']:.4g}, mean stopped-martingale estimate="
                    f"{row['mean_martingale']:.4g}, mean total CPU="
                    f"{row['mean_total_cpu_seconds']:.4g}s/replication."
                )
        reference = [
            row for row in references
            if row["scenario"] == scenario and row["benchmark"] == "same-grid monthly Bermudan CRR"
        ]
        if reference:
            lines.append(
                f"- Same-date Bermudan CRR references: "
                + ", ".join(f"{row['tree_steps']} steps={row['price']:.8g}" for row in reference)
                + "."
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation limits",
            "",
            "- Confidence intervals across replications quantify conditional pricing-sample variability for the one frozen training fit; they do not include policy/value-fit instability.",
            "- The spline is a restricted additive linear-spline approximation, not EH's full adaptive MARS/LDA-MARS procedure.",
            "- A VRF below one is retained and means this fitted control increased path-payoff variance.",
            "- No exact arithmetic-Asian Bermudan benchmark or EH-style dual upper bound is produced.",
        ]
    )
    (output_dir / "interpretations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run STAT 906 LSMC/martingale-CV experiments.")
    parser.add_argument("--config", type=Path, required=True, help="YAML run configuration")
    parser.add_argument("--output", type=Path, required=True, help="Result directory")
    args = parser.parse_args(argv)
    validation = run_experiment(args.config, args.output)
    return 0 if validation["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
