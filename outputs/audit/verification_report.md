# Independent verification report

Audit date: 7 November 2026 (Asia/Kolkata). Local acceptance: **VERIFIED for this illustrative course study**, with the input limitations below. This is not a finding that the proposed operations or investment are valid in practice.

| Check | Result | Evidence |
|---|---|---|
| End-to-end build and reproduction | PASS | `reproduction.log`; dataset replay, table generation, solver, sensitivity, figures and PDF compilation completed |
| Independent discovered tests | PASS: 25/25 | `final_tests.log`, final independent execution after recompilation |
| Solver stress cases | PASS: 30/30 | Deterministic perturbed RHS cases in `tests/test_audit_regressions.py`; 7 feasible objective/feasibility matches and 23 infeasibility matches against HiGHS |
| Report PDF | PASS | pypdf: exactly 8 pages: 7 A4 report/reference pages plus the appended summary slide; expected sections retained, Section 6 exactly three sentences |
| Summary slide | PASS | Exactly 1 standalone page, 16:9 widescreen; appended as report page 8; visually checked for bottom clipping |
| Poster PDF | PASS | pypdf: exactly 1 A3 landscape page, approximately 1190.55 by 841.89 points |
| Layout | PASS | Final report pages and poster rendered with Poppler and visually reviewed; no clipping or overlap; final LaTeX logs have no overfull/underfull boxes, warnings or errors |
| Python static types | NOT RUN | Pyright executable and module are unavailable |
| Python lint | NOT RUN | Ruff executable and module are unavailable |
| Coverage | NOT MEASURED | No coverage percentage is claimed |
| Production or operational acceptance | NOT APPLICABLE | Local academic model; no operational deployment performed |

## Numerical and structural findings

Actual solver execution establishes primal feasibility, signed dual feasibility, complementary slackness and strong duality. Custom two-phase simplex and independent SciPy HiGHS agree on the optimal cost of INR 56,982,720.00. Proper artificial-cost initialization, true Bland leaving-variable selection and artificial-basis cleanup are now exercised by degenerate and infeasible tests. Actual pivot telemetry is 28 Phase I plus 28 Phase II, totaling 56; the original handoff's 54 is superseded.

All 9 active shipment rows and all 7 numeric route columns in both Markdown and LaTeX are compared against the CSV. The CSV objective and every primal constraint are independently recomputed. Authorship, roll numbers, course and institution metadata are checked in both PDFs. Figure resolution is verified from actual 300 DPI metadata.

Independent one-sided finite differences locate the sensitivity regime change at 32,000 MT, not the handoff's 31,000 MT. Marginal savings change from INR 1,022.90/MT to INR 706.55/MT and become zero to the right of 34,000 MT. Expansion from 28,000 to 34,000 MT saves INR 5,504,700/month under the modeled assumptions. Route-rate rounding causes a INR 30 departure from the unrounded affine formula at beta=2.50. Unchanged sampled aggregate route flows do not prove an identical simplex basis or commodity split.

## Routing evidence

`independent_routing_check.log` records an independent hash and raw-array comparison. The original raw response remains unchanged with SHA256 `bdc58e0d7db5524c9a3586cd23dd13b545e7e897324f2c53d882cf501920cdb6`. Its original acquisition timestamp remains unverified and its historical provenance row remains PROVISIONAL.

A separate successful live retrieval has a manifest with HTTP 200, request URL and retrieval timestamp `20261106T202929537569Z` (7 November 2026 in India). Its snapshot SHA256 is `bc5ce0f7c3f330fa8185734752f0b5d325861638e011841bbccfeeb3afb66cc8`, independently matched to the manifest. All 24 raw distances and all 24 raw durations are exactly identical to the baseline, with maximum absolute difference zero. The new source-register entry is VERIFIED/RETRIEVED. Default offline replay preserves the original bytes and reproduces the processed matrices; invalid payloads fail explicitly without fabricated fallbacks.

## Practical limits

Depot coordinates, district proxy points, commodity stocks, demand, dispatch limits and freight coefficients remain ASSUMPTION data. Historical depot names and a reproducible routing response do not validate warehouse gates, current operations, district statutory quotas, operational capacities or tender rates. The OSRM driving profile does not certify truck restrictions or route suitability. Capital costs, attainable expanded throughput and investment payback remain unverified. Numerical and document checks do not resolve those missing operational inputs.

The final follow-up revision additionally checks the user-specified three Section 6 sentences in both TeX and extracted PDF text (normalizing line-end typesetting hyphenation), the four requested plain-language headings, and removal of their obsolete headings. Markdown remains unchanged outside the user-requested TeX/PDF scope. The standalone and appended summary slides were rendered and visually reviewed; their tables, recommendation, input note and footer are fully visible without bottom clipping.

Final rendered QA images are retained in `qa_render/`. Full terminal logs, rather than summary assertions alone, are retained in this audit directory.
