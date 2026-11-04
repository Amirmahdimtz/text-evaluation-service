# Stage 11 — GPU-free product-gap review and executable readiness gates

**Review date:** 2026-11-02. **Method:** source, workflow, configuration, traceability and runbook review on `main` through `80c0635` plus operator/CI evidence. No Simorgh server shell, real database, vLLM, GPU, or confidential input was accessed for this review.

**Scope decision:** build a correct, repeatably testable Persian **text-evaluation** application on the temporary shared host and hand it to the organization. Enterprise infrastructure operations (corporate SSO provisioning, organization KMS, firewall policy, operational Go-Live certification) belong to the recipient. This **does not transfer responsibility for application-layer authorization, encryption, data isolation, safe inference, grounded results or trustworthy scoring**.

## Verified implemented components

| Source reviewed | Actual evidence | Boundary |
|---|---|---|
| `src/application/text_evaluation/text_evaluation_controller.py` and DTOs | Four signed HTTP routes: submit, private report, rubric list, reviewer comment | No approval or rubric-administration UI |
| `src/core/services/text_evaluation/rubric_schema.py`, `scoring_service.py` | Three domain candidate Rubrics, version/checksum, bounded 0-5 score and deterministic Python aggregation | Rubrics/official rounding and numeric business thresholds still provisional |
| `src/core/services/text_evaluation/criterion_evaluation_service.py` | Exact source quote/Unicode offset verification and conservative abstention for research novelty | Model semantic relevance and scientific truth not proven |
| `src/core/services/text_evaluation/protected_evaluation_executor.py` | Encrypted scoped source, validated published Rubric, source-backed encrypted criterion output and consistency-checked coverage/status | Currently development-only; real model full-path not run |
| `src/infrastructure/repositories/text_evaluation/`, `src/host/evaluation_worker.py` | Async PostgreSQL, idempotent submission, Worker fencing/heartbeat/recovery, scoped readback | Only isolated test database is allowed by current runtime |
| `src/host/request_body_guard.py` | Bounded JSON body, duplicate-header rejection and declared-size checks | Corporate reverse-proxy policies not tested |
| `src/infrastructure/providers/llm/local_llm_provider.py` | Explicit internal endpoint, strict structured-output transport, circuit/retry bounds | Live model quality/runtime/provenance remains open |

**Real evidence:** [GitHub Actions Stage10 `41405074852`](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41405074852) completed `SUCCESS` with **424 passing tests** on synthetic/isolated PostgreSQL, including all three domain scenarios. Simorgh operator additionally reported **66 passing offline tests** on `ce5e930` and **16 passing auth/HTTP-guard tests** on `e7699be`. This is not live GPU inference or a production deployment.

## Prioritized product backlog — evidence required, not assumed DONE

| ID | Priority | Real source gap / open decision | Required completion evidence | GPU |
|---|---|---|---|---|
| G11-P01 | P0 | **Runtime activation / distribution:** private owner-only `TES_STAGE11_SETTINGS_FILE` now permits isolated development settings without Git edits. `PsqlDbContext.get_test_database_url()`, API settings gate, Worker Host and protected executor remain restricted to `development`/test-only DB. No general secure deployment wiring exists. Do not simply disable guards | Reviewed explicit runtime/deployment design; isolated signed API + Worker with policy/secret references and safe DB lifecycle; negative config tests | No to develop; real model E2E later |
| G11-P02 | P0 | **Full internal inference E2E** not yet proven: signed HTTP -> encrypted DB -> Worker -> actual local model -> evidence -> authorized report | Authorized bounded synthetic whole-path result, valid quote/offsets and ciphertext on real target runtime | **Yes** |
| G11-P03 | P0 | **Persian model quality/selection** for `speech`, `media`, `research` unvalidated against expert labels; earlier six-criterion `speech` live attempt had `LLM_CIRCUIT_OPEN` | Versioned authorized labels, per-domain quality/abstention/groundedness metrics, model comparison per applicable approved scope | **Yes** |
| G11-P04 | P0 | **Partial engineering resolution:** signed/scoped report now reconstructs the deterministic **candidate `provisional_score`** from all stored criterion rows + pinned published/retired rubric. The persisted official `overall_score` remains `NULL`; official rounding/publication policy OD-04 is open | Synthetic isolated-PostgreSQL CI confirms all three domains and report reconstruction after Rubric retirement; obtain OD-04 approval before any official numeric score/persistence | No |
| G11-P05 | P1 | **Packaging/installation reproducibility:** a test-only `compose.stage11-isolated-db.yml` and a host-only dry-run preflight now exist; no API/Worker image or validated runnable multi-process deployment exists. No manual startup has been executed on Simorgh. | Clean isolated install, explicit startup topology, pinned dependencies, validated execution/rollback for chosen deployment target | No for code/docs |
| G11-P06 | P1 | **Long document inference policy** uses conservative chunking/abstention; no measured model-context budget or validated document-level coherence | Explicit accepted long-text behavior and synthetic negative tests, followed by real tokenizer/context quality evidence | Mostly **Yes** |
| G11-P07 | P1 | **Capacity and recovery on target hardware** not demonstrated; previous instantaneous GPU/VRAM snapshots are not load/SLO acceptance | Agreed request limits, observed throughput/latency/OOM, queue fencing, restart and isolated DB recovery proof | **Yes** |
| G11-P08 | P1 | **Final immutable model and Rubric provenance:** configured revision is declared but not runtime verified; candidate Rubrics have `approval_status=PROPOSED` | Accepted model/runtime checksum/license/identity, Rubric/prompt policy and reproducible release manifest | Mostly after GPU |
| G11-P09 | P1 | **Application handoff prerequisites** for organization-specific IAM/PKI/KMS/network/backup remain outside our integration tests | Explicit recipient ownership checklist, adapter contracts and known limitations without claiming organization controls PASS | No for documents; recipient action later |

