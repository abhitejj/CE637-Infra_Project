# Project and audit guide

## Scope and acceptance

The handoff requests independent data, mathematical, numerical and PDF audits. Its claimed benchmarks are assertions to verify. The accepted scope includes correcting code and deliverables where evidence contradicts those assertions. It does not authorize inventing operational records, replacing stored routing evidence or claiming an investment is viable.

The final deliverables are a seven-page report (Sections 1–6 and references) and a one-page A3 landscape poster. Section 6 must have exactly three sentences. Authors are Abhitej Singh Bhullar (23110009) and Radhika Purohit (24110280), CE 637, IIT Gandhinagar.

## Reproduction environment

From the project root, use `.venv/bin/python`. Install `requirements.txt` in a new environment if needed. PDF verification additionally needs `pypdf`; compilation needs `pdflatex` (on this host `/Library/TeX/texbin/pdflatex`). Run `.venv/bin/python scripts/reproduce.py` for the complete single-command workflow and combined terminal log.

The manual sequence is:

```sh
.venv/bin/python scripts/01_build_dataset.py
.venv/bin/python scripts/02_generate_input_tables.py
.venv/bin/python scripts/03_solve_optimization.py
.venv/bin/python scripts/04_sensitivity_analysis.py
.venv/bin/python scripts/05_generate_figures.py
```

Then compile both LaTeX files from `report/` and run `.venv/bin/python -m unittest discover -s tests -v` from the root. Preserve full terminal logs; no local checks establish operational validity of assumed inputs.

## Correct interpretation

All scenario coordinates, stock, dispatch capacities, demands and cost coefficients are assumptions. The source register separates data category (`OFFICIAL`, `RETRIEVED`, `CALCULATED`, `ASSUMPTION`) from verification status (`VERIFIED`, `PROVISIONAL`, `ASSUMED`). Historical facility names do not certify coordinates or current capacity. District destinations are proxy points, not confirmed warehouse gates. The study omits many facilities, including any Surat supply node; it does not establish that Surat has no storage.

Total assumed demand is 90,000 MT wheat and 42,000 MT rice, against 112,000 MT and 55,000 MT stock and 141,000 MT dispatch capacity. Aggregate totals are necessary feasibility conditions, not a proof for every coupled commodity instance; the solver establishes baseline feasibility.

The custom solver uses proper Phase I artificial costs and Bland’s smallest-variable-index entering/leaving rule, cleans artificial basic variables before Phase II, and rejects infeasible cases. Its initial constraint matrix is 24×84; the full tableau is 25×85 including objective and RHS. Actual pivot telemetry is 28+28=56. Independent HiGHS agreement concerns feasibility and cost; alternative optima prevent requiring identical commodity vectors.

The Chhani breakpoint is 32,000 MT. Between 32,000 and 34,000 MT, Chhani replaces Sabarmati’s Surat flow and Sabarmati supplies Banaskantha instead of Gandhidham: 743.55−487.20+900.70−450.50=706.55 INR/MT. At 34,000 MT, capacity still binds but the right derivative is zero; beyond it, inventory binds and the cap has slack. Conditional savings from 28,000 to 34,000 MT are ₹5,504,700/month or ₹66,056,400/year; no capex or payback is established.

Unrounded budget scaling is Z(β)=13,200,000+17,513,100β INR. At β=2.50 it predicts ₹56,982,750; two-decimal route rates give ₹56,982,720 (₹30 lower). Stable aggregate routes do not prove an identical simplex basis. A coefficient shock is not a measured fuel-price response.

## Audit evidence

`outputs/audit/data_provenance_audit.md` records source URLs and access outcomes. Stored raw SHA256 at audit start: `bdc58e0d7db5524c9a3586cd23dd13b545e7e897324f2c53d882cf501920cdb6`. This establishes present integrity, not historical acquisition. Full test and reproduction logs are retained under `outputs/audit/`.


## Live routing cross-check completed

A fresh HTTPS OSRM Table request succeeded during this audit. The separate response `data/raw/osrm_response_20261106T202929537569Z_bc5ce0f7c3f3.json` has a timestamp/hash/query manifest; all 24 distance and duration values exactly match the preserved baseline. See `outputs/audit/live_routing_comparison.txt` and `live_routing_check.log`. The original baseline hash remains unchanged. This verifies the routing output today, while the original acquisition timestamp and real facility identities remain unverified.
