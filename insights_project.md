# Evidence-Backed AI Insights: Feature and Architecture
## Problem statement
`gitminer-dash` computes useful repository metrics, but most outputs are page-specific visualizations. This makes it difficult for an LLM agent to generate reliable, evidence-backed insights without scraping UI state or reconstructing context.
## Thin-slice end-to-end user story (v1)
As a repo maintainer, I choose a date range and request AI insights. The system returns the top 5 risky change hotspots with a score, a concise explanation, explicit evidence (files, affinity pairs, commit SHAs, metric values), and suggested next actions.
## Scope
### In scope (v1)
* Produce one normalized, versioned analysis snapshot from existing algorithms.
* Rank deterministic hotspot candidates from snapshot signals.
* Attach auditable evidence references to each hotspot.
* Optionally generate LLM narrative text constrained to cited evidence.
* Expose results through one CLI command and one Dash page.
### Out of scope (v1)
* Autonomous code remediation or PR generation.
* Full code-content RAG.
* Cross-repository portfolio analytics.
## Acceptance criteria (v1)
* For a repo and date range, the system emits a versioned snapshot artifact.
* Insight output includes at least 5 ranked hotspots.
* Each hotspot includes at least 2 concrete evidence references.
* Re-running with the same inputs yields reproducible ranking and evidence.
* Dash and CLI both consume the same report contract.
## Architectural layout
### Domain contracts
Create `insights/models.py` to define typed contracts:
* `AnalysisSnapshot`
* `HotspotCandidate`
* `EvidenceRef`
* `InsightReport`
Include `schema_version` on top-level contracts.
Create `insights/schema_version.py` for schema constants and migration hooks.
### Snapshot assembly
Create `insights/snapshot_builder.py` to assemble a canonical snapshot from existing algorithms and commit streams.
Reuse current logic from:
* `algorithms/commit_frequency.py`
* `algorithms/diff_analysis.py`
* `algorithms/affinity_calculator.py`
* `algorithms/commit_graph.py`
* `algorithms/chain_analyzer.py`
Create `insights/snapshot_store.py` for snapshot save/load and local cache behavior.
### Deterministic insight engine
Create `insights/hotspot_scoring.py` to compute hotspot risk from churn, coupling, and recurrence signals.
Create `insights/evidence_builder.py` to attach concrete metric and commit/file evidence to each candidate.
Create `insights/report_builder.py` to build deterministic, non-LLM insight reports.
### Optional LLM narrative layer
Create `insights/llm_client.py` behind a provider-agnostic interface.
Create `insights/prompt_builder.py` to transform structured insights into compact prompt payloads.
Create `insights/citation_guard.py` to ensure generated claims are backed by existing evidence references.
### Delivery surfaces
Create `pages/ai_insights.py` as a Dash view for ranked hotspots and evidence drill-down.
Create `scripts/generate_insights` as a CLI entrypoint for local and automation usage.
Optionally add `scripts/export_snapshot` later for offline agent workflows.
### Testing strategy
Add tests:
* `tests/test_snapshot_builder.py`
* `tests/test_hotspot_scoring.py`
* `tests/test_evidence_builder.py`
* `tests/test_report_builder.py`
* `tests/test_ai_insights_page.py`
Use fixtures to keep the same repo/date input deterministic and assert evidence coverage constraints.
## Data flow
1. `data.commits_in_period` provides commit stream for a selected range.
2. `insights/snapshot_builder.py` creates `AnalysisSnapshot`.
3. `insights/hotspot_scoring.py` ranks hotspot candidates.
4. `insights/evidence_builder.py` enriches candidates with evidence references.
5. `insights/report_builder.py` produces `InsightReport`.
6. Optional LLM layer rewrites for readability without introducing uncited claims.
7. Dash page and CLI render the same report contract.
## First implementation increment
Implement only these components first:
* `insights/models.py`
* `insights/snapshot_builder.py`
* `insights/hotspot_scoring.py`
* `scripts/generate_insights`
* minimal `pages/ai_insights.py`
This yields a small, testable, end-to-end path from commit data to evidence-backed hotspot insights.
