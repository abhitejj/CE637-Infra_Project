# Model specification (corrected during independent audit)

This document records the formulation used in the final report. Earlier preliminary numerical expectations were superseded by executed computations.

There are four selected supply nodes, six district demand proxy points, and two commodities. Let x[i,j,k] >= 0 be monthly tonnes. Minimize sum c[i,j] x[i,j,k], where c[i,j] is NumPy-rounded to two decimals from 100+2.50*d[i,j]. Costs are in INR/MT; both coefficients are assumptions.

Constraints are sum_j x[i,j,k] <= S[i,k] (8 stock inequalities), sum_i x[i,j,k] >= D[j,k] (12 demand inequalities), and sum_jk x[i,j,k] <= C[i] (4 shared dispatch inequalities). Positive costs and upper bounds make excess delivery suboptimal, so demands bind at an optimum. Removing dispatch coupling separates the two commodity problems.

Standard form adds 12 slacks, 12 demand surpluses and 12 artificial variables: 84 columns and 24 constraint rows; with objective/RHS, the initial tableau is25×85. Phase I minimizes the artificial sum and Phase II minimizes shipping costs after artificial cleanup. True Bland’s rule uses the lowest entering variable index and lowest basic-variable index among tied leaving candidates. Numerical tolerance is1e-9.

The baseline cost is₹56,982,720 with28+28=56 pivots, independently matched by HiGHS. Exported commodity allocations are HiGHS-selected and may differ from custom simplex due to alternative optima. Signed duals and primal residuals are recorded in diagnostics/tables. See the final report and sensitivity CSV for the32,000MT route breakpoint and34,000MT inventory boundary. No capex/payback inference is supported.

All coordinates, stocks, demands, dispatch limits and cost parameters are assumptions; historical depot names and stored OSRM evidence have narrower provenance. Read data/source_register.csv and outputs/audit/data_provenance_audit.md before treating any output as operational advice.
