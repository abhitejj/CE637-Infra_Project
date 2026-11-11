# Optimisation of Food Grain Distribution in Gujarat: Moving Wheat and Rice from FCI Depots to District Warehouses

**CE 637 Infrastructure Systems: Planning and Management — Course Project**  
*Indian Institute of Technology Gandhinagar*  
*Authors:* **Abhitej Singh Bhullar** (Roll No. 23110009) & **Radhika Purohit** (Roll No. 24110280)  

---

## Poster 

[![Optimisation of Food Grain Distribution in Gujarat — Course Project Poster](outputs/figures/poster_preview.png)](report/Poster.pdf)

> 📄 **[Download / View Full-Resolution Vector PDF (`report/Poster.pdf`)](report/Poster.pdf)**  
> 📑 **[Download / View Full Seven-Page Final Technical Report (`report/Final_Report.pdf`)](report/Final_Report.pdf)**

---

## 1. Executive Summary

Every month, the General Manager (Logistics & Movement) at the **Food Corporation of India (FCI) Gujarat Regional Office**, in coordination with the Managing Director of the **Gujarat State Civil Supplies Corporation Limited (GSCSCL)**, must determine how food grains move from bulk railhead storage depots to district warehouses to fulfill statutory public distribution entitlements under the National Food Security Act (NFSA, 2013).

This study formulates and solves a multi-commodity linear programming (LP) network model to minimize the statewide freight and terminal handling expenditure across Gujarat's highway corridors. The model coordinates the monthly distribution of **132,000 metric tonnes (MT)** of grain (**90,000 MT of Wheat** and **42,000 MT of Rice**) from **4 FCI railhead supply depots** to **6 GSCSCL district warehouses** across 24 candidate highway corridors.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           GUJARAT PUBLIC FOOD GRAIN DISTRIBUTION NETWORK                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
         [FCI DIVISIONAL SUPPLY DEPOTS]                      [GSCSCL DISTRICT WAREHOUSES]
    ┌──────────────────────────────────────┐            ┌──────────────────────────────────────┐
    │ D1: FSD Sabarmati (Ahmedabad)        │───────────>│ W1: Central Godown (Aslali / Sarkhej)│
    │     Stock: 35k W | 18k R | Cap: 45k  │───┐    ┌──>│     Demand: 24k W | 10k R (34k MT)   │
    ├──────────────────────────────────────┤   │    │   ├──────────────────────────────────────┤
    │ D2: FSD Chhani (Vadodara)            │───┼────┼──>│ W2: District Godown (Sachin / Udhna) │
    │     Stock: 22k W | 12k R | Cap: 28k  │───┼────┤   │     Demand: 22k W | 12k R (34k MT)   │
    ├──────────────────────────────────────┤   │    │   ├──────────────────────────────────────┤
    │ D3: FSD Ghanteshwar (Rajkot)         │───┼────┼──>│ W3: District Godown (Makarpura GIDC) │
    │     Stock: 25k W | 10k R | Cap: 30k  │───┼────┤   │     Demand: 14k W |  7k R (21k MT)   │
    ├──────────────────────────────────────┤   │    │   ├──────────────────────────────────────┤
    │ D4: FSD Gandhidham (Kutch)           │───┼────┼──>│ W4: District Godown (Aji GIDC)       │
    │     Stock: 30k W | 15k R | Cap: 38k  │───┘    │   │     Demand: 13k W |  5k R (18k MT)   │
    └──────────────────────────────────────┘        │   ├──────────────────────────────────────┤
             Shared Truck Loading Bays              ├──>│ W5: District Godown (Palanpur Highway)│
             & Throughput Handling Caps             │   │     Demand: 11k W |  5k R (16k MT)   │
             Force Wheat-Rice Competition           │   ├──────────────────────────────────────┤
                                                    └──>│ W6: District Godown (Bhuj Mandi)     │
                                                        │     Demand:  6k W |  3k R ( 9k MT)   │
                                                        └──────────────────────────────────────┘
