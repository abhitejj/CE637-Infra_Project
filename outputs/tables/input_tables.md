# Input Data Tables: Gujarat Food Grain Distribution Optimization
All stocks, capacities, district demands, and node coordinates are assumptions; OSRM distances are retrieved at proxy coordinates and costs are calculated from assumed rates.

## Table 1: Supply Depot Stock & Dispatch Handling Capacities
| Depot ID   | Depot Name                | District   |   Wheat Stock (MT) |   Rice Stock (MT) |   Total Stock (MT) |   Dispatch Cap C_i (MT) | Stock / Cap Ratio   | Coupling Status                        |
|:-----------|:--------------------------|:-----------|-------------------:|------------------:|-------------------:|------------------------:|:--------------------|:---------------------------------------|
| D1         | FSD Sabarmati (Ahmedabad) | Ahmedabad  |             35,000 |            18,000 |             53,000 |                  45,000 | 1.18x               | Assumed cap ( 8,000 MT below stock)    |
| D2         | FSD Chhani (Vadodara)     | Vadodara   |             22,000 |            12,000 |             34,000 |                  28,000 | 1.21x               | Assumed cap ( 6,000 MT below stock)    |
| D3         | FSD Ghanteshwar (Rajkot)  | Rajkot     |             25,000 |            10,000 |             35,000 |                  30,000 | 1.17x               | Assumed cap ( 5,000 MT below stock)    |
| D4         | FSD Gandhidham (Kutch)    | Kutch      |             30,000 |            15,000 |             45,000 |                  38,000 | 1.18x               | Assumed cap ( 7,000 MT below stock)    |
| TOTAL      | Scenario Total            | Gujarat    |            112,000 |            55,000 |            167,000 |                 141,000 | 1.18x               | System Cap Margin: +9,000 MT vs Demand |

*Key Operational Takeaway*: For every depot, the monthly dispatch throughput limit $C_i$ is strictly tighter than the total physical inventory ($S_{i,\text{Wheat}} + S_{i,\text{Rice}}$), with stock-to-capacity ratios ranging from $1.17\times$ to $1.21\times$. These assumed shared capacities couple wheat and rice; whether a constraint binds must be established by the solved allocation (D4 is slack at baseline).

## Table 2: Assumed District Monthly Food Grain Demand
| Warehouse ID   | District Warehouse                        | Facility / Godown Hub         |   Wheat Demand (MT) |   Rice Demand (MT) |   Total Demand (MT) | Share of Demand (%)   |
|:---------------|:------------------------------------------|:------------------------------|--------------------:|-------------------:|--------------------:|:----------------------|
| W1             | Ahmedabad District Warehouse              | Assumed district demand proxy |              24,000 |             10,000 |              34,000 | 25.76%                |
| W2             | Surat District Warehouse                  | Assumed district demand proxy |              22,000 |             12,000 |              34,000 | 25.76%                |
| W3             | Vadodara District Warehouse               | Assumed district demand proxy |              14,000 |              7,000 |              21,000 | 15.91%                |
| W4             | Rajkot District Warehouse                 | Assumed district demand proxy |              13,000 |              5,000 |              18,000 | 13.64%                |
| W5             | Banaskantha District Warehouse (Palanpur) | Assumed district demand proxy |              11,000 |              5,000 |              16,000 | 12.12%                |
| W6             | Kutch District Warehouse (Bhuj)           | Assumed district demand proxy |               6,000 |              3,000 |               9,000 | 6.82%                 |
| TOTAL          | 6 Target Districts                        | State Civil Supplies Grid     |              90,000 |             42,000 |             132,000 | 100.00%               |

*Demand Distribution*: Urban industrial corridors (Ahmedabad and Surat) account for $51.52\%$ of scenario food grain demand ($68,000\text{ MT/month}$), while Saurashtra and agrarian corridors make up the remaining $48.48\%$.

## Table 3: Combined OSRM Driving-Profile Distance & Unit Transport Cost Matrix
*Format: Road Distance in km (Unit Logistics Cost in INR/MT)*, where costs are rounded to paise: $c_{ij} = \mathrm{round}(100.00 + 2.50 \times d_{ij}, 2)$.

|                          | W1: Ahmedabad      | W2: Surat           | W3: Vadodara        | W4: Rajkot         | W5: Banaskantha    | W6: Kutch (Bhuj)    |
|:-------------------------|:-------------------|:--------------------|:--------------------|:-------------------|:-------------------|:--------------------|
| D1: Sabarmati (Ahmd)     | 6.7 km (₹116.85)   | 257.4 km (₹743.55)  | 122.3 km (₹405.75)  | 220.3 km (₹650.83) | 140.2 km (₹450.50) | 356.9 km (₹992.32)  |
| D2: Chhani (Vadodara)    | 102.6 km (₹356.42) | 154.9 km (₹487.20)  | 7.5 km (₹118.80)    | 274.8 km (₹786.88) | 253.3 km (₹733.35) | 450.5 km (₹1226.25) |
| D3: Ghanteshwar (Rajkot) | 222.4 km (₹656.12) | 429.8 km (₹1174.48) | 290.0 km (₹825.08)  | 8.5 km (₹121.32)   | 326.6 km (₹916.58) | 239.2 km (₹698.10)  |
| D4: Gandhidham (Kutch)   | 356.7 km (₹991.75) | 564.0 km (₹1510.10) | 424.3 km (₹1160.68) | 199.9 km (₹599.65) | 320.3 km (₹900.70) | 57.6 km (₹244.05)   |

*Network Structure*: Highlighted entries reflect local proximity corridors (e.g. D1 $\to$ W1 at 6.7 km, ₹116.85/MT; D2 $\to$ W3 at 7.5 km, ₹118.80/MT; D3 $\to$ W4 at 8.5 km, ₹121.32/MT; D4 $\to$ W6 at 57.6 km, ₹244.05/MT).