P0 means product implementation or intended functionality may be unproven/unshippable. The `PENDING_SERVER` label remains for live-model checks, and organization-owned checks retain the [original Stage11 IDs](01_test_strategy_and_traceability.md).

## GPU-free completion checklist (this Stage 11 preparation)

- [x] Inspect actual architecture, defaults, entrypoints, runtime restrictions and CI/Simorgh evidence.
- [x] Produce an operator-safe GPU-free installation/validation/handoff runbook without inventing Docker deployment or live secrets.
- [x] Add project README with correct no-network regression commands and Stage11 readiness caveats.
- [ ] Resolve G11-P01 full **deployable package** without modifying the shared server. A real API+Worker **two-process** E2E against CI-isolated PostgreSQL 17 and a synthetic loopback model now passes ([runbook](16_stage11_isolated_process_e2e.md)); an opt-in on-host Docker runner exists but has **not** run on Simorgh. No production deployment readiness claim.
- [x] Document and test the **candidate read-only** aggregate response
  contract without fabricating an official score
  ([contract](../architecture/04_stage11_review_only_scoring_contract.md)).
- [ ] Resolve G11-P04 numeric delivery/rounding/coverage policy after OD-04
  owner approval; do not silently promote the candidate Decimal into
  `Numeric(6,3)`.
- [ ] Prove G11-P05 with a fresh isolated installation/artifact build, not merely markdown.
- [ ] Real model-dependent G11-P02/03/06/07/08 remain pending until a future separately permitted GPU window.

## Acceptance and revision boundary

This review adds **no** new score or benchmark result and does not run Stage 12. Original 56 Stage11 enterprise IDs remain in the authoritative ledger; their proposed product vs recipient ownership is in [matrix 14](14_stage11_product_handoff_scope_matrix.md), not silently accepted as formal waiver. Product handoff can be discussed independently from recipient production Go-Live, but the service cannot be called fully built/tested while P0 items or real model gates remain unverified.

## 2026-11-04 — targeted non-deployment image packaging (G11-P01/P05)

A Stage11-only **API image candidate** and CI smoke were added.
`Dockerfile.stage11-candidate` uses an explicitly versioned
Python 3.12 base, pinned application requirements,
allowlisted `src/` copy, nonroot UID/GID 10001 and
unchanged fail-closed API startup. CI will build the
container and import actual FastAPI code in a
`--network none --read-only --cap-drop ALL` container.
No Worker, PostgreSQL, vLLM or GPU service is launched.
See `docs/deployment/12_stage11_candidate_image.md`.

This is **partial G11-P05 engineering verification** only:
no immutable approved base digest, signed image, SBOM,
privately provisioned secrets, approved non-development
PostgreSQL, multi-process topology or actual staging
deployment. G11-P01 remains OPEN/P0 and G11-P05
PARTIAL_PENDING_CI. The prior isolated synthetic API →
Worker E2E is already evidenced, so the next high-value
external prerequisite is authoritative served model/
tokenizer/backend attestation followed by separately
approved full-path GPU E2E. Stage11 BLOCKED.
