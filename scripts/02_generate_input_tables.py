#!/usr/bin/env python3
"""
scripts/02_generate_input_tables.py

Reads processed CSV datasets from data/processed/ and generates publication-grade
input tables in both Markdown and LaTeX formats:
  - Table 1: Supply & Dispatch Capacity Table (with Total Stock vs Dispatch Cap ratio)
  - Table 2: District Scenario Demand Table (Wheat, Rice, Total, and % share)
  - Table 3: Combined OSRM Driving-Profile Distance (km) and Unit Transport Cost (INR/MT) Matrix

Outputs:
  outputs/tables/input_tables.md
  outputs/tables/input_tables.tex
"""

import os
import pandas as pd

os.makedirs("outputs/tables", exist_ok=True)

def generate_tables():
    print("Reading processed datasets from data/processed/ ...")
    df_depots = pd.read_csv("data/processed/fci_depots_supply.csv")
    df_demands = pd.read_csv("data/processed/district_warehouses_demand.csv")
    df_dist = pd.read_csv("data/processed/distance_matrix_km.csv", index_col="depot_id")
    df_cost = pd.read_csv("data/processed/cost_matrix_inr_per_mt.csv", index_col="depot_id")

    # -------------------------------------------------------------
    # Table 1: Supply & Dispatch Capacity Table
    # -------------------------------------------------------------
    df_t1 = df_depots.copy()
    df_t1["total_stock_mt"] = df_t1["wheat_supply_mt"] + df_t1["rice_supply_mt"]
    df_t1["stock_to_cap_ratio"] = (df_t1["total_stock_mt"] / df_t1["max_dispatch_cap_mt"]).round(2)
    df_t1["bottleneck_status"] = df_t1.apply(
        lambda r: f"Assumed cap ( {r['total_stock_mt'] - r['max_dispatch_cap_mt']:,} MT below stock)", axis=1
    )

    # Format for display
    t1_display = pd.DataFrame({
        "Depot ID": df_t1["depot_id"],
        "Depot Name": df_t1["name"],
        "District": df_t1["district"],
        "Wheat Stock (MT)": df_t1["wheat_supply_mt"].apply(lambda v: f"{v:,}"),
        "Rice Stock (MT)": df_t1["rice_supply_mt"].apply(lambda v: f"{v:,}"),
        "Total Stock (MT)": df_t1["total_stock_mt"].apply(lambda v: f"{v:,}"),
        "Dispatch Cap C_i (MT)": df_t1["max_dispatch_cap_mt"].apply(lambda v: f"{v:,}"),
        "Stock / Cap Ratio": df_t1["stock_to_cap_ratio"].apply(lambda v: f"{v:.2f}x"),
        "Coupling Status": df_t1["bottleneck_status"]
    })

    # Summary row
    tot_wheat = df_t1["wheat_supply_mt"].sum()
    tot_rice = df_t1["rice_supply_mt"].sum()
    tot_stock = df_t1["total_stock_mt"].sum()
    tot_cap = df_t1["max_dispatch_cap_mt"].sum()
    tot_ratio = tot_stock / tot_cap

    t1_display.loc[len(t1_display)] = [
        "TOTAL", "Scenario Total", "Gujarat",
        f"{tot_wheat:,}", f"{tot_rice:,}", f"{tot_stock:,}", f"{tot_cap:,}",
        f"{tot_ratio:.2f}x", f"System Cap Margin: +{tot_cap - 132000:,} MT vs Demand"
    ]

    # -------------------------------------------------------------
    # Table 2: District Scenario Demand Table
    # -------------------------------------------------------------
    df_t2 = df_demands.copy()
    df_t2["total_demand_mt"] = df_t2["wheat_demand_mt"] + df_t2["rice_demand_mt"]
    total_grain_demand = df_t2["total_demand_mt"].sum()
    df_t2["share_pct"] = ((df_t2["total_demand_mt"] / total_grain_demand) * 100.0).round(2)

    t2_display = pd.DataFrame({
        "Warehouse ID": df_t2["warehouse_id"],
        "District Warehouse": df_t2["name"],
        "Facility / Godown Hub": df_t2["agency"],
        "Wheat Demand (MT)": df_t2["wheat_demand_mt"].apply(lambda v: f"{v:,}"),
        "Rice Demand (MT)": df_t2["rice_demand_mt"].apply(lambda v: f"{v:,}"),
        "Total Demand (MT)": df_t2["total_demand_mt"].apply(lambda v: f"{v:,}"),
        "Share of Demand (%)": df_t2["share_pct"].apply(lambda v: f"{v:.2f}%")
    })

    t2_display.loc[len(t2_display)] = [
        "TOTAL", "6 Target Districts", "State Civil Supplies Grid",
        f"{df_t2['wheat_demand_mt'].sum():,}",
        f"{df_t2['rice_demand_mt'].sum():,}",
        f"{total_grain_demand:,}",
        "100.00%"
    ]

    # -------------------------------------------------------------
    # Table 3: Combined Distance (km) and Cost (INR/MT) Matrix
    # -------------------------------------------------------------
    warehouse_labels = {
        "W1": "W1: Ahmedabad",
        "W2": "W2: Surat",
        "W3": "W3: Vadodara",
        "W4": "W4: Rajkot",
        "W5": "W5: Banaskantha",
        "W6": "W6: Kutch (Bhuj)"
    }
    depot_labels = {
        "D1": "D1: Sabarmati (Ahmd)",
        "D2": "D2: Chhani (Vadodara)",
        "D3": "D3: Ghanteshwar (Rajkot)",
        "D4": "D4: Gandhidham (Kutch)"
    }

    t3_combined = pd.DataFrame(index=[depot_labels[d] for d in df_dist.index])
    for w_col in df_dist.columns:
        col_name = warehouse_labels[w_col]
        t3_combined[col_name] = [
            f"{df_dist.loc[d, w_col]:.1f} km (₹{df_cost.loc[d, w_col]:.2f})"
            for d in df_dist.index
        ]

    # -------------------------------------------------------------
    # Generate Markdown Output
    # -------------------------------------------------------------
    md_content = []
    md_content.append("# Input Data Tables: Gujarat Food Grain Distribution Optimization\n")
    md_content.append("All stocks, capacities, district demands, and node coordinates are assumptions; OSRM distances are retrieved at proxy coordinates and costs are calculated from assumed rates.\n\n")
    md_content.append("## Table 1: Supply Depot Stock & Dispatch Handling Capacities\n")
    md_content.append(t1_display.to_markdown(index=False))
    md_content.append("\n\n*Key Operational Takeaway*: For every depot, the monthly dispatch throughput limit $C_i$ is strictly tighter than the total physical inventory ($S_{i,\\text{Wheat}} + S_{i,\\text{Rice}}$), with stock-to-capacity ratios ranging from $1.17\\times$ to $1.21\\times$. These assumed shared capacities couple wheat and rice; whether a constraint binds must be established by the solved allocation (D4 is slack at baseline).\n")

    md_content.append("\n## Table 2: Assumed District Monthly Food Grain Demand\n")
    md_content.append(t2_display.to_markdown(index=False))
    md_content.append("\n\n*Demand Distribution*: Urban industrial corridors (Ahmedabad and Surat) account for $51.52\\%$ of scenario food grain demand ($68,000\\text{ MT/month}$), while Saurashtra and agrarian corridors make up the remaining $48.48\\%$.\n")

    md_content.append("\n## Table 3: Combined OSRM Driving-Profile Distance & Unit Transport Cost Matrix\n")
    md_content.append("*Format: Road Distance in km (Unit Logistics Cost in INR/MT)*, where costs are rounded to paise: $c_{ij} = \\mathrm{round}(100.00 + 2.50 \\times d_{ij}, 2)$.\n\n")
    md_content.append(t3_combined.to_markdown(index=True))
    md_content.append("\n\n*Network Structure*: Highlighted entries reflect local proximity corridors (e.g. D1 $\\to$ W1 at 6.7 km, ₹116.85/MT; D2 $\\to$ W3 at 7.5 km, ₹118.80/MT; D3 $\\to$ W4 at 8.5 km, ₹121.32/MT; D4 $\\to$ W6 at 57.6 km, ₹244.05/MT).\n")

    md_output_path = "outputs/tables/input_tables.md"
    with open(md_output_path, "w") as f:
        f.write("".join(md_content))
    print(f"Generated {md_output_path}")

    # -------------------------------------------------------------
    # Generate LaTeX Output
    # -------------------------------------------------------------
    tex_content = []
    tex_content.append("% Input Data Tables for Gujarat Food Grain Distribution Optimization\n")
    tex_content.append("% Auto-generated by scripts/02_generate_input_tables.py\n\n")

    # LaTeX Table 1
    tex_content.append("\\begin{table}[htbp]\n\\centering\n")
    tex_content.append("\\caption{FCI Supply Depots: Monthly Stock and Handling Throughput Capacities (MT)}\n")
    tex_content.append("\\label{tab:supply_capacity}\n")
    tex_content.append("\\resizebox{\\textwidth}{!}{\n")
    tex_content.append("\\begin{tabular}{llccccccl}\n\\toprule\n")
    tex_content.append("Depot ID & Depot Name & District & Wheat (MT) & Rice (MT) & Total Stock (MT) & Dispatch Cap $C_i$ (MT) & Ratio & Coupling Status \\\\\n\\midrule\n")
    for _, r in t1_display.iterrows():
        is_total = r["Depot ID"] == "TOTAL"
        if is_total:
            tex_content.append("\\midrule\n")
            tex_content.append(f"\\textbf{{{r['Depot ID']}}} & \\textbf{{{r['Depot Name']}}} & \\textbf{{{r['District']}}} & \\textbf{{{r['Wheat Stock (MT)']}}} & \\textbf{{{r['Rice Stock (MT)']}}} & \\textbf{{{r['Total Stock (MT)']}}} & \\textbf{{{r['Dispatch Cap C_i (MT)']}}} & \\textbf{{{r['Stock / Cap Ratio']}}} & \\textbf{{{r['Coupling Status']}}} \\\\\n")
        else:
            tex_content.append(f"{r['Depot ID']} & {r['Depot Name']} & {r['District']} & {r['Wheat Stock (MT)']} & {r['Rice Stock (MT)']} & {r['Total Stock (MT)']} & {r['Dispatch Cap C_i (MT)']} & {r['Stock / Cap Ratio']} & {r['Coupling Status']} \\\\\n")
    tex_content.append("\\bottomrule\n\\end{tabular}\n}\n\\end{table}\n\n")

    # LaTeX Table 2
    tex_content.append("\\begin{table}[htbp]\n\\centering\n")
    tex_content.append("\\caption{District Demand Proxies: Assumed Monthly Demand (MT)}\n")
    tex_content.append("\\label{tab:district_demand}\n")
    tex_content.append("\\begin{tabular}{lllcccc}\n\\toprule\n")
    tex_content.append("ID & District Warehouse & Facility Location & Wheat (MT) & Rice (MT) & Total (MT) & Share (\\%) \\\\\n\\midrule\n")
    for _, r in t2_display.iterrows():
        is_total = r["Warehouse ID"] == "TOTAL"
        if is_total:
            tex_content.append("\\midrule\n")
            tex_content.append(f"\\textbf{{{r['Warehouse ID']}}} & \\textbf{{{r['District Warehouse']}}} & \\textbf{{{r['Facility / Godown Hub']}}} & \\textbf{{{r['Wheat Demand (MT)']}}} & \\textbf{{{r['Rice Demand (MT)']}}} & \\textbf{{{r['Total Demand (MT)']}}} & \\textbf{{{r['Share of Demand (%)']}}} \\\\\n")
        else:
            tex_content.append(f"{r['Warehouse ID']} & {r['District Warehouse']} & {r['Facility / Godown Hub']} & {r['Wheat Demand (MT)']} & {r['Rice Demand (MT)']} & {r['Total Demand (MT)']} & {r['Share of Demand (%)']} \\\\\n")
    tex_content.append("\\bottomrule\n\\end{tabular}\n\\end{table}\n\n")

    # LaTeX Table 3
    tex_content.append("\\begin{table}[htbp]\n\\centering\n")
    tex_content.append("\\caption{Driving-Profile Distance Matrix $d_{ij}$ (km) and Unit Transport Cost $c_{ij}$ (INR/MT)}\n")
    tex_content.append("\\label{tab:distance_cost_matrix}\n")
    tex_content.append("\\resizebox{\\textwidth}{!}{\n")
    tex_content.append("\\begin{tabular}{lcccccc}\n\\toprule\n")
    tex_content.append("Depot & W1 (Ahmd) & W2 (Surat) & W3 (Vadodara) & W4 (Rajkot) & W5 (Banas) & W6 (Bhuj) \\\\\n\\midrule\n")
    for idx, row in t3_combined.iterrows():
        cells = [row[col] for col in t3_combined.columns]
        cells_latex = [c.replace("₹", "\\rupee ").replace("&", "\\&") for c in cells]
        tex_content.append(f"{idx} & " + " & ".join(cells_latex) + " \\\\\n")
    tex_content.append("\\bottomrule\n\\end{tabular}\n}\n")
    tex_content.append("\\small Note: Values indicate driving-profile route distance in km followed by parenthesized unit cost in INR/MT ($c_{ij} = 100.00 + 2.50 \\times d_{ij}$).\n")
    tex_content.append("\\end{table}\n")

    tex_output_path = "outputs/tables/input_tables.tex"
    with open(tex_output_path, "w") as f:
        f.write("".join(tex_content))
    print(f"Generated {tex_output_path}")

    print("\n" + "="*80)
    print("PHASE 2: INPUT TABLES GENERATED SUCCESSFULLY")
    print("="*80)
    print("\n[TABLE 1: SUPPLY & DISPATCH CAPACITY]")
    print(t1_display.to_string(index=False))
    print("\n[TABLE 2: ASSUMED DISTRICT DEMAND]")
    print(t2_display.to_string(index=False))
    print("\n[TABLE 3: COMBINED DISTANCE & COST MATRIX]")
    print(t3_combined.to_string())
    print("\n" + "="*80)

if __name__ == "__main__":
    generate_tables()
