#!/usr/bin/env python3
"""Re-solve capacity and rounded freight scenarios; never infer basis from flows."""
import importlib.util
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog

spec = importlib.util.spec_from_file_location("grain_solver", Path(__file__).with_name("03_solve_optimization.py"))
solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solver)


def load_base_data():
    lp = solver.build_lp_matrices()
    return lp["df_depots"], lp["df_demands"], lp["df_cost"], lp["df_dist"]


def solve(c, A, b):
    result = linprog(c, A_ub=A, b_ub=b, method="highs-ds")
    if not result.success:
        raise RuntimeError(f"Sensitivity solve failed: {result.message}")
    return result


def matrices():
    lp = solver.build_lp_matrices()
    base, A, b = solver.solve_scipy_highs_verification(lp)
    return lp, base, A, b


def run_experiment_1_capacity_expansion(df_depots, df_demands, df_cost, df_dist):
    lp, base, A, b = matrices()
    records = []
    for cap in range(21000, 36000, 1000):
        bb = b.copy()
        bb[9] = cap
        res = solve(lp["c_cost"], A, bb)
        flows = res.x.reshape(4, 6, 2).sum(axis=2)
        # The objective is nondifferentiable at 32k and 34k: record both sides.
        left_b, right_b = bb.copy(), bb.copy()
        left_b[9] -= 1
        right_b[9] += 1
        left = solve(lp["c_cost"], A, left_b)
        right = solve(lp["c_cost"], A, right_b)
        records.append(dict(
            experiment="Exp1_Capacity_Expansion", vadodara_dispatch_cap_mt=cap,
            total_system_cost_inr=round(res.fun, 2), total_cost_inr_crores=round(res.fun / 1e7, 4),
            shadow_price_inr_per_mt=round(abs(res.ineqlin.marginals[9]), 2),
            marginal_saving_left_inr_per_mt=round(left.fun - res.fun, 2),
            marginal_saving_right_inr_per_mt=round(res.fun - right.fun, 2),
            dispatch_slack_mt=round(res.ineqlin.residual[9], 2),
            flow_chhani_to_surat_mt=round(flows[1, 1], 1),
            flow_sabarmati_to_surat_mt=round(flows[0, 1], 1),
            flow_gandhidham_to_surat_mt=round(flows[3, 1], 1),
            flow_sabarmati_to_banaskantha_mt=round(flows[0, 4], 1),
            cost_savings_vs_base_inr=round(base.fun - res.fun, 2)))
    return pd.DataFrame(records)


def run_experiment_2_freight_shock(df_depots, df_demands, df_dist):
    lp, base, A, b = matrices()
    baseline_flows = base.x.reshape(4, 6, 2).sum(axis=2)
    demand = float(df_demands[["wheat_demand_mt", "rice_demand_mt"]].to_numpy().sum())
    work = float((baseline_flows * df_dist.to_numpy()).sum())
    records = []
    for beta in (1.5, 2., 2.5, 3., 3.5, 4.):
        # Match dataset's numpy rounding, including half-cent values.
        costs = np.repeat(np.round(100 + beta * df_dist.to_numpy(), 2).ravel(), 2)
        res = solve(costs, A, b)
        aggregate = res.x.reshape(4, 6, 2).sum(axis=2)
        invariant = np.allclose(aggregate, baseline_flows, atol=1e-6, rtol=0)
        affine = 100 * demand + beta * work
        records.append(dict(experiment="Exp2_Freight_Rate_Shock", freight_rate_beta_inr_per_mt_km=beta,
            total_system_cost_inr=round(res.fun, 2), total_cost_inr_crores=round(res.fun / 1e7, 4),
            cost_change_pct_vs_base=round(100 * (res.fun / base.fun - 1), 2),
            unrounded_affine_cost_inr=round(affine, 2),
            rounding_residual_inr=round(res.fun - affine, 2),
            routing_basis_status="INVARIANT aggregate flows; basis not inspected" if invariant else "SHIFTED aggregate flows"))
    return pd.DataFrame(records)


def main():
    data = load_base_data()
    capacity = run_experiment_1_capacity_expansion(*data)
    freight = run_experiment_2_freight_shock(data[0], data[1], data[3])
    pd.concat([capacity, freight], ignore_index=True).to_csv("outputs/tables/sensitivity_results.csv", index=False)
    savings = float(capacity.loc[capacity.vadodara_dispatch_cap_mt == 34000, "cost_savings_vs_base_inr"].iloc[0])
    text = "# Sensitivity analysis: illustrative Gujarat distribution scenario\n\n"
    text += capacity.to_markdown(index=False) + "\n\n"
    text += ("The value function has marginal savings of INR 1,022.90/MT for 21,000 < C2 < 32,000 MT, "
             "INR 706.55/MT for 32,000 < C2 < 34,000 MT, and zero above 34,000 MT. "
             "At 32,000 MT Gandhidham-to-Surat reaches zero. The second regime is the exchange "
             "Chhani-to-Surat + Sabarmati-to-Banaskantha replacing Sabarmati-to-Surat + Gandhidham-to-Banaskantha: "
             "743.55 - 487.20 + 900.70 - 450.50 = 706.55 INR/MT. "
             "At 34,000 MT capacity is still binding; left/right marginal savings are 706.55/0, "
             "and stock prevents further gain. Only above this point is dispatch capacity slack. "
             "The solver-selected dual at either kink is one valid subgradient, not a unique two-sided derivative.\n\n")
    text += f"Baseline-to-34,000 savings: INR {savings:,.2f}/month; INR {12*savings:,.2f}/year, assuming the same scenario repeats. No construction cost or payback has been evaluated.\n\n"
    text += freight.to_markdown(index=False) + "\n\n"
    text += ("Aggregate corridor flows were unchanged at the six tested rates; solver bases were not inspected. "
             "For unrounded route costs, Z(beta)=13,200,000 + 17,513,100 beta INR "
             "(1.32 + 1.75131 beta crore). Rounded costs depart from that affine identity by the recorded residuals, "
             "including -30 INR at beta=2.50. A freight-rate shock is a scenario, not a direct diesel-price pass-through model.\n")
    Path("outputs/tables/sensitivity_summary.md").write_text(text)
    print(capacity.to_string(index=False))
    print(freight.to_string(index=False))


if __name__ == "__main__":
    main()
