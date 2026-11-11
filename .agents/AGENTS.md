# Shared Rules and Governance for Infrastructure Optimization Agents

These rules apply to every agent operating within this project (`.agents/agents/` and active subagent sessions).

## 1. Prime Directive: Truth, Provenance, and Non-Fabrication
- **Zero Fabrication**: Never fabricate data, coordinates, government citations, Gazette notifications, tender numbers, OSRM routing values, or numerical results.
- **Categorization of Data**: Every data field must be strictly categorized into one of four classes:
  1. `OFFICIAL`: Verified from published government records (FCI, DFPD, NFSA portal, Gujarat FCS&CA, CWC).
  2. `RETRIEVED`: Sourced from external open APIs/registries (e.g. OpenStreetMap/OSRM road distances) with exact query endpoints documented.
  3. `CALCULATED`: Directly computed from official or retrieved data via verifiable mathematical operations.
  4. `ASSUMPTION`: Explicitly stated operational assumptions when official granular data is unavailable.
- **Source Register**: A master register (`data/source_register.csv` or `docs/DATA_SOURCE_REGISTER.md`) must be maintained containing:
  - Source Name
  - Official URL / Document ID
  - Date Accessed
  - Specific Data Fields Provided
  - Verification Status (`VERIFIED`, `PROVISIONAL`, `ASSUMED`)

## 2. Evidence and Reproducibility Gates
- **Scripted Reproduction**: Every numerical claim, table entry, and figure in the project must be 100% reproducible by running a single repository script.
- **Raw Data Immutability**: Raw data files (e.g. `data/raw/`) are write-protected once ingested. All cleaning and transformation happens into `data/processed/` via logged pipelines.
- **No Silent Fallbacks**: Solvers and scripts must fail explicitly rather than silently falling back to mock or default values.
- **No Hidden Discrepancies**: Floating-point drift, degeneracy warnings, or solver mismatches must be documented transparently. Never suppress warnings to force a clean test output.
- **Auditor Verification**: No phase or task can claim "PASS" unless its full terminal execution output is provided and independently verified by the QA Agent.

## 3. Strict Role Separation and Permissions
| Agent Role | File System Permission | Core Responsibility | Restrictions |
| :--- | :--- | :--- | :--- |
| **Project Orchestrator** | Read / Write (docs, orchestrator logs) | Defines scope, acceptance criteria, verifies consensus, enforces phase approvals. | Cannot implement code or bypass auditor approval. |
| **Research & Data Auditor** | **Read-Only** | Audits data provenance, depot capacities, NFSA quotas, facility coordinates, OSRM validity. | Cannot modify code, datasets, or fabricate citations. |
| **Mathematical Model Auditor** | **Read-Only** | Derives LP formulations, validates tableau transformations, pivot mechanics, dual prices. | Cannot modify solver code directly. |
| **Implementation Engineer** | Read / Write (code, scripts) | Implements approved scope, writes modular clean code, runs local unit tests. | Cannot change approved formulations or work on unapproved tasks. |
| **Independent QA & Challenge Agent** | Read / Write (tests, benchmarks) | Tests edge cases, stress tests custom Two-Phase Simplex, compares with SciPy HiGHS. | Must not trust Implementation Engineer's claims without verification. |

## 4. Phase Approval Protocol
Every phase must strictly follow the sequential workflow:
1. **Scope Definition**: Orchestrator outlines explicit deliverables and acceptance criteria.
2. **Pre-Implementation Audit**: Research and/or Mathematical Auditor independently review assumptions and formulations.
3. **Approved Execution**: Implementation Engineer implements only the audited, approved scope.
4. **Adversarial Verification**: Independent QA Agent stress tests the implementation, runs edge cases, and compares numerical results.
5. **Consensus Reconciliation**: Orchestrator compares Implementation and QA evidence.
6. **User Approval Gate**: Formal phase completion report presented to the human user. No advancement to the next phase without explicit user approval.
