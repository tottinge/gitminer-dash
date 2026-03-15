# Evidence-Backed AI Insights
## Current status (done)
- [x] Deterministic insights pipeline is working end-to-end (snapshot → scoring → evidence → report).
- [x] Shared contracts and schema versioning are implemented (`insights/models.py`, `insights/schema_version.py`).
- [x] Snapshot assembly and storage are implemented (`insights/snapshot_builder.py`, `insights/snapshot_store.py`).
- [x] Deterministic scoring and evidence attachment are implemented (`insights/hotspot_scoring.py`, `insights/evidence_builder.py`, `insights/report_builder.py`).
- [x] Delivery surfaces are implemented (`scripts/generate_insights`, `pages/ai_insights.py`).
- [x] Core deterministic tests are in place and passing:
  - [x] `tests/test_snapshot_builder.py`
  - [x] `tests/test_hotspot_scoring.py`
  - [x] `tests/test_evidence_builder.py`
  - [x] `tests/test_report_builder.py`
  - [x] `tests/test_ai_insights_page.py`

## Next wave stories (user POV slices)
### [x] Slice 1 — Export snapshot artifact for reuse
- **User invokes:** `./scripts/export_snapshot . --from <YYYY-MM-DD> --to <YYYY-MM-DD>`
- **User uses result:** gets a versioned snapshot artifact they can archive, diff, and reuse in offline/automation workflows.
- **Acceptance checks:**
  - [x] command writes a valid snapshot artifact with schema/version
  - [x] output reflects selected repo + date range
  - [x] rerun with same inputs is deterministic
- **Not yet in this slice:** LLM narrative generation and citation validation

### [x] Slice 2 — Build prompt payload from deterministic report
- **User invokes:** `./scripts/generate_insights . --from <YYYY-MM-DD> --to <YYYY-MM-DD> --prompt-payload`
- **User uses result:** gets a compact, provider-agnostic prompt payload based only on report data + evidence refs.
- **Acceptance checks:**
  - [x] payload includes ranked hotspots and explicit evidence refs
  - [x] payload order is deterministic
  - [x] payload excludes uncited/generated claims
- **Not yet in this slice:** external provider calls

### [x] Slice 3 — Enforce citation guard on narrative claims
- **User invokes:** `./scripts/generate_insights ... --narrative-file <path> --validate-citations`
- **User uses result:** sees a clear pass/fail result showing whether narrative claims are backed by known evidence refs.
- **Acceptance checks:**
  - [x] invalid or uncited claims are reported with reasons
  - [x] valid claims pass without false failures
  - [x] validation checks only report-backed evidence
- **Not yet in this slice:** generating narrative text

### [x] Slice 4 — Optional strict-citation narrative generation
- **User invokes:** `./scripts/generate_insights . --from <YYYY-MM-DD> --to <YYYY-MM-DD> --narrative --strict-citations`
- **User uses result:** receives readable narrative text only when citation validation passes.
- **Acceptance checks:**
  - [x] provider-agnostic `llm_client` interface is used
  - [x] narrative output includes citations tied to evidence refs
  - [x] deterministic report still returns if narrative fails
- **Not yet in this slice:** multi-provider tuning and optimization

## Done criteria per slice
- [x] slice tests added/updated and passing
- [x] `./run_tests` passes
- [x] `./check` passes
- [x] this file updated with completion markers
