#!/usr/bin/env python3
"""
scripts/03_solve_optimization.py

Solves the 4-Depot, 6-District, 2-Commodity Food Grain Distribution Linear Program in Gujarat.
Part A: Custom Two-Phase Simplex Implementation
  - Explicit 24 x 84 tableau (48 primal, 12 slacks, 12 surplus, 12 artificial variables).
  - Phase I: Drives artificial infeasibility W -> 0 via Bland's anti-cycling rule.
  - Phase II: Drops artificial columns, restores cost vector c, and minimizes Z.
Part B: Independent Cross-Verification with SciPy HiGHS (method='highs-ds')
  - Verifies objective Z* to machine precision.
  - Extracts optimal shipment flow matrix x*_{ijk}, depot utilization, slacks, and dual shadow prices.
  - Identifies alternative optima and reports a selected HiGHS commodity allocation.

Outputs:
  outputs/tables/optimal_shipments_wheat_rice.csv
  outputs/tables/shadow_prices_and_slacks.csv
  outputs/tables/solver_diagnostics.json
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from scipy.optimize import linprog

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
os.makedirs("outputs/tables", exist_ok=True)

def build_lp_matrices():
    """Loads processed data and builds the 48-variable LP matrices."""
    df_depots = pd.read_csv("data/processed/fci_depots_supply.csv")
    df_demands = pd.read_csv("data/processed/district_warehouses_demand.csv")
    df_cost = pd.read_csv("data/processed/cost_matrix_inr_per_mt.csv", index_col="depot_id")
    df_dist = pd.read_csv("data/processed/distance_matrix_km.csv", index_col="depot_id")

    if len(df_depots) != 4 or len(df_demands) != 6:
        raise ValueError("This model requires exactly four depots and six districts")
    for frame in (df_cost, df_dist):
        if list(frame.index) != list(df_depots.depot_id) or list(frame.columns) != list(df_demands.warehouse_id):
            raise ValueError("Matrix labels do not align with node ordering")
    for frame in (df_cost, df_dist):
        if frame.shape != (4, 6) or not np.isfinite(frame.to_numpy()).all() or (frame.to_numpy() < 0).any():
            raise ValueError("Matrices must be complete finite nonnegative 4 x 6 arrays")
    for frame, cols in ((df_depots, ["wheat_supply_mt", "rice_supply_mt", "max_dispatch_cap_mt"]),
                        (df_demands, ["wheat_demand_mt", "rice_demand_mt"])):
        values = frame[cols].to_numpy()
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Supply, capacity and demand must be finite and nonnegative")
    num_depots = len(df_depots)       # 4
    num_warehouses = len(df_demands)  # 6
    num_vars = num_depots * num_warehouses * 2 # 48 primal variables

    # Variable mapping: index p = i * 12 + j * 2 + k
    # k=0: Wheat, k=1: Rice
    c_cost = np.zeros(num_vars)
    var_names = []
    for i in range(num_depots):
        d_id = df_depots.loc[i, "depot_id"]
        for j in range(num_warehouses):
            w_id = df_demands.loc[j, "warehouse_id"]
            for k, comm in enumerate(["W", "R"]):
                p = i * 12 + j * 2 + k
                c_cost[p] = df_cost.iloc[i, j]
                var_names.append(f"x_{d_id}_{w_id}_{comm}")

    num_constraints = 24
    num_slacks = 12       # 8 commodity supply (<=) + 4 dispatch capacity (<=)
    num_surplus = 12      # 12 demand (>=)
    num_artificial = 12   # 12 artificial for demand (>=)
    total_cols = num_vars + num_slacks + num_surplus + num_artificial # 84 cols

    A = np.zeros((num_constraints, total_cols))
    b = np.zeros(num_constraints)
    constraint_names = []

    # 1. Commodity Stock Limit: Rows 0..3 (Wheat), Rows 4..7 (Rice)
    for i in range(num_depots):
        d_id = df_depots.loc[i, "depot_id"]
        for j in range(num_warehouses):
            A[i, i * 12 + j * 2 + 0] = 1.0
        A[i, num_vars + i] = 1.0  # slack s_0..s_3
        b[i] = df_depots.loc[i, "wheat_supply_mt"]
        constraint_names.append(f"Supply_Wheat_{d_id}")

    for i in range(num_depots):
        d_id = df_depots.loc[i, "depot_id"]
        for j in range(num_warehouses):
            A[4 + i, i * 12 + j * 2 + 1] = 1.0
        A[4 + i, num_vars + 4 + i] = 1.0  # slack s_4..s_7
        b[4 + i] = df_depots.loc[i, "rice_supply_mt"]
        constraint_names.append(f"Supply_Rice_{d_id}")

    # 2. Depot Dispatch Capacity: Rows 8..11 (<=)
    for i in range(num_depots):
        d_id = df_depots.loc[i, "depot_id"]
        for j in range(num_warehouses):
            for k in range(2):
                A[8 + i, i * 12 + j * 2 + k] = 1.0
        A[8 + i, num_vars + 8 + i] = 1.0  # slack s_8..s_11
        b[8 + i] = df_depots.loc[i, "max_dispatch_cap_mt"]
        constraint_names.append(f"Dispatch_Cap_{d_id}")

    # 3. District Demand: Rows 12..17 (Wheat, >=), Rows 18..23 (Rice, >=)
    # Form: sum x_ijk - e_m + a_m = D_jk
    for j in range(num_warehouses):
        w_id = df_demands.loc[j, "warehouse_id"]
        for i in range(num_depots):
            A[12 + j, i * 12 + j * 2 + 0] = 1.0
        A[12 + j, num_vars + num_slacks + j] = -1.0                    # surplus e_0..e_5
        A[12 + j, num_vars + num_slacks + num_surplus + j] = 1.0      # artificial a_0..a_5
        b[12 + j] = df_demands.loc[j, "wheat_demand_mt"]
        constraint_names.append(f"Demand_Wheat_{w_id}")

    for j in range(num_warehouses):
        w_id = df_demands.loc[j, "warehouse_id"]
        for i in range(num_depots):
            A[18 + j, i * 12 + j * 2 + 1] = 1.0
        A[18 + j, num_vars + num_slacks + 6 + j] = -1.0                # surplus e_6..e_11
        A[18 + j, num_vars + num_slacks + num_surplus + 6 + j] = 1.0  # artificial a_6..a_11
        b[18 + j] = df_demands.loc[j, "rice_demand_mt"]
        constraint_names.append(f"Demand_Rice_{w_id}")

    return {
        "df_depots": df_depots,
        "df_demands": df_demands,
        "df_cost": df_cost,
        "df_dist": df_dist,
        "c_cost": c_cost,
        "A": A,
        "b": b,
        "var_names": var_names,
        "constraint_names": constraint_names,
        "num_vars": num_vars,
        "num_slacks": num_slacks,
        "num_surplus": num_surplus,
        "num_artificial": num_artificial,
        "total_cols": total_cols,
        "num_constraints": num_constraints
    }


def solve_custom_two_phase_simplex(lp):
    """
    Solves the LP using a custom, transparent Two-Phase Simplex implementation.
    Tableau Dimensions:
      Phase I: 25 rows x 85 columns (24 constraints + 1 objective, 84 vars + 1 RHS).
      Phase II: 25 rows x 73 columns (artificial columns purged).
    Enforces Bland's Anti-Cycling Rule for entering and leaving variable selection.
    """
    logging.info("Starting Custom Two-Phase Simplex Solver...")
    A = lp["A"]
    b = lp["b"]
    c_cost = lp["c_cost"]
    M = lp["num_constraints"]       # 24
    N1 = lp["total_cols"]           # 84
    num_vars = lp["num_vars"]       # 48
    tol = 1e-9
    max_pivots = 10000

    # Initial basis: 12 slacks (indices 48..59) + 12 artificials (indices 72..83)
    basis = list(range(48, 60)) + list(range(72, 84))

    # Construct Phase I Tableau (M+1 rows x N1+1 cols)
    T1 = np.zeros((M + 1, N1 + 1), dtype=np.float64)
    T1[1:, :N1] = A
    T1[1:, -1] = b

    # Objective: min W = sum(artificial) => max -W = -sum(a_m)
    # Artificial variables are basic in rows 13..24 (1-indexed).
    # Canonicalize row 0: subtract artificial constraint rows from row 0
    T1[0, 72:84] = 1.0
    for r in range(12, 24):
        T1[0, :] -= T1[r + 1, :]

    pivots_phase1 = 0
    while True:
        # Bland's Rule for entering variable: smallest column index with reduced cost < -tol
        entering = -1
        for j in range(N1):
            if T1[0, j] < -tol:
                entering = j
                break
        
        if entering == -1:
            # Optimal for Phase I
            break

        # Minimum Ratio Test for leaving variable (Bland's tie-break: smallest basic variable index)
        min_ratio = np.inf
        leaving_row = -1
        for r in range(1, M + 1):
            if T1[r, entering] > tol:
                ratio = T1[r, -1] / T1[r, entering]
                if (ratio < min_ratio - 1e-12 or
                        (abs(ratio - min_ratio) <= 1e-12 and
                         (leaving_row == -1 or basis[r - 1] < basis[leaving_row - 1]))):
                    min_ratio = ratio
                    leaving_row = r

        if leaving_row == -1:
            raise RuntimeError("Phase I encountered an unbounded auxiliary problem.")

        # Gauss-Jordan pivot on (leaving_row, entering)
        pivot_element = T1[leaving_row, entering]
        T1[leaving_row, :] /= pivot_element
        for r in range(M + 1):
            if r != leaving_row:
                T1[r, :] -= T1[r, entering] * T1[leaving_row, :]

        basis[leaving_row - 1] = entering
        pivots_phase1 += 1
        if pivots_phase1 > max_pivots:
            raise RuntimeError("Phase I pivot limit exceeded")

    W_val = -T1[0, -1]
    logging.info("Phase I completed in %d pivots. Optimal W* = %.6f", pivots_phase1, W_val)
    if abs(W_val) > 1e-4:
        raise ValueError(f"Infeasible problem instance: Phase I terminated with W* = {W_val} > 0.")

    # Artificial variables must leave the basis before their columns disappear.
    # This fixed model has independent stock/cap rows and demand surplus columns,
    # so a zero artificial basic row always has an eligible retained column.
    cleanup_pivots = 0
    for r in range(1, M + 1):
        if basis[r - 1] >= 72:
            if abs(T1[r, -1]) > 1e-7:
                raise ValueError("Nonzero artificial variable remains after Phase I")
            candidates = [j for j in range(72) if j not in basis and abs(T1[r, j]) > tol]
            if not candidates:
                raise RuntimeError("Redundant artificial row requires explicit removal")
            entering = min(candidates)
            T1[r, :] /= T1[r, entering]
            for other in range(M + 1):
                if other != r:
                    T1[other, :] -= T1[other, entering] * T1[r, :]
            basis[r - 1] = entering
            cleanup_pivots += 1

    # -------------------------------------------------------------
    # Transition to Phase II
    # -------------------------------------------------------------
    # Purge artificial columns (indices 72..83) -> keep columns 0..71 + RHS
    N2 = num_vars + lp["num_slacks"] + lp["num_surplus"] # 72 columns
    T2 = np.zeros((M + 1, N2 + 1), dtype=np.float64)
    T2[1:, :N2] = T1[1:, :N2]
    T2[1:, -1] = T1[1:, -1]

    # Setup Phase II objective: min Z = c^T x
    # Canonical row 0 equation: Z - sum(c_j * x_j) = 0
    # In minimization, reduced cost for column j is c_j - z_j. Variable can enter if c_j - z_j < -tol.
    c_full = np.zeros(N2)
    c_full[:num_vars] = c_cost
    T2[0, :N2] = c_full

    # Canonicalize Row 0 by clearing basic variables currently in the basis:
    for r in range(1, M + 1):
        b_var = basis[r - 1]
        if b_var < N2:
            cost_b = c_full[b_var]
            if abs(cost_b) > tol:
                T2[0, :] -= cost_b * T2[r, :]

    pivots_phase2 = 0
    while True:
        # Bland's Rule: lowest column index with reduced cost < -tol
        entering = -1
        for j in range(N2):
            if T2[0, j] < -tol:
                entering = j
                break

        if entering == -1:
            # Optimal for Phase II
            break

        # Minimum Ratio Test with Bland's tie-breaking
        min_ratio = np.inf
        leaving_row = -1
        for r in range(1, M + 1):
            if T2[r, entering] > tol:
                ratio = T2[r, -1] / T2[r, entering]
                if (ratio < min_ratio - 1e-12 or
                        (abs(ratio - min_ratio) <= 1e-12 and
                         (leaving_row == -1 or basis[r - 1] < basis[leaving_row - 1]))):
                    min_ratio = ratio
                    leaving_row = r

        if leaving_row == -1:
            raise RuntimeError("Phase II encountered an unbounded cost problem.")

        pivot_element = T2[leaving_row, entering]
        T2[leaving_row, :] /= pivot_element
        for r in range(M + 1):
            if r != leaving_row:
                T2[r, :] -= T2[r, entering] * T2[leaving_row, :]

        basis[leaving_row - 1] = entering
        pivots_phase2 += 1
        if pivots_phase2 > max_pivots:
            raise RuntimeError("Phase II pivot limit exceeded")

    # Extract primal solution from final tableau
    x_solution = np.zeros(N2)
    for r in range(1, M + 1):
        x_solution[basis[r - 1]] = T2[r, -1]

    Z_star = float(np.sum(c_cost * x_solution[:num_vars]))
    if not np.isfinite(x_solution).all() or np.min(x_solution) < -1e-7:
        raise RuntimeError("Custom simplex returned invalid primal variables")
    if not np.allclose(A[:, :N2] @ x_solution, b, atol=1e-6, rtol=0):
        raise RuntimeError("Custom simplex failed standard-form feasibility")
    logging.info("Phase II completed in %d pivots. Optimal Z* = INR %.2f", pivots_phase2, Z_star)

    return {
        "pivots_phase1": pivots_phase1,
        "pivots_phase2": pivots_phase2,
        "total_pivots": pivots_phase1 + pivots_phase2 + cleanup_pivots,
        "cleanup_pivots": cleanup_pivots,
        "Z_star": Z_star,
        "x_solution": x_solution[:num_vars],
        "basis": basis
    }


def solve_scipy_highs_verification(lp):
    """Solves the identical LP using SciPy HiGHS (highs-ds) for independent numerical verification."""
    logging.info("Running Independent Cross-Verification via SciPy HiGHS (highs-ds)...")
    df_depots = lp["df_depots"]
    df_demands = lp["df_demands"]
    c_cost = lp["c_cost"]
    num_vars = lp["num_vars"]

    A_ub = []
    b_ub = []

    # 1. Supply limits (<=)
    for i in range(len(df_depots)):
        row_w = np.zeros(num_vars)
        for j in range(len(df_demands)):
            row_w[i * 12 + j * 2 + 0] = 1.0
        A_ub.append(row_w)
        b_ub.append(df_depots.loc[i, "wheat_supply_mt"])

    for i in range(len(df_depots)):
        row_r = np.zeros(num_vars)
        for j in range(len(df_demands)):
            row_r[i * 12 + j * 2 + 1] = 1.0
        A_ub.append(row_r)
        b_ub.append(df_depots.loc[i, "rice_supply_mt"])

    # 2. Dispatch capacity (<=)
    for i in range(len(df_depots)):
        row_c = np.zeros(num_vars)
        for j in range(len(df_demands)):
            for k in range(2):
                row_c[i * 12 + j * 2 + k] = 1.0
        A_ub.append(row_c)
        b_ub.append(df_depots.loc[i, "max_dispatch_cap_mt"])

    # 3. Demand satisfaction (>=) rewritten as -A x <= -D
    for j in range(len(df_demands)):
        row_dw = np.zeros(num_vars)
        for i in range(len(df_depots)):
            row_dw[i * 12 + j * 2 + 0] = -1.0
        A_ub.append(row_dw)
        b_ub.append(-df_demands.loc[j, "wheat_demand_mt"])

    for j in range(len(df_demands)):
        row_dr = np.zeros(num_vars)
        for i in range(len(df_depots)):
            row_dr[i * 12 + j * 2 + 1] = -1.0
        A_ub.append(row_dr)
        b_ub.append(-df_demands.loc[j, "rice_demand_mt"])

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)

    res = linprog(c_cost, A_ub=A_ub, b_ub=b_ub, method="highs-ds")
    if not res.success:
        raise RuntimeError(f"SciPy HiGHS failed: {res.message}")

    logging.info("SciPy HiGHS finished successfully. Optimal Z* = INR %.2f", res.fun)
    return res, A_ub, b_ub


def export_optimization_results(lp, simplex_res, highs_res, A_ub, b_ub):
    """Exports structured shipment tables, shadow prices, and diagnostics."""
    df_depots = lp["df_depots"]
    df_demands = lp["df_demands"]
    df_dist = lp["df_dist"]
    df_cost = lp["df_cost"]
    var_names = lp["var_names"]
    constraint_names = lp["constraint_names"]
    x_opt = highs_res.x

    # 1. Optimal Shipments Table
    shipments = []
    total_tonne_km = 0.0
    for i in range(len(df_depots)):
        d_id = df_depots.loc[i, "depot_id"]
        d_name = df_depots.loc[i, "name"]
        for j in range(len(df_demands)):
            w_id = df_demands.loc[j, "warehouse_id"]
            w_name = df_demands.loc[j, "name"]
            dist = df_dist.loc[d_id, w_id]
            unit_cost = df_cost.loc[d_id, w_id]

            p_w = i * 12 + j * 2 + 0
            p_r = i * 12 + j * 2 + 1
            flow_w = round(x_opt[p_w], 2)
            flow_r = round(x_opt[p_r], 2)
            flow_total = round(flow_w + flow_r, 2)
            cost_total = round(flow_total * unit_cost, 2)
            tonne_km = round(flow_total * dist, 2)
            total_tonne_km += tonne_km

            shipments.append({
                "depot_id": d_id,
                "depot_name": d_name,
                "warehouse_id": w_id,
                "warehouse_name": w_name,
                "distance_km": dist,
                "unit_cost_inr_per_mt": unit_cost,
                "wheat_shipped_mt": flow_w,
                "rice_shipped_mt": flow_r,
                "total_shipped_mt": flow_total,
                "total_cost_inr": cost_total,
                "tonne_km": tonne_km
            })

    df_shipments = pd.DataFrame(shipments)
    df_shipments.to_csv("outputs/tables/optimal_shipments_wheat_rice.csv", index=False)
    logging.info("Saved outputs/tables/optimal_shipments_wheat_rice.csv")

    # 2. Shadow Prices and Slacks Table
    # Complementary slackness: positive shadow price implies zero slack (binding)
    marginals = highs_res.ineqlin.marginals
    slacks = b_ub - A_ub @ x_opt

    dual_records = []
    for idx, name in enumerate(constraint_names):
        sp = round(abs(marginals[idx]), 2)
        slk = round(max(0.0, slacks[idx]), 2)
        is_binding = "BINDING" if slk < 1e-4 else "NON-BINDING"
        dual_records.append({
            "constraint_index": idx + 1,
            "constraint_name": name,
            "shadow_price_inr_per_mt": sp,
            "signed_rhs_marginal_inr_per_mt": float(marginals[idx] if idx < 12 else -marginals[idx]),
            "rhs_sense": "<=" if idx < 12 else ">=",
            "slack_mt": slk,
            "status": is_binding
        })

    df_duals = pd.DataFrame(dual_records)
    df_duals.to_csv("outputs/tables/shadow_prices_and_slacks.csv", index=False)
    logging.info("Saved outputs/tables/shadow_prices_and_slacks.csv")

    # 3. Solver Diagnostics
    total_grain_demand = df_demands["wheat_demand_mt"].sum() + df_demands["rice_demand_mt"].sum()
    avg_cost_per_mt = round(highs_res.fun / total_grain_demand, 2)
    avg_lead_distance_km = round(total_tonne_km / total_grain_demand, 2)

    diagnostics = {
        "status": "OPTIMAL",
        "simplex_pivots_phase1": simplex_res["pivots_phase1"],
        "simplex_pivots_phase2": simplex_res["pivots_phase2"],
        "simplex_total_pivots": simplex_res["total_pivots"],
        "simplex_artificial_cleanup_pivots": simplex_res["cleanup_pivots"],
        "simplex_tolerance": 1e-9,
        "exported_allocation_solver": "SciPy HiGHS highs-ds",
        "maximum_custom_highs_allocation_difference_mt": float(np.max(abs(simplex_res["x_solution"] - highs_res.x))),
        "custom_max_primal_violation_mt": float(max(0, np.max(A_ub @ simplex_res["x_solution"] - b_ub))),
        "highs_max_primal_violation_mt": float(max(0, np.max(A_ub @ highs_res.x - b_ub))),
        "custom_simplex_Z_star_inr": simplex_res["Z_star"],
        "scipy_highs_Z_star_inr": round(highs_res.fun, 2),
        "discrepancy_abs_inr": round(abs(simplex_res["Z_star"] - highs_res.fun), 6),
        "total_demand_satisfied_mt": float(total_grain_demand),
        "total_system_cost_inr": round(highs_res.fun, 2),
        "total_system_cost_inr_crores": round(highs_res.fun / 1e7, 4),
        "average_cost_per_mt_inr": avg_cost_per_mt,
        "total_tonne_km": round(total_tonne_km, 2),
        "average_lead_distance_km": avg_lead_distance_km,
        "alternative_optima_note": (
            "Because unit transportation cost c_ij is identical for wheat and rice on any shared corridor, "
            "feasible wheat/rice exchanges preserving stock and capacity limits can yield identical cost. "
            "Reported allocation is the selected SciPy HiGHS optimum; the custom simplex may select another optimum."
        )
    }

    diag_path = "outputs/tables/solver_diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(diagnostics, f, indent=2)
    logging.info("Saved %s", diag_path)

    # Console Summary
    print("\n" + "="*80)
    print("PHASE 3: OPTIMIZATION SOLVER EXECUTION SUMMARY")
    print("="*80)
    print(f"Custom Two-Phase Simplex: Phase I = {simplex_res['pivots_phase1']} pivots | Phase II = {simplex_res['pivots_phase2']} pivots")
    print(f"Custom Simplex Z*       : INR {simplex_res['Z_star']:,.2f}")
    print(f"SciPy HiGHS Z*          : INR {highs_res.fun:,.2f}")
    print(f"Absolute Discrepancy    : INR {abs(simplex_res['Z_star'] - highs_res.fun):.6f} (Machine Precision Agreement)")
    print(f"Total Grain Distributed : {total_grain_demand:,} MT (100% Demand Met)")
    print(f"Total Logistics Cost    : INR {highs_res.fun/1e7:.4f} Crore (₹{highs_res.fun:,.2f})")
    print(f"Average Logistics Cost  : ₹{avg_cost_per_mt:.2f} per MT")
    print(f"Total Tonne-Kilometers  : {total_tonne_km:,.1f} MT-km (Avg Lead: {avg_lead_distance_km:.1f} km)")
    print("\n[Active Non-Zero Corridors (Total Tonnage)]")
    df_active = df_shipments[df_shipments["total_shipped_mt"] > 0]
    print(df_active[["depot_id", "warehouse_id", "distance_km", "wheat_shipped_mt", "rice_shipped_mt", "total_shipped_mt", "total_cost_inr"]].to_string(index=False))
    print("\n[Active Binding Constraints (Shadow Prices)]")
    df_binding = df_duals[df_duals["status"] == "BINDING"]
    print(df_binding[["constraint_name", "shadow_price_inr_per_mt", "status"]].to_string(index=False))
    print("="*80 + "\n")


def main():
    lp = build_lp_matrices()
    simplex_res = solve_custom_two_phase_simplex(lp)
    highs_res, A_ub, b_ub = solve_scipy_highs_verification(lp)
    if abs(simplex_res["Z_star"] - highs_res.fun) > 1e-4:
        raise RuntimeError("Custom simplex and HiGHS objective mismatch")
    for result in (simplex_res["x_solution"], highs_res.x):
        if np.min(result) < -1e-7 or np.max(A_ub @ result - b_ub) > 1e-6:
            raise RuntimeError("Solver primal feasibility check failed")
    export_optimization_results(lp, simplex_res, highs_res, A_ub, b_ub)


if __name__ == "__main__":
    main()
