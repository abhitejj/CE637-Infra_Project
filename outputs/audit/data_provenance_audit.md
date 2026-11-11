# Independent data provenance audit

Audit date and external-source access date: **2026-11-07** (Asia/Kolkata).

Scope: read-only review of the original handoff, pipeline, input files, source register, report, poster and supporting documentation. This evidence file is the only file authored by the Research & Data Auditor. Findings below describe the original baseline; implementation and final QA are separate responsibilities.

## Overall finding

The stored routing data support an illustrative optimization scenario. They do not establish a verified operational plan for Gujarat. Depot names have partial official support, but the exact facility coordinates, warehouse identities, stocks, dispatch limits, district allocations, handling rate and distance rate lack supporting granular records. Classify these numerical scenario inputs as `ASSUMPTION`, routing output as `RETRIEVED`, and transformations as `CALCULATED`. An official portal homepage does not establish provenance for every field attributed to that institution.

## Preserved routing evidence and historical limitations

The file `data/raw/osrm_response.json` was inspected without mutation. SHA-256 measured during this audit:

`bdc58e0d7db5524c9a3586cd23dd13b545e7e897324f2c53d882cf501920cdb6`

It contains `code: "Ok"`, 4 sources, 6 destinations, and 4-by-6 distance and duration arrays, with OSRM-like waypoint locations, hints, names and snap distances. Example distances in metres are D1-W1 = 6742.8, D2-W3 = 7521.6, D3-W4 = 8528.5, D4-W6 = 57615.4, and D4-W2 = 564040.9. Their rounding to kilometres is consistent with the baseline processed matrix.

This is a current integrity fingerprint, not a historical acquisition hash. The baseline file has no acquisition timestamp, HTTP headers, independently verifiable request record, or historical hash. The original source register claims access on **2026-11-06**; that date is **reported by the original project, not independently verified by this audit**. The endpoint can be reconstructed from the hardcoded coordinates and source/destination indices. Valid schema and plausible values alone do not prove when the response was fetched or that input coordinates are actual facility gates. A new live query would be new evidence, not proof of the old retrieval.

Waypoint evidence also limits the facility interpretation: the Ahmedabad destination snaps to **Ashram Road** and the Bhuj destination to **Jubilee Circle**. These are not evidence of the named Aslali/Sarkhej or Bhuj Mandi warehouses. All node coordinates should be described as assumed scenario proxy points unless facility-specific evidence is supplied.

The original pipeline overwrites the raw response during a live run and writes a hardcoded fallback response after network failure. It also supplies zero durations if the response lacks that array. These behaviors conflict with raw immutability and explicit-failure rules. Reproduction should use validated preserved evidence by default; optional live checks should fail clearly on error and preserve new responses separately.

## External source checks

All outcomes below were observed on 2026-11-07. Search indexing dates are not treated as publication dates. Successful access is not blanket verification of all claims attributed to a source.

