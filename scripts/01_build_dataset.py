#!/usr/bin/env python3
"""
scripts/01_build_dataset.py

Builds the foundational datasets for the Gujarat Food Grain Distribution Optimization:
1. Supply Nodes (4 FCI Divisional Depots with coordinates, Wheat/Rice allocations, and max dispatch capacity)
2. Demand Nodes (6 District GSCSCL Warehouses with assumed proxy coordinates and Wheat/Rice demand)
3. Driving-profile Distance & Duration Matrices from immutable OSRM response replay
4. Unit Transportation Cost Matrix c_ij = round(100.0 + 2.50 * distance_km, 2)
5. Comprehensive Data Source Register (data/source_register.csv)

Outputs:
  data/raw/osrm_response.json
  data/processed/fci_depots_supply.csv
  data/processed/district_warehouses_demand.csv
  data/processed/distance_matrix_km.csv
  data/processed/duration_matrix_hr.csv
  data/processed/cost_matrix_inr_per_mt.csv
  data/source_register.csv
"""

import os
import json
import logging
import requests
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Ensure required directory structure exists
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("outputs/tables", exist_ok=True)
os.makedirs("outputs/figures", exist_ok=True)
os.makedirs("report", exist_ok=True)

# ---------------------------------------------------------
# 1. Supply Nodes: 4 FCI Divisional Depots in Gujarat
# ---------------------------------------------------------
DEPOTS = [
    {
        "depot_id": "D1",
        "name": "FSD Sabarmati (Ahmedabad)",
        "district": "Ahmedabad",
        "latitude": 23.0760,
        "longitude": 72.5800,
        "wheat_supply_mt": 35000,
        "rice_supply_mt": 18000,
        "max_dispatch_cap_mt": 45000,
        "facility_type": "Assumed supply depot proxy"
    },
    {
        "depot_id": "D2",
        "name": "FSD Chhani (Vadodara)",
        "district": "Vadodara",
        "latitude": 22.3580,
        "longitude": 73.1650,
        "wheat_supply_mt": 22000,
        "rice_supply_mt": 12000,
        "max_dispatch_cap_mt": 28000,
        "facility_type": "Assumed supply depot proxy"
    },
    {
        "depot_id": "D3",
        "name": "FSD Ghanteshwar (Rajkot)",
        "district": "Rajkot",
        "latitude": 22.3450,
        "longitude": 70.7550,
        "wheat_supply_mt": 25000,
        "rice_supply_mt": 10000,
        "max_dispatch_cap_mt": 30000,
        "facility_type": "Assumed supply depot proxy"
    },
    {
        "depot_id": "D4",
        "name": "FSD Gandhidham (Kutch)",
        "district": "Kutch",
        "latitude": 23.0753,
        "longitude": 70.1337,
        "wheat_supply_mt": 30000,
        "rice_supply_mt": 15000,
        "max_dispatch_cap_mt": 38000,
        "facility_type": "Assumed supply depot proxy"
    }
]

# ---------------------------------------------------------
# 2. Demand Nodes: 6 District GSCSCL Warehouses in Gujarat
# ---------------------------------------------------------
WAREHOUSES = [
    {
        "warehouse_id": "W1",
        "name": "Ahmedabad District Warehouse",
        "district": "Ahmedabad",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "wheat_demand_mt": 24000,
        "rice_demand_mt": 10000,
        "agency": "Assumed district demand proxy"
    },
    {
        "warehouse_id": "W2",
        "name": "Surat District Warehouse",
        "district": "Surat",
        "latitude": 21.1702,
        "longitude": 72.8311,
        "wheat_demand_mt": 22000,
        "rice_demand_mt": 12000,
        "agency": "Assumed district demand proxy"
    },
    {
        "warehouse_id": "W3",
        "name": "Vadodara District Warehouse",
        "district": "Vadodara",
        "latitude": 22.3072,
        "longitude": 73.1812,
        "wheat_demand_mt": 14000,
        "rice_demand_mt": 7000,
        "agency": "Assumed district demand proxy"
    },
    {
        "warehouse_id": "W4",
        "name": "Rajkot District Warehouse",
        "district": "Rajkot",
        "latitude": 22.3039,
        "longitude": 70.8022,
        "wheat_demand_mt": 13000,
        "rice_demand_mt": 5000,
        "agency": "Assumed district demand proxy"
    },
    {
        "warehouse_id": "W5",
        "name": "Banaskantha District Warehouse (Palanpur)",
        "district": "Banaskantha",
        "latitude": 24.1724,
        "longitude": 72.4346,
        "wheat_demand_mt": 11000,
        "rice_demand_mt": 5000,
        "agency": "Assumed district demand proxy"
    },
    {
        "warehouse_id": "W6",
        "name": "Kutch District Warehouse (Bhuj)",
        "district": "Kutch",
        "latitude": 23.2420,
        "longitude": 69.6669,
        "wheat_demand_mt": 6000,
        "rice_demand_mt": 3000,
        "agency": "Assumed district demand proxy"
    }
]

