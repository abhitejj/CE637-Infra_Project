#!/usr/bin/env python3
"""
scripts/05_generate_figures.py

Generates publication-grade, high-resolution (300 DPI) figures for the Gujarat
Food Grain Distribution Optimization project:
  1. fig1_network_flow_map.png:
     Optimal FCI-to-District Food Grain Distribution Network in Gujarat,
     directional curved shipment arrows weighted by tonnage, and non-overlapping
     callouts with leader lines.
  2. fig2_depot_utilization.png:
     Grouped bar chart comparing Wheat Stock, Rice Stock, Total Dispatched Tonnage,
     and Max Dispatch Capacity (C_i) across the 4 depots, highlighting binding limits.
  3. fig3_sensitivity_curve.png:
     Dual-axis plot showing Total Monthly Logistics Cost (INR Crores) and
     Marginal Shadow Price (INR/MT) as a function of Vadodara Dispatch Capacity C_2.

Outputs:
  outputs/figures/fig1_network_flow_map.png
  outputs/figures/fig2_depot_utilization.png
  outputs/figures/fig3_sensitivity_curve.png
  outputs/figures/fig3_sensitivity_curve_shadow_price.png
"""

import os
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

# Configure plotting style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 14,
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
os.makedirs("outputs/figures", exist_ok=True)