| Source and exact URL | Observed access outcome | What it supports and what it does not |
|---|---|---|
| [NFSA coverage and entitlement](https://www.nfsa.gov.in/portal/Coverage_Entitlements_NFSA_AA) | Page content retrieved | PHH entitlement is 5 kg/person/month; AAY is 35 kg/household/month. It does not establish the modeled district demands or wheat/rice split. |
| [Gujarat government FCI address directory](https://gil.gujarat.gov.in/tendercms/TenderDocs/2011824164857520.pdf) | PDF content retrieved | Lists Sabarmati (owned), CWC Chhani, FSD & SPG Gandhidham, and CWC Surat. Supports named facilities in a historical directory, not their current capacities, coordinates, ownership descriptions beyond the directory, or stocks. The filename suggests an older document; do not use search crawler dating as proof of a recent operational inventory. |
| [Government eProcurement Ghanteshwar tender](https://eprocure.gov.in/eprocure/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&session=T&sp=Sz9izhMYwlQ72lAuL%2Bs0n7A%3D%3D) | Official tender text returned by search | Describes construction on FCI land at FSD Ghanteshwar, Gujarat Region, pincode 360006; published 23 September 2026. Establishes facility existence, not modeled coordinates, stock, monthly throughput or cost parameters. Session-dependent link may not be durable. |
| [OSRM Table API documentation](https://project-osrm.org/docs/v5.24.0/api/#table-service) | Page content retrieved | Distances are metres along fastest routes, not shortest-distance routes; durations are seconds. Driving output does not certify truck suitability, legal access, highway-only routes or actual travel conditions. |
| [NFSA Gujarat state page](https://www.nfsa.gov.in/State/GJ) | Page content returned by search | Displayed 15,441 FPS and zero godown fields. Incomplete fields show why this dashboard should not establish a complete infrastructure inventory. It does not verify the project's 17,000+ FPS or 220+ taluka counts. |
| [Rajya Sabha proceedings, 13 March 2020](https://cms.rajyasabha.nic.in/UploadedFiles/Debates/OfficialDebatesDatewise/Floor/251/F13.03.2020.pdf) | Official PDF text returned by search | Historical answer reports 33 FCI and 662 GSCSC godowns in Gujarat. Confirms a network much larger than four supply and six demand nodes; it is not a 2026 inventory. |
| [FCI official homepage](https://fci.gov.in/) | Page content retrieved | Official institutional context only. No granular records substantiating this project's numerical inputs were identified there. |
| [Gujarat FCS&CA homepage](https://fcsca.gujarat.gov.in/) | Fetch timed out | Not verified during this audit; timeout is not proof of a broken URL. |
| [CWC homepage](https://cewacor.nic.in/) | Fetch timed out | Not verified during this audit; timeout is not proof of a broken URL. |
| [Annavitran homepage](https://annavitran.nic.in/) | Not individually fetched | Original generic reference does not establish district allocation provenance. No claim of link verification is made. |
| [Routledge resilience book record](https://www.routledge.com/Critical-Infrastructures-Resilience-Policy-and-Engineering-Principles/Bhatia-Flynn-Ganguly/p/book/9781498758635) | Publisher page content retrieved | Correct author order/year: Ganguly, A. R., Bhatia, U., & Flynn, S. E. (2018), *Critical Infrastructures Resilience: Policy and Engineering Principles*. Original citation's 2020 date/order require correction. |
| [McGraw-Hill engineering catalogue](https://learn.mheducation.com/rs/303-FKF-702/images/McGraw-Hill%20Engr%20Catalogue.pdf) | Publisher PDF text returned by search | Supports Hillier and Lieberman, *Introduction to Operations Research*, 11th edition, copyright 2021. Does not supply project data. |

## Required claim corrections

1. **Beneficiary arithmetic:** 1.56 crore persons times 5 kg/month is **78,000 MT/month**, not 132,000 MT. The modeled demand corresponds to **2.64 crore PHH equivalents** if that simple per-person conversion is used. AAY entitlements use households, so a real district allocation derivation requires beneficiary composition. Remove the unsupported 1.56 crore derivation and avoid presenting scenario demand as statutory measured demand.
2. **Surat:** Replace claims of no local FCI storage with “no Surat supply node is included in the selected model.” The government directory explicitly lists CWC Surat; omission from a scenario is not real-world absence.
3. **Spatial scope:** Use “selected four-source, six-district scenario,” not a complete statewide operational network. Avoid calling mean lead distance statewide unless explicitly qualified as the modeled scenario.
4. **Facility precision:** Remove exact warehouse-estate claims and unverified silo/railhead/port subtype descriptions, or label them provisional. Routing an assumed coordinate does not verify its institutional identity.
5. **Cost parameters:** The project supplies no tender ID, priced schedule, period or page supporting INR 100/MT and INR 2.50/MT-km. They are assumptions. The calculated matrix inherits those assumptions.
6. **Capex and payback:** The poster invents INR 60 lakh for two loading docks and a weighbridge; neither procurement evidence nor a throughput engineering calculation supports it. Remove the cost and under-two-month payback claim. Operating-cost sensitivity is conditional on assumed inputs and does not establish attainable capacity or investment returns.
7. **Downstream counts:** Remove unsourced precise counts from the three-sentence limitations section while preserving three sentences. Do not replace them mechanically with incomplete dashboard counts.
8. **References:** Cite exact records for specific claims and correct the resilience book metadata. Generic portal names, unspecified 2024-2026 tender schedules, Census handbooks without a derivation, or CWC directories without a specific record are not evidence for modeled allocations.

## Classification and verification rules for the revised register

Keep field category distinct from evidence status. Use the allowed categories `OFFICIAL`, `RETRIEVED`, `CALCULATED`, `ASSUMPTION`; use separate statuses `VERIFIED`, `PROVISIONAL`, `ASSUMED`. Record exactly which field a source establishes. Official existence support does not upgrade assumed coordinates, throughput, demand or rates. A calculation can be reproducible while its inputs remain assumptions.

Preserve the original routing response. Record the audit date separately from the original claimed retrieval date, and do not retroactively assign a new acquisition timestamp. A final audit may report corrected provenance and reproducible mathematics; it cannot certify missing operational records as authentic.


## Live routing cross-check completed

A fresh HTTPS OSRM Table request succeeded during this audit. The separate response `data/raw/osrm_response_20261106T202929537569Z_bc5ce0f7c3f3.json` has a timestamp/hash/query manifest; all 24 distance and duration values exactly match the preserved baseline. See `outputs/audit/live_routing_comparison.txt` and `live_routing_check.log`. The original baseline hash remains unchanged. This verifies the routing output today, while the original acquisition timestamp and real facility identities remain unverified.