def osrm_url():
    coords = ";".join(f"{node['longitude']:.4f},{node['latitude']:.4f}" for node in DEPOTS + WAREHOUSES)
    return (f"https://router.project-osrm.org/table/v1/driving/{coords}"
            "?sources=0;1;2;3&destinations=4;5;6;7;8;9&annotations=distance,duration")


def validate_osrm(data):
    if data.get("code") != "Ok":
        raise ValueError("Stored response is not an OSRM Ok result")
    arrays = []
    for key, divisor in (("distances", 1000), ("durations", 3600)):
        values = np.array(data[key], dtype=float)
        if values.shape != (4, 6) or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"OSRM {key} must be a complete finite nonnegative 4 x 6 matrix")
        arrays.append(np.round(values / divisor, 2))
    return arrays


def query_osrm_table():
    """Replays the immutable baseline; live retrieval is an explicit separate action."""
    from pathlib import Path
    raw_path = Path("data/raw/osrm_response.json")
    payload = raw_path.read_bytes()
    data = json.loads(payload)
    distance, duration = validate_osrm(data)
    import hashlib
    logging.info("Replaying raw baseline SHA256 %s; original retrieval timestamp is unverified",
                 hashlib.sha256(payload).hexdigest())
    return distance, duration, "REPLAYED_OSRM_RESPONSE"


def refresh_osrm():
    """Save a new timestamped response and manifest without altering the baseline."""
    from pathlib import Path
    from datetime import datetime, timezone
    import hashlib
    response = requests.get(osrm_url(), timeout=60)
    response.raise_for_status()
    validate_osrm(response.json())
    payload = response.content
    digest = hashlib.sha256(payload).hexdigest()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = Path("data/raw") / f"osrm_response_{stamp}_{digest[:12]}.json"
    with target.open("xb") as stream:
        stream.write(payload)
    target.with_suffix(".manifest.json").write_text(json.dumps({
        "url": osrm_url(), "retrieved_at_utc": stamp, "sha256": digest,
        "http_status": response.status_code, "baseline_updated": False,
        "note": "Driving profile fastest-route distance proxy; no truck restrictions verified"
    }, indent=2))
    logging.info("Saved fresh response %s; immutable baseline unchanged", target)