def plot_fig1_network_flow_map():
    """Generates the clean, collision-free geographic network flow map across Gujarat."""
    logging.info("Generating fig1_network_flow_map.png ...")
    df_depots = pd.read_csv("data/processed/fci_depots_supply.csv")
    df_demands = pd.read_csv("data/processed/district_warehouses_demand.csv")
    df_shipments = pd.read_csv("outputs/tables/optimal_shipments_wheat_rice.csv")

    fig, ax = plt.subplots(figsize=(12, 9))

    # Base coordinates
    depot_base = {}
    for _, r in df_depots.iterrows():
        depot_base[r["depot_id"]] = (r["longitude"], r["latitude"], r["name"], r["max_dispatch_cap_mt"])

    wh_base = {}
    for _, r in df_demands.iterrows():
        wh_base[r["warehouse_id"]] = (r["longitude"], r["latitude"], r["name"], r["wheat_demand_mt"] + r["rice_demand_mt"])

    # Visual jitter offsets for co-located clusters (~7 km apart)
    # Allows square (Depot) and circle (Warehouse) markers to sit side-by-side cleanly
    depot_plot = {
        "D1": (depot_base["D1"][0] - 0.05, depot_base["D1"][1] + 0.02),
        "D2": (depot_base["D2"][0] - 0.05, depot_base["D2"][1] + 0.02),
        "D3": (depot_base["D3"][0] - 0.05, depot_base["D3"][1] + 0.02),
        "D4": (depot_base["D4"][0], depot_base["D4"][1])  # Gandhidham
    }

    wh_plot = {
        "W1": (wh_base["W1"][0] + 0.05, wh_base["W1"][1] - 0.02),  # Ahmedabad
        "W2": (wh_base["W2"][0], wh_base["W2"][1]),                # Surat
        "W3": (wh_base["W3"][0] + 0.05, wh_base["W3"][1] - 0.02),  # Vadodara
        "W4": (wh_base["W4"][0] + 0.05, wh_base["W4"][1] - 0.02),  # Rajkot
        "W5": (wh_base["W5"][0], wh_base["W5"][1]),                # Banaskantha
        "W6": (wh_base["W6"][0], wh_base["W6"][1])                 # Kutch (Bhuj)
    }

    # Distinct thematic colors for origin depots
    depot_colors = {
        "D1": "#1f77b4",  # Blue (Sabarmati)
        "D2": "#ff7f0e",  # Orange (Chhani)
        "D3": "#2ca02c",  # Green (Ghanteshwar)
        "D4": "#d62728"   # Red (Gandhidham)
    }

    # Draw 9 Active Shipping Corridors using FancyArrowPatch
    # Long-haul corridors are curved to prevent cutting through intermediate clusters (e.g. Rajkot)
    corridor_configs = {
        # Long-haul Surat bypasses
        ("D4", "W2"): {"rad": -0.22, "label_pos": (70.95, 21.55), "text": "4,000 MT\n(W:0 | R:4,000)"},
        ("D3", "W2"): {"rad": -0.08, "label_pos": (71.85, 21.75), "text": "12,000 MT\n(W:12k | R:0)"},
        ("D1", "W2"): {"rad": -0.06, "label_pos": (72.60, 21.95), "text": "11,000 MT\n(W:3k | R:8k)"},
        ("D2", "W2"): {"rad": 0.08,  "label_pos": (73.25, 21.65), "text": "7,000 MT\n(W:7k | R:0)"},
        # Long-haul Banaskantha corridor
        ("D4", "W5"): {"rad": -0.05, "label_pos": (71.25, 23.70), "text": "16,000 MT\n(W:11k | R:5k)"},
        # Local short-haul corridors (straight connection)
        ("D1", "W1"): {"rad": 0.0, "label_pos": None, "text": None},
        ("D2", "W3"): {"rad": 0.0, "label_pos": None, "text": None},
        ("D3", "W4"): {"rad": 0.0, "label_pos": None, "text": None},
        ("D4", "W6"): {"rad": 0.0, "label_pos": None, "text": None}
    }

    df_active = df_shipments[df_shipments["total_shipped_mt"] > 0].copy()
    # Draw thicker arrows first so thinner ones stay visible
    df_active = df_active.sort_values(by="total_shipped_mt", ascending=False)

    for _, row in df_active.iterrows():
        d_id = row["depot_id"]
        w_id = row["warehouse_id"]
        tot_mt = row["total_shipped_mt"]

        p_start = depot_plot[d_id]
        p_end = wh_plot[w_id]
        cfg = corridor_configs.get((d_id, w_id), {"rad": 0.0, "label_pos": None, "text": None})

        # Scaled line weight proportional to tonnage
        lw = max(1.3, (tot_mt / 34000.0) * 6.5)
        color = depot_colors[d_id]

        arrow = FancyArrowPatch(
            posA=p_start,
            posB=p_end,
            connectionstyle=f"arc3,rad={cfg['rad']}",
            arrowstyle="-|>",
            mutation_scale=14,
            shrinkA=8,
            shrinkB=8,
            color=color,
            lw=lw,
            alpha=0.78,
            zorder=3
        )
        ax.add_patch(arrow)

        # Draw mid-corridor label for long-haul routes
        if cfg["label_pos"] is not None:
            lx, ly = cfg["label_pos"]
            ax.text(
                lx, ly,
                cfg["text"],
                fontsize=7.5,
                fontweight="bold",
                ha="center",
                va="center",
                color="#111111",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=color, alpha=0.92, lw=0.8),
                zorder=7
            )

    # Plot Scatter Points: District Warehouses (Circles)
    for w_id, (wx, wy) in wh_plot.items():
        ax.scatter(wx, wy, color="#2b5c8f", s=130, marker="o", edgecolors="black", linewidths=1.5, zorder=5)

    # Plot Scatter Points: FCI Depots (Squares)
    for d_id, (dx, dy) in depot_plot.items():
        ax.scatter(dx, dy, color=depot_colors[d_id], s=180, marker="s", edgecolors="black", linewidths=1.8, zorder=6)

    # =========================================================================
    # EXPLICIT NON-OVERLAPPING CALLOUTS WITH LEADER LINES
    # =========================================================================

    # 1. Kutch Cluster (D4 Gandhidham & W6 Bhuj)
    ax.annotate(
        "W6: Kutch / Bhuj (9,000 MT)",
        xy=wh_plot["W6"],
        xytext=(-20, 25),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color="#0b2545",
        ha="right",
        va="bottom",
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    ax.annotate(
        "D4: FSD Gandhidham\n(Cap: 38,000 MT)",
        xy=depot_plot["D4"],
        xytext=(-30, -45),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color=depot_colors["D4"],
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=depot_colors["D4"], alpha=0.92, lw=1.0),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    # Flow box between D4 and W6
    mid_kutch = ((depot_plot["D4"][0] + wh_plot["W6"][0]) / 2.0, (depot_plot["D4"][1] + wh_plot["W6"][1]) / 2.0)
    ax.annotate(
        "9,000 MT\n(W:6k | R:3k)",
        xy=mid_kutch,
        xytext=(0, 16),
        textcoords="offset points",
        fontsize=7.5,
        fontweight="bold",
        color="#111111",
        ha="center",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#fefefe", edgecolor="#aaaaaa", alpha=0.92, lw=0.6),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=7
    )

    # 2. Rajkot Cluster (D3 Ghanteshwar & W4 Rajkot)
    ax.annotate(
        "D3: FSD Ghanteshwar\n(Cap: 30,000 MT)",
        xy=depot_plot["D3"],
        xytext=(0, 35),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color=depot_colors["D3"],
        ha="center",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=depot_colors["D3"], alpha=0.92, lw=1.0),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    ax.annotate(
        "W4: Rajkot (18,000 MT)",
        xy=wh_plot["W4"],
        xytext=(-85, -28),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color="#0b2545",
        ha="right",
        va="top",
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    # Local flow box D3 -> W4
    mid_rajkot = ((depot_plot["D3"][0] + wh_plot["W4"][0]) / 2.0, (depot_plot["D3"][1] + wh_plot["W4"][1]) / 2.0)
    ax.annotate(
        "Local: 18,000 MT\n(W:13k | R:5k)",
        xy=mid_rajkot,
        xytext=(18, 14),
        textcoords="offset points",
        fontsize=7.5,
        fontweight="bold",
        color="#111111",
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#fefefe", edgecolor=depot_colors["D3"], alpha=0.92, lw=0.6),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=7
    )

    # 3. Ahmedabad Cluster (D1 Sabarmati & W1 Ahmedabad)
    ax.annotate(
        "D1: FSD Sabarmati\n(Cap: 45,000 MT)",
        xy=depot_plot["D1"],
        xytext=(-125, 25),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color=depot_colors["D1"],
        ha="right",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=depot_colors["D1"], alpha=0.92, lw=1.0),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    ax.annotate(
        "W1: Ahmedabad (34,000 MT)",
        xy=wh_plot["W1"],
        xytext=(18, -5),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color="#0b2545",
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    # Local flow box D1 -> W1
    mid_ahmd = ((depot_plot["D1"][0] + wh_plot["W1"][0]) / 2.0, (depot_plot["D1"][1] + wh_plot["W1"][1]) / 2.0)
    ax.annotate(
        "Local: 34,000 MT\n(W:24k | R:10k)",
        xy=mid_ahmd,
        xytext=(18, 22),
        textcoords="offset points",
        fontsize=7.5,
        fontweight="bold",
        color="#111111",
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#fefefe", edgecolor=depot_colors["D1"], alpha=0.92, lw=0.6),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=7
    )

    # 4. Vadodara Cluster (D2 Chhani & W3 Vadodara)
    ax.annotate(
        "D2: FSD Chhani\n(Cap: 28,000 MT)",
        xy=depot_plot["D2"],
        xytext=(-110, 26),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color=depot_colors["D2"],
        ha="right",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=depot_colors["D2"], alpha=0.92, lw=1.0),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    ax.annotate(
        "W3: Vadodara (21,000 MT)",
        xy=wh_plot["W3"],
        xytext=(18, -12),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color="#0b2545",
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    # Local flow box D2 -> W3
    mid_vado = ((depot_plot["D2"][0] + wh_plot["W3"][0]) / 2.0, (depot_plot["D2"][1] + wh_plot["W3"][1]) / 2.0)
    ax.annotate(
        "Local: 21,000 MT\n(W:14k | R:7k)",
        xy=mid_vado,
        xytext=(18, 18),
        textcoords="offset points",
        fontsize=7.5,
        fontweight="bold",
        color="#111111",
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#fefefe", edgecolor=depot_colors["D2"], alpha=0.92, lw=0.6),
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=7
    )

    # 5. Standalone Warehouses: Banaskantha (W5) & Surat (W2)
    ax.annotate(
        "W5: Banaskantha / Palanpur (16,000 MT)",
        xy=wh_plot["W5"],
        xytext=(-20, 20),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color="#0b2545",
        ha="right",
        va="bottom",
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )
    ax.annotate(
        "W2: Surat (34,000 MT)",
        xy=wh_plot["W2"],
        xytext=(14, -8),
        textcoords="offset points",
        fontsize=8.5,
        fontweight="bold",
        color="#0b2545",
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
        zorder=8
    )

    # Title & Labels
    ax.set_title("Optimal FCI-to-District Food Grain Distribution Network in Gujarat", fontsize=13, pad=15, fontweight="bold")
    ax.set_xlabel("Longitude (°E)", labelpad=8)
    ax.set_ylabel("Latitude (°N)", labelpad=8)

    # Axis Limits with generous framing margin
    ax.set_xlim(68.5, 74.8)
    ax.set_ylim(20.5, 24.8)
    ax.grid(True, linestyle="--", alpha=0.4)

    # Custom Legend
    legend_elements = [
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=depot_colors["D1"], markersize=10, label="FSD Sabarmati (Ahmedabad)"),
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=depot_colors["D2"], markersize=10, label="FSD Chhani (Vadodara)"),
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=depot_colors["D3"], markersize=10, label="FSD Ghanteshwar (Rajkot)"),
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=depot_colors["D4"], markersize=10, label="FSD Gandhidham (Kutch)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#2b5c8f", markersize=9, label="GSCSCL District Warehouse (Demand)"),
        plt.Line2D([0], [0], color="#555555", lw=3.0, label="Corridor Flow (width $\\propto$ MT)")
    ]
    ax.legend(handles=legend_elements, loc="upper right", framealpha=0.95, edgecolor="#999999", fontsize=9)

    fig.tight_layout()
    output_path = "outputs/figures/fig1_network_flow_map.png"
    plt.savefig(output_path)
    plt.close()
    logging.info("Saved %s", output_path)


