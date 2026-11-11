# Infrastructure Optimization Agent Workspace Structure

This directory defines the multi-agent system configured for the project:
**"Optimisation of Food Grain Distribution from FCI Depots to District Warehouses in Gujarat"**.

## Available Agents

1. **`project-orchestrator`** (`.agents/agents/project-orchestrator/agent.md`)
   - Primary coordinator owning project plan, decisions, dependencies, and phase approvals.
2. **`research-data-auditor`** (`.agents/agents/research-data-auditor/agent.md`)
   - Read-only data provenance auditor verifying FCI facilities, NFSA allocations, coordinates, and freight equations.
3. **`mathematical-model-auditor`** (`.agents/agents/mathematical-model-auditor/agent.md`)
   - Read-only mathematical auditor verifying LP formulations, tableau mechanics, Bland's rule, and dual shadow prices.
4. **`implementation-engineer`** (`.agents/agents/implementation-engineer/agent.md`)
   - Implementation agent writing clean, modular Python solvers and pipeline scripts.
5. **`independent-qa-agent`** (`.agents/agents/independent-qa-agent/agent.md`)
   - Adversarial QA agent verifying numerical outputs against SciPy HiGHS benchmarks and stress testing edge cases.

## Invocation in Antigravity CLI

Launch a dedicated session with any agent using:
```bash
agy --agent project-orchestrator
agy --agent research-data-auditor
agy --agent mathematical-model-auditor
agy --agent implementation-engineer
agy --agent independent-qa-agent
```