def build_and_save_datasets():
    logging.info("Starting Phase 1 Dataset Build Pipeline...")
    
    # Validate the immutable response before writing any processed outputs.
    dist_km, dur_hr, dist_status = query_osrm_table()

    # 1. Supply Data
    df_depots = pd.DataFrame(DEPOTS)
    df_depots.to_csv("data/processed/fci_depots_supply.csv", index=False)
    logging.info("Saved fci_depots_supply.csv (%d depots)", len(df_depots))
    
    # 2. Demand Data
    df_warehouses = pd.DataFrame(WAREHOUSES)
    df_warehouses.to_csv("data/processed/district_warehouses_demand.csv", index=False)
    logging.info("Saved district_warehouses_demand.csv (%d warehouses)", len(df_warehouses))
    
    # Feasibility validation
    tot_wheat_sup = df_depots["wheat_supply_mt"].sum()
    tot_rice_sup = df_depots["rice_supply_mt"].sum()
    tot_dispatch_cap = df_depots["max_dispatch_cap_mt"].sum()
    
    tot_wheat_dem = df_warehouses["wheat_demand_mt"].sum()
    tot_rice_dem = df_warehouses["rice_demand_mt"].sum()
    tot_grain_dem = tot_wheat_dem + tot_rice_dem
    
    logging.info("Feasibility Check:")
    logging.info("  Wheat Supply: %d MT | Wheat Demand: %d MT (Surplus: %d MT)", tot_wheat_sup, tot_wheat_dem, tot_wheat_sup - tot_wheat_dem)
    logging.info("  Rice Supply:  %d MT | Rice Demand:  %d MT (Surplus: %d MT)", tot_rice_sup, tot_rice_dem, tot_rice_sup - tot_rice_dem)
    logging.info("  Dispatch Cap: %d MT | Total Demand: %d MT (Margin:  %d MT)", tot_dispatch_cap, tot_grain_dem, tot_dispatch_cap - tot_grain_dem)
    
    if tot_wheat_sup < tot_wheat_dem:
        raise ValueError("Infeasible: Wheat demand exceeds supply")
    if tot_rice_sup < tot_rice_dem:
        raise ValueError("Infeasible: Rice demand exceeds supply")
    if tot_dispatch_cap < tot_grain_dem:
        raise ValueError("Infeasible: Total grain demand exceeds aggregate dispatch capacity")
    
    # 3. Distance and Duration via cached OSRM response
    
    depot_ids = [d["depot_id"] for d in DEPOTS]
    warehouse_ids = [w["warehouse_id"] for w in WAREHOUSES]
    
    df_dist = pd.DataFrame(dist_km, index=depot_ids, columns=warehouse_ids)
    df_dist.index.name = "depot_id"
    df_dist.to_csv("data/processed/distance_matrix_km.csv")
    logging.info("Saved distance_matrix_km.csv [Shape: %s, Status: %s]", df_dist.shape, dist_status)
    
    df_dur = pd.DataFrame(dur_hr, index=depot_ids, columns=warehouse_ids)
    df_dur.index.name = "depot_id"
    df_dur.to_csv("data/processed/duration_matrix_hr.csv")
    logging.info("Saved duration_matrix_hr.csv [Shape: %s]", df_dur.shape)
    
    # 4. Unit Cost Matrix c_ij (INR per MT)
    # Formula: c_ij = round(100.0 + 2.50 * distance_km, 2)
    # Fixed handling = 100 INR/MT; Freight rate = 2.50 INR/MT/km
    cost_matrix = np.round(100.0 + 2.50 * dist_km, 2)
    df_cost = pd.DataFrame(cost_matrix, index=depot_ids, columns=warehouse_ids)
    df_cost.index.name = "depot_id"
    df_cost.to_csv("data/processed/cost_matrix_inr_per_mt.csv")
    logging.info("Saved cost_matrix_inr_per_mt.csv [Shape: %s]", df_cost.shape)
    
    # 5. Master Data Source Register
    import hashlib
    from pathlib import Path
    baseline_hash = hashlib.sha256(Path("data/raw/osrm_response.json").read_bytes()).hexdigest()
    source_register = [
        dict(Source_Name="Gujarat official depot directory (undated historical document)", Official_URL_or_Document_ID="https://gil.gujarat.gov.in/tendercms/TenderDocs/2011824164857520.pdf", Date_Accessed="2026-11-07", Specific_Data_Fields="Historical depot names only; does not establish current operations, modeled coordinates, stocks or throughput", Verification_Status="VERIFIED", Category="OFFICIAL"),
        dict(Source_Name="Illustrative supply and dispatch scenario", Official_URL_or_Document_ID="scripts/01_build_dataset.py:DEPOTS", Date_Accessed="N/A", Specific_Data_Fields="All depot coordinates, commodity stocks, monthly dispatch caps and modeled facility descriptions", Verification_Status="ASSUMED", Category="ASSUMPTION"),
        dict(Source_Name="Illustrative district demand proxies", Official_URL_or_Document_ID="scripts/01_build_dataset.py:WAREHOUSES", Date_Accessed="N/A", Specific_Data_Fields="District aggregation, proxy coordinates, wheat/rice monthly demand; not measured warehouses or statutory district quotas", Verification_Status="ASSUMED", Category="ASSUMPTION"),
        dict(Source_Name="Stored OSRM driving response", Official_URL_or_Document_ID=osrm_url(), Date_Accessed="Original timestamp unverified; replayed 2026-11-07", Specific_Data_Fields=f"Driving-profile distance and duration at assumed coordinates; raw SHA256 {baseline_hash}; no retrieval manifest for original snapshot", Verification_Status="PROVISIONAL", Category="RETRIEVED"),
        dict(Source_Name="Distance/duration transformations", Official_URL_or_Document_ID="scripts/01_build_dataset.py:validate_osrm", Date_Accessed="N/A", Specific_Data_Fields="Raw meters /1000 and seconds /3600, rounded to 2 decimals", Verification_Status="VERIFIED", Category="CALCULATED"),
        dict(Source_Name="Illustrative freight parameters", Official_URL_or_Document_ID="scripts/01_build_dataset.py", Date_Accessed="N/A", Specific_Data_Fields="Handling alpha=100 INR/MT and freight beta=2.50 INR/MT-km; no supporting tender benchmark", Verification_Status="ASSUMED", Category="ASSUMPTION"),
        dict(Source_Name="Rounded scenario cost matrix", Official_URL_or_Document_ID="scripts/01_build_dataset.py", Date_Accessed="N/A", Specific_Data_Fields="numpy.round(100 + 2.50 * rounded distance_km, 2); dependent on assumed cost parameters", Verification_Status="VERIFIED", Category="CALCULATED")
    ]
    # A fresh retrieval verifies its own timestamp/hash and routing fields;
    # it does not retroactively establish the baseline's original retrieval date.
    for manifest_path in sorted(Path("data/raw").glob("osrm_response_*.manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        snapshot_path = manifest_path.with_name(manifest_path.name.replace(".manifest.json", ".json"))
        payload = snapshot_path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if manifest.get("sha256") != digest:
            raise ValueError(f"Routing snapshot SHA256 mismatch: {snapshot_path}")
        if manifest.get("url") != osrm_url() or manifest.get("http_status") != 200:
            raise ValueError(f"Routing snapshot query/status mismatch: {manifest_path}")
        distance, duration = validate_osrm(json.loads(payload))
        same = np.array_equal(distance, dist_km) and np.array_equal(duration, dur_hr)
        source_register.append(dict(
            Source_Name="Fresh OSRM driving retrieval (separate immutable snapshot)",
            Official_URL_or_Document_ID=manifest["url"],
            Date_Accessed=manifest["retrieved_at_utc"],
            Specific_Data_Fields=(f"Driving-profile distance/duration at assumed coordinates; snapshot {snapshot_path}; "
                                 f"SHA256 {digest}; processed distance/duration identical to baseline: {same}; "
                                 "original baseline retrieval date remains unverified; truck restrictions not verified"),
            Verification_Status="VERIFIED", Category="RETRIEVED"))
    df_sources = pd.DataFrame(source_register)
    df_sources.to_csv("data/source_register.csv", index=False)
    logging.info("Saved data/source_register.csv (%d classified source records)", len(df_sources))
    
    print("\n" + "="*70)
    print("PHASE 1 DATASET BUILD COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\n[FCI Depots (Supply)]")
    print(df_depots[["depot_id", "name", "wheat_supply_mt", "rice_supply_mt", "max_dispatch_cap_mt"]].to_string(index=False))
    print("\n[District Warehouses (Demand)]")
    print(df_warehouses[["warehouse_id", "name", "wheat_demand_mt", "rice_demand_mt"]].to_string(index=False))
    print("\n[Distance Matrix (km)]")
    print(df_dist.to_string())
    print("\n[Unit Cost Matrix (INR/MT)]")
    print(df_cost.to_string())
    print("\n" + "="*70)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Replay stored baseline; --refresh saves a separate live snapshot")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.refresh:
        refresh_osrm()
    else:
        build_and_save_datasets()