def plot_fig2_depot_utilization():
    """Generates the grouped bar chart comparing stock, dispatched tonnage, and capacity."""
    logging.info("Generating fig2_depot_utilization.png ...")
    df_depots = pd.read_csv("data/processed/fci_depots_supply.csv")
    df_shipments = pd.read_csv("outputs/tables/optimal_shipments_wheat_rice.csv")

    # Aggregate dispatched tonnage by depot
    df_disp = df_shipments.groupby("depot_id")["total_shipped_mt"].sum().reset_index()
    df_merged = df_depots.merge(df_disp, on="depot_id")

    depot_labels = [
        "D1: Sabarmati\n(Ahmedabad)",
        "D2: Chhani\n(Vadodara)",
        "D3: Ghanteshwar\n(Rajkot)",
        "D4: Gandhidham\n(Kutch)"
    ]

    # Specific shadow prices for each depot capacity constraint
    shadow_prices = {
        "D1": "Rs. 767",
        "D2": "Rs. 1,023",
        "D3": "Rs. 336",
        "D4": "Rs. 0"
    }

    x = np.arange(len(depot_labels))
    width = 0.20

    fig, ax = plt.subplots(figsize=(10.5, 6.2))

    rects1 = ax.bar(x - 1.5 * width, df_merged["wheat_supply_mt"], width, label="Wheat in Stock", color="#e69f00", edgecolor="black", alpha=0.9)
    rects2 = ax.bar(x - 0.5 * width, df_merged["rice_supply_mt"], width, label="Rice in Stock", color="#56b4e9", edgecolor="black", alpha=0.9)
    rects3 = ax.bar(x + 0.5 * width, df_merged["total_shipped_mt"], width, label="Grain Sent", color="#009e73", edgecolor="black", alpha=0.9)
    rects4 = ax.bar(x + 1.5 * width, df_merged["max_dispatch_cap_mt"], width, label="Loading Limit", color="#d55e00", edgecolor="black", alpha=0.9)

    # Highlight binding capacity limits with shadow prices and annotate total stock
    for i in range(len(df_merged)):
        d_id = df_merged.loc[i, "depot_id"]
        tot_disp = df_merged.loc[i, "total_shipped_mt"]
        cap = df_merged.loc[i, "max_dispatch_cap_mt"]
        w_stock = df_merged.loc[i, "wheat_supply_mt"]
        r_stock = df_merged.loc[i, "rice_supply_mt"]
        total_stock = w_stock + r_stock
        sp_text = shadow_prices[d_id]

        # Annotate total physical stock above the stock bars (centered between rects1 and rects2)
        stock_x = x[i] - 1.0 * width
        max_stock_bar = max(w_stock, r_stock)
        ax.annotate(
            f"Total Stock:\n{int(total_stock):,} MT",
            xy=(stock_x, max_stock_bar),
            xytext=(stock_x, max_stock_bar + 2500),
            ha="center",
            va="bottom",
            fontsize=7.8,
            fontweight="bold",
            color="#555555",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#fffbee", edgecolor="#d4af37", alpha=0.85, lw=0.6)
        )

        if abs(tot_disp - cap) < 1e-4:
            ax.annotate(
                f"All loading capacity used\nSavings per extra MT: {sp_text}",
                xy=(x[i] + 1.5 * width, cap),
                xytext=(x[i] + 1.5 * width, cap + 6500),
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color="#b30000",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffebee", edgecolor="#b30000", alpha=0.9, lw=0.8),
                arrowprops=dict(arrowstyle="->", color="#b30000", lw=1.2)
            )
        else:
            buffer_mt = cap - tot_disp
            ax.annotate(
                f"Spare loading capacity: {int(buffer_mt):,} MT\nSavings per extra MT: {sp_text}",
                xy=(x[i] + 1.5 * width, cap),
                xytext=(x[i], cap + 3500),
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color="#006633",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#e8f5e9", edgecolor="#006633", alpha=0.9, lw=0.8),
                arrowprops=dict(arrowstyle="->", color="#006633", lw=1.2)
            )

    ax.set_ylabel("Quantity (Metric Tonnes / MT)", fontsize=11, fontweight="bold")
    ax.set_title("Grain in Stock, Grain Sent and Loading Limits", fontsize=12, pad=15, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(depot_labels, fontsize=10, fontweight="bold")
    ax.set_ylim(0, 62000)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper right", framealpha=0.95)

    # Add data values on top of dispatched bars
    for r in rects3:
        h = r.get_height()
        ax.annotate(f"{int(h):,} MT", xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

    fig.tight_layout()
    output_path = "outputs/figures/fig2_depot_utilization.png"
    plt.savefig(output_path)
    plt.close()
    logging.info("Saved %s", output_path)


def plot_fig3_sensitivity_curve(*, shadow_price=False):
    """Plot cost and marginal savings with the poster or report labels."""
    if shadow_price:
        title = "Chhani Capacity Expansion: Scenario Cost and Shadow Price"
        savings_label = "Shadow Price (Marginal Cost Savings in INR/MT)"
        filename = "fig3_sensitivity_curve_shadow_price.png"
    else:
        title = "Monthly Cost and Savings at Chhani"
        savings_label = "Savings per Extra Tonne (Rs./MT)"
        filename = "fig3_sensitivity_curve.png"
    logging.info("Generating %s ...", filename)
    df_sens = pd.read_csv("outputs/tables/sensitivity_results.csv")
    df_exp1 = df_sens[df_sens["experiment"] == "Exp1_Capacity_Expansion"].copy()

    c2_caps = df_exp1["vadodara_dispatch_cap_mt"]
    cost_crores = df_exp1["total_cost_inr_crores"]
    sp_vals = df_exp1["marginal_saving_right_inr_per_mt"]

    fig, ax1 = plt.subplots(figsize=(10.5, 6.2))

    color1 = "#1b4965"
    ax1.set_xlabel("FSD Chhani (Vadodara) Monthly Dispatch Capacity $C_2$ (Metric Tonnes)", fontsize=11, fontweight="bold", labelpad=8)
    ax1.set_ylabel("Total Monthly System Logistics Cost (INR Crore)", color=color1, fontsize=11, fontweight="bold")
    line1 = ax1.plot(c2_caps, cost_crores, color=color1, marker="o", lw=2.4, markersize=6, label="Total System Cost $Z^*$ (INR Cr)")
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_ylim(5.0, 6.6)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Secondary axis for shadow price
    ax2 = ax1.twinx()
    color2 = "#c1121f"
    ax2.set_ylabel(savings_label, color=color2, fontsize=11, fontweight="bold")
    line2 = ax2.step(c2_caps, sp_vals, where="post", color=color2, lw=2.2, linestyle="-", marker="s", markersize=5, label=savings_label)
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(0, 1200)

    # Baseline reference line at C_2 = 28,000 MT
    ax1.axvline(x=28000, color="#666666", linestyle=":", lw=1.8, label="Baseline Capacity ($C_2 = 28,000$ MT)")
    ax1.annotate(
        "Current Baseline\n($C_2 = 28,000$ MT)\n$Z^* = ₹5.698$ Cr",
        xy=(28000, 5.698),
        xytext=(28000 - 2500, 5.45),
        ha="center",
        va="top",
        fontsize=8.5,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#f0f0f0", edgecolor="#666666", alpha=0.9),
        arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2)
    )

    # Gandhidham stops supplying Surat at 32,000 MT.
    ax1.axvline(x=32000, color="#d90429", linestyle="--", lw=1.2, alpha=0.7)
    ax1.annotate(
        "32,000 MT\nGandhidham stops supplying Surat\nSavings fall from ₹1,023 to ₹707 per MT",
        xy=(32000, 5.2891),
        xytext=(28000, 6.05),
        ha="left",
        va="bottom",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffe6e6", edgecolor="#d90429", alpha=0.9),
        arrowprops=dict(arrowstyle="->", color="#d90429", lw=1.2)
    )

    # Chhani reaches its stock limit at 34,000 MT.
    ax1.axvline(x=34000, color="#0077b6", linestyle="--", lw=1.2, alpha=0.7)
    ax1.annotate(
        "34,000 MT: Chhani reaches its stock limit\nExtra capacity saves nothing beyond this point",
        xy=(34000, 5.1478),
        xytext=(29000, 5.035),
        ha="left",
        va="bottom",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#e0f2fe", edgecolor="#0077b6", alpha=0.9),
        arrowprops=dict(arrowstyle="->", color="#0077b6", lw=1.2)
    )

    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper right", framealpha=0.95)

    plt.title(title, fontsize=11.5, pad=15, fontweight="bold")
    fig.tight_layout()

    output_path = f"outputs/figures/{filename}"
    plt.savefig(output_path)
    plt.close()
    logging.info("Saved %s", output_path)


def main():
    plot_fig1_network_flow_map()
    plot_fig2_depot_utilization()
    plot_fig3_sensitivity_curve()
    plot_fig3_sensitivity_curve(shadow_price=True)
    print("\n" + "="*80)
    print("PHASE 3: ALL 4 FIGURE FILES GENERATED (300 DPI)")
    print("  1. outputs/figures/fig1_network_flow_map.png")
    print("  2. outputs/figures/fig2_depot_utilization.png")
    print("  3. outputs/figures/fig3_sensitivity_curve.png")
    print("  4. outputs/figures/fig3_sensitivity_curve_shadow_price.png")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
