"""
Independent QA Verification Suite for Phase 1
Food Grain Distribution Optimization (Gujarat FCI to District Warehouses)
Course: CE 637 Infrastructure Systems

Auditor: Independent QA & Challenge Agent
"""

import os
import sys
import json
import re
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_qa_checks():
    print("=" * 80)
    print("INDEPENDENT QA AUDIT: PHASE 1 INFRASTRUCTURE OPTIMIZATION DATASET")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Python Executable: {sys.executable}")
    print("=" * 80)
    
    passed_checks = 0
    total_checks = 0
    
    # -------------------------------------------------------------
    # 1. FILE EXISTENCE & INTEGRITY CHECK
    # -------------------------------------------------------------
    print("\n[CHECK 1] Required File Existence & Integrity Check:")
    required_files = [
        "requirements.txt",
        "data/raw/osrm_response.json",
        "data/processed/fci_depots_supply.csv",
        "data/processed/district_warehouses_demand.csv",
        "data/processed/distance_matrix_km.csv",
        "data/processed/cost_matrix_inr_per_mt.csv",
        "data/source_register.csv",
        "scripts/01_build_dataset.py",
        "README.md",
        "PROJECT_GUIDE.md"
    ]
    
    all_files_exist = True
    for rel_path in required_files:
        full_path = os.path.join(BASE_DIR, rel_path)
        exists = os.path.isfile(full_path)
        sz = os.path.getsize(full_path) if exists else 0
        total_checks += 1
        if exists and sz > 0:
            print(f"  [PASS] {rel_path} ({sz} bytes)")
            passed_checks += 1
        else:
            print(f"  [FAIL] {rel_path} (Missing or empty!)")
            all_files_exist = False
            
    assert all_files_exist, "One or more required files are missing or empty."
    
    # -------------------------------------------------------------
    # 2. NUMERICAL & DIMENSIONAL VERIFICATION
    # -------------------------------------------------------------
    print("\n[CHECK 2] Distance Matrix Dimensionality & Sanity Checks:")
    dist_file = os.path.join(BASE_DIR, "data/processed/distance_matrix_km.csv")
    df_dist = pd.read_csv(dist_file, index_col=0)
    print(f"  Loaded Distance Matrix:\n{df_dist}")
    
    # Assert shape is (4, 6)
    total_checks += 1
    assert df_dist.shape == (4, 6), f"Distance matrix shape expected (4, 6), got {df_dist.shape}"
    print(f"  [PASS] Distance matrix shape is exactly (4, 6)")
    passed_checks += 1
    
    # Assert rows and cols
    total_checks += 1
    expected_rows = ['D1', 'D2', 'D3', 'D4']
    expected_cols = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6']
    assert list(df_dist.index) == expected_rows, f"Expected rows {expected_rows}, got {list(df_dist.index)}"
    assert list(df_dist.columns) == expected_cols, f"Expected cols {expected_cols}, got {list(df_dist.columns)}"
    print(f"  [PASS] Rows are D1..D4 and columns are W1..W6")
    passed_checks += 1
    
    # Assert all positive floats
    total_checks += 1
    assert (df_dist.values > 0).all(), "All distances must be strictly positive floats!"
    print(f"  [PASS] All distances are strictly positive (min={df_dist.values.min():.2f} km, max={df_dist.values.max():.2f} km)")
    passed_checks += 1
    
    # Cluster distance reasonableness
    print("\n[CHECK 3] Local Cluster Proximity Checks:")
    cluster_checks = [
        ("D1", "W1", 15.0, "FSD Sabarmati -> Ahmedabad Warehouse"),
        ("D2", "W3", 15.0, "FSD Chhani -> Vadodara Warehouse"),
        ("D3", "W4", 15.0, "FSD Ghanteshwar -> Rajkot Warehouse"),
        ("D4", "W6", 70.0, "FSD Gandhidham -> Kutch (Bhuj) Warehouse")
    ]
    for depot, wh, limit, name in cluster_checks:
        total_checks += 1
        d_val = df_dist.loc[depot, wh]
        assert d_val < limit, f"Cluster distance for {name} ({depot}->{wh}) is {d_val} km >= {limit} km"
        print(f"  [PASS] {name} ({depot}->{wh}): {d_val:.2f} km < {limit} km limit")
        passed_checks += 1
        
    # Cost Matrix check
    print("\n[CHECK 4] Cost Matrix Formulation Check (|c_ij - (100.0 + 2.50 * d_ij)| < 0.02):")
    cost_file = os.path.join(BASE_DIR, "data/processed/cost_matrix_inr_per_mt.csv")
    df_cost = pd.read_csv(cost_file, index_col=0)
    print(f"  Loaded Cost Matrix:\n{df_cost}")
    
    total_checks += 1
    assert df_cost.shape == (4, 6), f"Cost matrix shape expected (4, 6), got {df_cost.shape}"
    passed_checks += 1
    
    max_cost_discrepancy = 0.0
    for i in expected_rows:
        for j in expected_cols:
            d_val = df_dist.loc[i, j]
            c_val = df_cost.loc[i, j]
            expected_c = 100.0 + 2.50 * d_val
            diff = abs(c_val - expected_c)
            if diff > max_cost_discrepancy:
                max_cost_discrepancy = diff
            assert diff < 0.02, f"Cost discrepancy at ({i}, {j}): actual {c_val}, expected {expected_c}, diff {diff} >= 0.02"
    
    total_checks += 1
    print(f"  [PASS] Cost formula c_ij = 100.0 + 2.50 * d_ij verified across all 24 pairs. Max absolute discrepancy = {max_cost_discrepancy:.6f} INR/MT (< 0.02)")
    passed_checks += 1
    
    # -------------------------------------------------------------
    # 3. FEASIBILITY & CONSERVATION CHECKS
    # -------------------------------------------------------------
    print("\n[CHECK 5] Supply vs Demand Feasibility Checks:")
    depots_file = os.path.join(BASE_DIR, "data/processed/fci_depots_supply.csv")
    wh_file = os.path.join(BASE_DIR, "data/processed/district_warehouses_demand.csv")
    df_supply = pd.read_csv(depots_file)
    df_demand = pd.read_csv(wh_file)
    
    tot_wheat_supply = df_supply['wheat_supply_mt'].sum()
    tot_rice_supply = df_supply['rice_supply_mt'].sum()
    tot_dispatch_cap = df_supply['max_dispatch_cap_mt'].sum()
    
    tot_wheat_demand = df_demand['wheat_demand_mt'].sum()
    tot_rice_demand = df_demand['rice_demand_mt'].sum()
    tot_demand = tot_wheat_demand + tot_rice_demand
    
    print(f"  Wheat Supply: {tot_wheat_supply:,} MT | Wheat Demand: {tot_wheat_demand:,} MT (Surplus: +{tot_wheat_supply - tot_wheat_demand:,} MT)")
    print(f"  Rice Supply:  {tot_rice_supply:,} MT  | Rice Demand:  {tot_rice_demand:,} MT (Surplus: +{tot_rice_supply - tot_rice_demand:,} MT)")
    print(f"  Dispatch Cap: {tot_dispatch_cap:,} MT | Total Demand: {tot_demand:,} MT (Surplus: +{tot_dispatch_cap - tot_demand:,} MT)")
    
    total_checks += 1
    assert tot_wheat_supply == 112000, f"Expected total wheat supply 112,000 MT, got {tot_wheat_supply}"
    assert tot_wheat_demand == 90000, f"Expected total wheat demand 90,000 MT, got {tot_wheat_demand}"
    assert tot_wheat_supply >= tot_wheat_demand, "Wheat supply cannot satisfy demand!"
    print(f"  [PASS] Wheat Supply (112,000 MT) >= Demand (90,000 MT)")
    passed_checks += 1
    
    total_checks += 1
    assert tot_rice_supply == 55000, f"Expected total rice supply 55,000 MT, got {tot_rice_supply}"
    assert tot_rice_demand == 42000, f"Expected total rice demand 42,000 MT, got {tot_rice_demand}"
    assert tot_rice_supply >= tot_rice_demand, "Rice supply cannot satisfy demand!"
    print(f"  [PASS] Rice Supply (55,000 MT) >= Demand (42,000 MT)")
    passed_checks += 1
    
    total_checks += 1
    assert tot_dispatch_cap == 141000, f"Expected total dispatch capacity 141,000 MT, got {tot_dispatch_cap}"
    assert tot_demand == 132000, f"Expected total demand 132,000 MT, got {tot_demand}"
    assert tot_dispatch_cap >= tot_demand, "Dispatch capacity cannot satisfy total demand!"
    print(f"  [PASS] Total Dispatch Capacity (141,000 MT) >= Total Demand (132,000 MT)")
    passed_checks += 1
    
    # -------------------------------------------------------------
    # 4. STORED OSRM PAYLOAD STRUCTURAL AUDIT
    # -------------------------------------------------------------
    print("\n[CHECK 6] Stored OSRM Payload Audit:")
    osrm_file = os.path.join(BASE_DIR, "data/raw/osrm_response.json")
    with open(osrm_file, 'r', encoding='utf-8') as f:
        osrm_json = json.load(f)
        
    osrm_code = osrm_json.get("code")
    print(f"  OSRM Status Code: {osrm_code}")
    total_checks += 1
    assert osrm_code == "Ok", f"OSRM status is not 'Ok': {osrm_code}"
    print(f"  [PASS] Stored payload has OSRM success status; this does not establish acquisition authenticity")
    passed_checks += 1
    
    sources = osrm_json.get("sources", [])
    destinations = osrm_json.get("destinations", [])
    raw_distances = osrm_json.get("distances", [])
    raw_durations = osrm_json.get("durations", [])
    
    total_checks += 1
    assert len(sources) == 4, f"Expected 4 sources, got {len(sources)}"
    assert len(destinations) == 6, f"Expected 6 destinations, got {len(destinations)}"
    assert len(raw_distances) == 4 and all(len(row) == 6 for row in raw_distances), "Distances matrix dimensions must be 4x6"
    assert len(raw_durations) == 4 and all(len(row) == 6 for row in raw_durations), "Durations matrix dimensions must be 4x6"
    print(f"  [PASS] OSRM response has valid dimensions: 4 sources, 6 destinations, 4x6 distance and duration matrices")
    passed_checks += 1
    
    # Operational guide must document the actual replay and scenario limitations.
    print("\n[CHECK 7] Reproducibility and interpretation guide:")
    with open(os.path.join(BASE_DIR, "PROJECT_GUIDE.md"), encoding="utf-8") as f:
        guide_text = f.read()
    for phrase in ("scripts/01_build_dataset.py", "scripts/03_solve_optimization.py", "assumptions", "seven-page report", "one-page A3 landscape poster"):
        total_checks += 1
        assert phrase in guide_text, f"Missing guide requirement: {phrase}"
        passed_checks += 1
        print(f"  [PASS] Guide documents {phrase}")

    # -------------------------------------------------------------
    # SUMMARY AUDIT VERDICT
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"AUDIT SUMMARY: {passed_checks}/{total_checks} CHECKS PASSED (100%)")
    print("STRUCTURAL DATA CHECKS SATISFIED; EXTERNAL AUTHENTICITY REQUIRES SEPARATE SOURCE EVIDENCE.")
    print("VERDICT: PASS")
    print("=" * 80)

import unittest


class TestPhase1Dataset(unittest.TestCase):
    def test_phase1_structural_checks(self):
        run_qa_checks()


if __name__ == "__main__":
    run_qa_checks()