```

### Key Verified Results:
* **Minimum Monthly Logistics Expenditure**: **₹56,982,720.00** (**₹5.70 Crore** / month).
* **Average Unit Delivery Cost**: **₹431.69 / MT** (₹43.17 per quintal).
* **Total Transportation Work**: **17,513,100 Tonne-Kilometers** (Average lead distance: **132.7 km**).
* **Algorithmic Convergence**: Custom Two-Phase Simplex converges in exactly **56 pivots** (28 Phase I + 28 Phase II), matching SciPy HiGHS (`highs-ds`) to machine precision ($0.000000$ INR error).
* **Core Operational Bottleneck**: Surat needs 34,000 MT but has no local supply depot in this model. Nearest depot Chhani can only send 7,000 MT before hitting its 28,000 MT monthly loading limit; Surat must therefore draw grain from all 4 depots, including a 564 km haul from Gandhidham.
* **Targeted Infrastructure Expansion**: Expanding Chhani's loading capacity from 28,000 MT to 34,000 MT (+6,000 MT) saves **₹55,04,700 / month** (₹6.61 Crore annually).

---

## 2. System Topology & Operational Characteristics

### Table 1: Supply Depots and Demand Sinks Directory
| Node ID | Facility Name | District | Role | Latitude | Longitude | Wheat (MT) | Rice (MT) | Monthly Capacity / Demand |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1** | FSD Sabarmati (Ahmedabad) | Ahmedabad | Supply Origin | 23.0760°N | 72.5800°E | 35,000 | 18,000 | **45,000 MT** (Dispatch Cap $C_1$) |
| **D2** | FSD Chhani (Vadodara) | Vadodara | Supply Origin | 22.3580°N | 73.1650°E | 22,000 | 12,000 | **28,000 MT** (Dispatch Cap $C_2$) |
| **D3** | FSD Ghanteshwar (Rajkot) | Rajkot | Supply Origin | 22.3450°N | 70.7550°E | 25,000 | 10,000 | **30,000 MT** (Dispatch Cap $C_3$) |
| **D4** | FSD Gandhidham (Kutch) | Kutch | Supply Origin | 23.0753°N | 70.1337°E | 30,000 | 15,000 | **38,000 MT** (Dispatch Cap $C_4$) |
| **W1** | Ahmedabad Central Godown (Aslali) | Ahmedabad | Demand Sink | 23.0225°N | 72.5714°E | 24,000 | 10,000 | **34,000 MT** (Total Demand $D_1$) |
| **W2** | Surat District Godown (Sachin) | Surat | Demand Sink | 21.1702°N | 72.8311°E | 22,000 | 12,000 | **34,000 MT** (Total Demand $D_2$) |
| **W3** | Vadodara District Godown (Makarpura) | Vadodara | Demand Sink | 22.3072°N | 73.1812°E | 14,000 | 7,000 | **21,000 MT** (Total Demand $D_3$) |
| **W4** | Rajkot District Godown (Aji GIDC) | Rajkot | Demand Sink | 22.3039°N | 70.8022°E | 13,000 | 5,000 | **18,000 MT** (Total Demand $D_4$) |
| **W5** | Banaskantha Godown (Palanpur) | Banaskantha | Demand Sink | 24.1724°N | 72.4346°E | 11,000 | 5,000 | **16,000 MT** (Total Demand $D_5$) |
| **W6** | Kutch District Godown (Bhuj) | Kutch | Demand Sink | 23.2420°N | 69.6669°E | 6,000 | 3,000 | **9,000 MT** (Total Demand $D_6$) |
| **Total**| | | | | | **112,000** (Supply)<br>**90,000** (Demand) | **55,000** (Supply)<br>**42,000** (Demand) | **141,000 MT** (Total Cap)<br>**132,000 MT** (Total Demand) |

### The Shared Handling Bottleneck
In real-world grain logistics, static storage capacity differs fundamentally from monthly throughput capacity. While depots hold combined stock of 167,000 MT, physical loading bays, 60 MT weighbridges, and rail siding cycle limits cap monthly aggregate dispatch ($C_i$) at **141,000 MT**. 

Crucially, **$C_i < S_{i1} + S_{i2}$ across every depot** (e.g., FSD Chhani holds 34,000 MT physical stock but can dispatch at most 28,000 MT). This shared limit tightly couples wheat and rice into direct operational competition for truck loading slots.

---

## 3. Mathematical Optimization Formulation

### Decision Variables
* $x_{ijk} \ge 0$: Metric tonnes (MT) of commodity $k \in \{1: \text{Wheat}, 2: \text{Rice}\}$ transported from depot $i \in \{1..4\}$ to district warehouse $j \in \{1..6\}$.  
  Total: $4 \times 6 \times 2 = \mathbf{48 \text{ continuous decision variables}}$.

### Objective Function
Minimize statewide monthly haulage and terminal handling expenditure:
$$\min Z = \sum_{i=1}^4 \sum_{j=1}^6 \sum_{k=1}^2 c_{ij} x_{ijk} = \sum_{i=1}^4 \sum_{j=1}^6 c_{ij} (x_{ij1} + x_{ij2})$$
where unit shipping cost $c_{ij} = \alpha + \beta \cdot d_{ij} = 100.00 + 2.50 \cdot d_{ij}$ [₹/MT] combines terminal handling ($\alpha = \text{₹}100/\text{MT}$) and line-haul haulage ($\beta = \text{₹}2.50/\text{MT-km}$).

### Table 2: OSRM Highway Driving Distances ($d_{ij}$ in km) & Unit Freight Rates ($c_{ij}$ in ₹/MT)
| Origin Depot | W1 (Ahmedabad) | W2 (Surat) | W3 (Vadodara) | W4 (Rajkot) | W5 (Banaskantha) | W6 (Kutch/Bhuj) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1: Sabarmati** | 6.7 km (₹116.85) | 257.4 km (₹743.55) | 122.3 km (₹405.75) | 220.3 km (₹650.83) | 140.2 km (₹450.50) | 356.9 km (₹992.32) |
| **D2: Chhani** | 102.6 km (₹356.42) | 154.9 km (₹487.20) | 7.5 km (₹118.80) | 274.8 km (₹786.88) | 253.3 km (₹733.35) | 450.5 km (₹1226.25) |
| **D3: Ghanteshwar**| 222.4 km (₹656.12) | 429.8 km (₹1174.48)| 290.0 km (₹825.08) | 8.5 km (₹121.32) | 326.6 km (₹916.58) | 239.2 km (₹698.10) |
| **D4: Gandhidham** | 356.7 km (₹991.75) | 564.0 km (₹1510.10)| 424.3 km (₹1160.68)| 199.9 km (₹599.65) | 320.3 km (₹900.70) | 57.6 km (₹244.05) |

### Operational Constraints (24 Linear Inequalities)
1. **Depot Commodity Available Stock Limits (8 constraints, $\le$)**:
   $$\sum_{j=1}^6 x_{ijk} \le S_{ik} \quad \forall i \in \{1..4\}, \; \forall k \in \{1, 2\}$$
2. **District Commodity Demand Requirements (12 constraints, $\ge$)**:
   $$\sum_{i=1}^4 x_{ijk} \ge D_{jk} \quad \forall j \in \{1..6\}, \; \forall k \in \{1, 2\}$$
3. **Depot Monthly Dispatch & Handling Capacity Coupling (4 constraints, $\le$)**:
   $$\sum_{k=1}^2 \sum_{j=1}^6 x_{ijk} \le C_i \quad \forall i \in \{1..4\}$$
4. **Non-Negativity Restrictions (48 restrictions)**:
   $$x_{ijk} \ge 0 \quad \forall i, j, k$$

---

## 4. Method: Custom Two-Phase Simplex Solver

### Standard Canonical Tableau Conversion
Because all 12 demand constraints are $\ge$, the origin $x=0$ is strictly infeasible. The system is converted into canonical standard equality form $A x_{\text{all}} = b, x_{\text{all}} \ge 0$:
* **8 Slacks ($s_1..s_8 \ge 0$)** for physical supply limits.
* **4 Slacks ($s_9..s_{12} \ge 0$)** for depot dispatch capacities.
* **12 Surpluses ($e_1..e_{12} \ge 0$)** for district demand requirements.
* **12 Artificials ($a_1..a_{12} \ge 0$)** to form an initial identity basis for Phase I.

$$\text{Total Columns} = 48 \text{ (Primal)} + 12 \text{ (Slacks)} + 12 \text{ (Surplus)} + 12 \text{ (Artificial)} = \mathbf{84 \text{ variables across 24 equality rows}}$$

### Solver Telemetry & Verification
* **Phase I**: Minimized artificial sum $W = \sum a_m$, driving infeasibility from $132,000 \to 0.000000$ in **28 pivots** using Bland's anti-cycling rule.
* **Phase II**: Dropped artificial variables and optimized the economic objective $Z$ in **28 pivots**.
* **Total Simplex Work**: Exactly **56 pivots**.
* **Cross-Solver Audit**: Benchmarked against SciPy HiGHS (`method='highs-ds'`). Both solvers converge to **₹56,982,720.00** with **0.000000 INR error**.

---

## 5. The Optimal Distribution Plan

The optimal solution activates **9 highway corridors** out of 24 candidate routes.

### Table 3: Optimal Monthly Commodity Shipments
| Origin Supply Depot | Destination Warehouse | Distance | Wheat (MT) | Rice (MT) | Total Flow (MT) | Unit Freight | Total Monthly Cost | Tonne-km |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1: Sabarmati** | W1: Ahmedabad | 6.7 km | 24,000 | 10,000 | **34,000** | ₹116.85 | ₹39,72,900.00 | 229,160 |
| **D1: Sabarmati** | W2: Surat | 257.4 km | 3,000 | 8,000 | **11,000** | ₹743.55 | ₹81,79,050.00 | 2,831,620 |
| **D2: Chhani** | W2: Surat | 154.9 km | 7,000 | 0 | **7,000** | ₹487.20 | ₹34,10,400.00 | 1,084,160 |
| **D2: Chhani** | W3: Vadodara | 7.5 km | 14,000 | 7,000 | **21,000** | ₹118.80 | ₹24,94,800.00 | 157,920 |
| **D3: Ghanteshwar** | W2: Surat | 429.8 km | 12,000 | 0 | **12,000** | ₹1,174.48 | ₹1,40,93,760.00 | 5,157,480 |
| **D3: Ghanteshwar** | W4: Rajkot | 8.5 km | 13,000 | 5,000 | **18,000** | ₹121.32 | ₹21,83,760.00 | 153,540 |
| **D4: Gandhidham** | W2: Surat | 564.0 km | 0 | 4,000 | **4,000** | ₹1,510.10 | ₹60,40,400.00 | 2,256,160 |
| **D4: Gandhidham** | W5: Banaskantha | 320.3 km | 11,000 | 5,000 | **16,000** | ₹900.70 | ₹1,44,11,200.00 | 5,124,480 |
| **D4: Gandhidham** | W6: Kutch (Bhuj) | 57.6 km | 6,000 | 3,000 | **9,000** | ₹244.05 | ₹21,96,450.00 | 518,580 |
| **Statewide Total** | | | **90,000** | **42,000** | **132,000** | | **₹5,69,82,720.00** | **17,513,100** |

### Network Visualizations

<p align="center">
  <img src="outputs/figures/fig1_network_flow_map.png" alt="Optimal Network Flow Map" width="75%"/>
  <br><em>Figure 1: Optimal multi-commodity network flow map across Gujarat FCI railheads and GSCSCL district warehouses. Line widths indicate monthly flow volume.</em>
</p>

<p align="center">
  <img src="outputs/figures/fig2_depot_utilization.png" alt="Depot Capacity Utilization" width="75%"/>
  <br><em>Figure 2: Physical inventory stock vs. dispatched flow vs. maximum monthly dispatch capacity ($C_i$).</em>
</p>

### Operational Bottleneck Analysis: The Surat Deficit Split
1. **Local Proximity Dominance**: In Ahmedabad (W1), Vadodara (W3), Rajkot (W4), and Kutch (W6), 100% of demand is fulfilled by the immediately adjacent depot at low unit cost (₹116.85 to ₹244.05 / MT).
2. **The Surat Deficit Crisis**: Surat needs 34,000 MT but has no supply depot in this model. The nearest depot, FSD Chhani ($d=154.9\text{ km}$), has a dispatch cap of 28,000 MT, of which 21,000 MT must serve local Vadodara demand. Chhani can only supply **7,000 MT** to Surat before hitting 100% capacity utilization.
3. **Four-Way Sourcing Split**: To cover Surat's remaining 27,000 MT deficit, the optimizer exhausts surplus dispatch capacity across the entire state:
   - **11,000 MT** from Sabarmati ($d=257.4\text{ km}$, exhausting D1's 45,000 MT cap).
   - **12,000 MT** from Ghanteshwar ($d=429.8\text{ km}$, exhausting D3's 30,000 MT cap).
   - **4,000 MT** long-hauled 564.0 km from Gandhidham at a steep ₹1,510.10 / MT.

---

## 6. Sensitivity Analysis: Bottleneck Capacity Expansion

### Parametric Variation of FSD Chhani Capacity ($C_2$)
To evaluate infrastructure debottlenecking, the dispatch capacity at FSD Chhani ($C_2$) was varied from 21,000 MT to 35,000 MT in increments of 1,000 MT.

<p align="center">
  <img src="outputs/figures/fig3_sensitivity_curve.png" alt="Sensitivity Curve" width="75%"/>
  <br><em>Figure 3: System cost reduction and marginal shadow price across Chhani dispatch capacity ($C_2$).</em>
</p>

### Table 4: Sensitivity Results for FSD Chhani Expansion
| Chhani Capacity $C_2$ (MT) | System Cost (₹ Cr) | Shadow Price $y_2^*$ (₹/MT) | Chhani $\to$ Surat | Sabarmati $\to$ Surat | Gandhidham $\to$ Surat | Monthly Savings vs Baseline |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 21,000 | ₹6.4143 Cr | ₹1,022.90 | 0 MT | 11,000 MT | 11,000 MT | -₹71,60,300.00 |
| 24,000 | ₹6.1074 Cr | ₹1,022.90 | 3,000 MT | 11,000 MT | 8,000 MT | -₹40,91,600.00 |
| **28,000 (Base)** | **₹5.6983 Cr** | **₹1,022.90** | **7,000 MT** | **11,000 MT** | **4,000 MT** | **₹0.00** |
| 30,000 | ₹5.4937 Cr | ₹1,022.90 | 9,000 MT | 11,000 MT | 2,000 MT | +₹20,45,800.00 |
| 31,000 | ₹5.3914 Cr | ₹1,022.90 | 10,000 MT | 11,000 MT | 1,000 MT | +₹30,68,700.00 |
| 32,000 | ₹5.2891 Cr | ₹706.55 | 11,000 MT | 11,000 MT | 0 MT | +₹40,91,600.00 |
| **34,000 (Break)**| **₹5.1478 Cr** | **₹706.55** | **13,000 MT** | **9,000 MT** | **0 MT** | **+₹55,04,700.00** |
| 35,000 | ₹5.1478 Cr | ₹0.00 | 13,000 MT | 9,000 MT | 0 MT | +₹55,04,700.00 |

### Economic Interpretation of Shadow Prices
1. **Regime 1 ($21,000 \le C_2 \le 32,000\text{ MT}$)**: The marginal shadow price is constant at **₹1,022.90 / MT**. Every additional 1 MT of truck loading capacity at Chhani allows 1 MT of grain to move Chhani $\to$ Surat (₹487.20/MT) instead of Gandhidham $\to$ Surat (₹1,510.10/MT), saving exactly $c_{42} - c_{22} = ₹1,510.10 - ₹487.20 = \mathbf{₹1,022.90 / \text{MT}}$. Over 4,000 MT (from 28k to 32k MT), cumulative savings are **₹40,91,600 / month**.
2. **Regime 2 ($32,000 < C_2 \le 34,000\text{ MT}$)**: At 32,000 MT, Gandhidham's flow to Surat is eliminated. Additional Chhani dispatches to Surat allow Sabarmati to reassign flow to Banaskantha, displacing Gandhidham's long haul to Palanpur. The combined marginal saving is $c_{12} - c_{22} + c_{45} - c_{15} = 743.55 - 487.20 + 900.70 - 450.50 = \mathbf{₹706.55 / \text{MT}}$. Over 2,000 MT (from 32k to 34k MT), this saves an additional **₹14,13,100 / month**.
3. **Inventory Saturation ($C_2 \ge 34,000\text{ MT}$)**: At 34,000 MT, total throughput equals Chhani's entire physical inventory (22k wheat + 12k rice = 34k MT). Beyond 34,000 MT, the warehouse is stock-constrained, capacity slack develops, and the shadow price drops to **₹0.00 / MT**.
4. **Actionable Policy Takeaway**: Expanding FSD Chhani dispatch capacity from 28,000 MT to 34,000 MT (+6,000 MT) yields conditional savings of **₹55.05 Lakh / month (₹6.61 Crore / year)**.

---

## 7. What the Model Cannot Say (Operational Scope Boundaries)

As documented in Section 6 of the Final Report, three strict structural boundaries delimit this optimization model:

1. **Continuous Flow vs. Discrete Batching**: The linear programming model treats freight flows as continuous fluid variables and assumes independent point-to-point delivery, thereby failing to capture discrete truckload batching (20–25 MT minimum consignments), carrier vehicle schedule synchronization, or backhaul empty-trip repositioning economics.
2. **Spatial Aggregation vs. Last-Mile Logistics**: By aggregating demand at district central warehouses, the formulation cannot optimize downstream secondary transport routing or temporal inventory stocking across taluka godowns and Fair Price Shops that execute last-mile distribution to rural households.
3. **Single-Period Determinism vs. Seasonal Risk**: The single-period deterministic formulation abstracts away intra-annual procurement seasonality, monsoon corridor washouts, and multi-month grain shelf-life degradation, preventing it from evaluating strategic inter-seasonal buffer carryover or silo moisture spoilage risks.

---

## 8. Data Governance & Provenance Classification

All data fields used in this study are classified into four strict audit classes in `data/source_register.csv`:
* `OFFICIAL`: Verified from published government records (FCI, DFPD, NFSA portal, Gujarat FCS&CA). Historical records support selected facility names.
* `RETRIEVED`: Sourced from external open APIs/registries (OpenStreetMap / OSRM highway routing graphs with exact query endpoints documented).
* `CALCULATED`: Directly computed via deterministic mathematical operations (hauling distances, costs, pivot counts, shadow prices).
* `ASSUMPTION`: Operational assumptions explicitly identified for this scenario (facility coordinates, monthly stocks, dispatch caps, district quotas, and freight rate coefficients $\alpha = \text{₹}100/\text{MT}$, $\beta = \text{₹}2.50/\text{MT-km}$). This is an illustrative optimization study, not an official Gujarat government operational plan.

Full provenance audit logs and live OSRM routing cross-check evidence are documented in `outputs/audit/data_provenance_audit.md`.

---

## 9. Deliverables Directory

| File Path | Description |
| :--- | :--- |
| [`report/Poster.pdf`](report/Poster.pdf) | One-page A3 landscape executive poster deliverable (source: `report/Poster.tex`). |
| [`report/Final_Report.pdf`](report/Final_Report.pdf) | Seven-page A4 comprehensive technical report (source: `report/Final_Report.tex` & `Final_Report.md`). |
| [`report/Summary_Slide.pdf`](report/Summary_Slide.pdf) | One-page executive summary slide (source: `report/Summary_Slide.tex`). |
| [`outputs/figures/`](outputs/figures/) | 300-DPI high-resolution publication figures (`fig1`, `fig2`, `fig3`, `poster_preview.png`). |
| [`outputs/tables/`](outputs/tables/) | Machine-readable CSV tables (`optimal_shipments_wheat_rice.csv`, `shadow_prices_and_slacks.csv`, `sensitivity_results.csv`, `solver_diagnostics.json`). |
| [`outputs/audit/`](outputs/audit/) | Comprehensive verification reports, test execution logs, and provenance registers. |
| [`scripts/`](scripts/) | Modular Python pipelines (`01_build_dataset.py` through `05_generate_figures.py`). |
| [`tests/`](tests/) | Independent QA test suites covering dataset integrity, simplex convergence, HiGHS benchmarking, and deliverable compliance. |

---

## 10. Reproducibility

Every numerical result, figure, table, and document in this repository is 100% reproducible via a single command:

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run complete end-to-end reproduction pipeline
python scripts/reproduce.py
```

This automated pipeline:
1. Rebuilds processed datasets from preserved raw evidence (`scripts/01_build_dataset.py`).
2. Generates Markdown and LaTeX input tables (`scripts/02_generate_input_tables.py`).
3. Solves the optimization problem using the custom Two-Phase Simplex and validates against HiGHS (`scripts/03_solve_optimization.py`).
4. Executes parametric sensitivity analysis across Chhani capacity and freight rates (`scripts/04_sensitivity_analysis.py`).
5. Renders 300-DPI publication figures (`scripts/05_generate_figures.py`).
6. Compiles LaTeX deliverables (`Summary_Slide.pdf`, `Final_Report.pdf`, `Poster.pdf`).
7. Runs the complete test suite with 25 independent QA checks.
