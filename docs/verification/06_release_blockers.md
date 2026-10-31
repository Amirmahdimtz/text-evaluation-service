# Stage 11 — Release Blocker and Preflight Decision Register

**Date:** 2026-10-28 · **Overall stage status:** `BLOCKED` · **Next stage:** unauthorized until Stage 11 PASS and separate Production approval. All organizational owners below are **roles from existing documents**, not confirmed signatories.

| ID | Priority | Open prerequisite / blocker | Required accountable owner | Closure evidence |
|---|---|---|---|---|
| B11-01 | P0 | Signed Stage11 authorization, isolated staging, test identities, data classification, allowed network actions and explicit resource/stop window not provided | Security + Infra/SRE + Data Steward/Legal | Approved test plan, named approvers and sanitized approval reference stored securely |
| B11-02 | P0 | Real model and vLLM pinned artifact revisions, import/legal license, tokenizer checksum and full software supply-chain attestations absent | MLOps + AI Lead + Security + Legal | Immutable private hashes, license and exact image/SBOM/vulnerability acceptance (`S04-S11-06`, `S07-S11-06`) |
| B11-03 | P0 | Golden three-domain corpus, qualified expert labels, holdout protocol and numeric AI thresholds `OD-14` not approved | Data Steward + SMEs + AI Lead + Product Owner | Adjudicated split manifests and signed metric acceptance thresholds |
| B11-04 | P0 | Organizational SSO/JWKS refresh/revocation, roles/reviewer assignment and ingress TLS/mTLS policy absent | IAM + AppSec + PKI + Product Owner | Authorized identity infrastructure, token revocation tests, full-path gateway protection, successful negative access cases |
| B11-05 | P0 | KMS/envelope keys, retention/legal hold, backup and secure source access policy `OD-08` unapproved | Security + Data Steward + KMS/DBA | Signed policy, scoped key lifecycle, isolation/restore, no leaked source or key |
| B11-06 | P0 | API/DB guards currently development-only; secure enterprise Worker source resolver/executor intentionally not wired | Software Architect + Security + DBA + AI Lead | Reviewed approved staged adapter/integration patch; safe end-to-end tests using real authorized model, without bypassing security controls |
| B11-07 | P0 | No corporate No-Egress, segmentation, multi-sink log-redaction or supply-chain proof | Network Security + SecOps + SRE | Authorized packet and DNS/TCP evidence, trace/log review, provenance/license signoff |
| B11-08 | P0 | Actual workload, SLO/RPO/RTO, GPU/VRAM and approved load/failure-injection budgets `OD-12/13` missing | SRE + Infrastructure + Product Owner | Approved threshold and abort policy, measured load/soak and restore run artifacts |
| B11-09 | P1 | Rubric/scoring/reviewer governance `OD-03/04/06/09/11` remains `OPEN`; Stage12 business signoff not granted | SMEs + Product Owner + Reviewer Lead + AI Quality | Approved policy for applicable Stage11 acceptance and separate Stage12 official release |
| B11-10 | P1 | Organization-owned incident monitoring, audit retention, on-call/restore/change management not assigned | SRE + Security + Operations | Approved operational runbooks, alerts and ownership with controlled staging rehearsal |

**Approval conditions:** A user's request to start Stage11 authorizes planning, not unbounded privileged execution, moving proprietary artifacts, exposing confidential data, altering shared containers/network/secrets, applying migrations to organizational DB, downloading models or starting GPU load. Do not request credentials in chat or store them in GitHub.

**First permitted next action:** receive approved **nonsecret** staging readiness metadata and role/approval references. The [host-only inventory](07_stage11_readonly_preflight.md) was actually run by the operator on Simorgh (13 offline safety tests passed; one RTX3090 observed); that snapshot did **not** validate inference capacity. The new bounded [read-only container/package-and-loopback metadata probe](08_stage11_container_metadata.md) is tested only off-host and can be used by an appropriately authorized local operator with scoped Docker metadata/exec and optional loopback model-list permission. Do **not** use it without authorization or treat this as a full security/runtime acceptance test. If mandatory approvals remain absent, retain `BLOCKED`. All 56 enterprise tests remain `PENDING_SERVER`.

## Decision/Progress policy

- Record Stage11 `BLOCKED` after starting documentation-only preflight, not `DONE`.
- Record no numeric quality, throughput or No-Egress status as passed.
- Preserve existing 240 CI and 226 operator-reported Simorgh offline passes as historical *local* evidence, not Stage11 results.
- Stage12 is not authorized and cannot start without the independent Stage11 acceptance gate.
 
## Bounded synthetic smoke authorization and remaining boundary — 2026-10-28

The user authorized exactly one minimal synthetic-only inference against the existing internal service. A [one-shot bounded probe](09_stage11_single_inference_smoke.md) with 35 assistant-host synthetic tests has been prepared; **no real inference has yet been observed or executed by the assistant**. This narrowly authorizes requesting the single synthetic inference at the approved loopback endpoint; it does not resolve B11-01 (enterprise staging/security/data approval), B11-02/03 (artifact and gold dataset), B11-06 (protected Worker), B11-07 (No-Egress), or B11-08 (capacity/SLO). No acceptance test is marked `PASS` in advance; all 56 organization tests remain `PENDING_SERVER` and Stage11 stays `BLOCKED`.

## Progress checkpoint: one authorized synthetic model completion succeeded — 2026-10-28

The operator reported a single real loopback synthetic completion on source `0ba42a2`: HTTP 200, valid one-field strict JSON object, `finish_reason=stop`, 149ms POST timing, 70 prompt + 10 completion tokens. Source tests (35 on Simorgh) and dry-run also passed. **This retires only the auxiliary "can one synthetic JSON-schema request complete?" uncertainty**, not B11-01..B11-10, the secure product Worker integration, signed model/provenance, production network/data controls, required golden benchmark, load/SLO, approved IAM/KMS or release authorization. The one-request permission was consumed. **Stage11 `BLOCKED` and all 56 mandatory organization tests `PENDING_SERVER`**; Stage12 `NOT_STARTED`. [Evidence](09_stage11_single_inference_smoke.md).

## Stage11 execution dependencies — 2026-10-31

A dependency-ordered [Stage11 closure execution packet](11_stage11_gate_closure_execution.md) now provides Wave 0 organizational approval/limits; Wave 1 immutable model/runtime provenance; Wave 2 real criterion validation and adjudicated dual-model tri-domain gold results; Wave 3 No-Egress/IAM/KMS/log-redaction; Wave 4 protected application/Worker E2E; Wave 5 SLO/Load/Backup/Recovery; Wave 6 independent full 56-ID release-gate review. Each wave identifies original owners and evidence; **no protected step is declared authorized or completed by publishing this packet**.

The repository's production config still has `llm.enabled=false`, `worker.enabled=false` and `http_security.enabled=false`. The secure organizational Worker source resolver is not wired; safe actual integration is therefore a **P0 blocker**, not simply a test-environment switch. One live minimal schema smoke was completed previously; this does not prove the broader `CriterionInference` or enterprise gate. An independent parse confirms 56 unique original Stage11 test IDs in the ledger, not their execution.

**Gate:** all 56 enterprise tests remain `PENDING_SERVER`; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`; no network/model/production actions authorized by this documentation change.

## Right-sized interpretation of B11-01..10 — 2026-10-31

The user's governing engineering preference is **standard, secure, useful production software without unnecessary enterprise infrastructure** (`D-018`). Read the original blocker table as **required *capabilities and test evidence***, not as an obligation to procure a separate physical staging fleet, mandatory Kubernetes, a new corporate SSO/Vault/KMS product, pervasive same-host mTLS, an observability cluster, or a week-long load test. Use the existing internal platform where it meets the same requirements. Full rationale and status per blocker: [Pragmatic Stage11 baseline](../requirements/07_pragmatic_stage11_baseline.md).

- **Still P0:** `B11-06` requires real approved protected-source Worker integration, not a bypass. `B11-02/03` require approved model provenance and quality/criterion evidence; `B11-04/05/07` require real authentication, encryption/key custody and no-egress, not named vendor products; `B11-08` requires measured capacity/recovery against a **real accepted workload**; `B11-01` requires authorization for the protected test operations.
- **Conditional implementation choices:** existing RS256 signed-identity infrastructure may be reused in lieu of adding custom SSO only when a trusted issuer and revocation/key-rollover policy are adequate; existing AES-256-GCM may be reused without buying a separate KMS only with an authorized, tested key-management/rotation/backup plan. A single host and same-host loopback are acceptable only if isolation and SLO/availability requirements actually pass; cross-host links still require validated transport security.
- **Test efficiency:** the original 56 IDs **must all be reconciled**, but can share isolated run IDs and collected evidence when distinct acceptance checks are genuinely covered. The original mandatory two-model Stage11 gate is **not waived**; sequential model comparison may avoid simultaneous GPU loads.
- **Release distinction:** `D-015` formal business/SME sign-off is Stage12, **not** a demand for multiple employer signatures on every Stage11 test. Organizational permission for privileged operations/data/network changes remains a separate absolute prerequisite. All 56 original IDs remain `PENDING_SERVER` and Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## B11-06 implementation update — 2026-10-31

The **development/test** protected-source Worker integration gap has been addressed using existing layers and services in commit `e63b2ca`. Repository reads a matching tenant/owner encrypted source + validated published candidate Rubric; injected executor decrypts only under approved development flags and current key version, evaluates with the existing engine, checks original quote/offsets, encrypts details, returns review-only results, and preserves fenced result finalization. Host closes the actual provider client. A real isolated PostgreSQL + signed HTTP + AES-GCM + Worker + **synthetic engine** E2E passed within Stage10 GitHub Actions `41178699423` (full suite 374 passed). Five related GitHub CI workflows succeeded.

**Do not close B11-06 P0 yet:** staging/production deployment still intentionally fail-closed (`PsqlDbContext` only supports isolated development loopback databases), real on-prem model+enterprise identity/key custody E2E and safe deployment must be separately approved and tested. Do not replace the synthetic stub result with real model evidence. Remaining B11-01..10 operational/acceptance evidence is unchanged; all 56 required IDs remain `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. [B11-06 runbook](12_stage11_protected_worker_integration.md).

## B11-06 host-side offline regression result — 2026-10-31

The operator ran the protected Worker and prior Worker unit suites after pulling `c8f10ba` on Simorgh: **36 passed in 0.87s**. This closes uncertainty about Python import/dependency compatibility of these synthetic Worker tests on that host and reinforces **B11-06 offline integration**; it does not close the P0 blocker for corporate secured API → DB → real on-prem LLM E2E, IAM/key lifecycle, or staging deployment. The original 56 mandatory enterprise tests remain `PENDING_SERVER`, Stage11 `BLOCKED`; Stage12 not started.

## Active full-criterion contract smoke did not pass — 2026-10-31

The operator-provided Simorgh output for one approved synthetic on-prem criterion request showed `HTTP 200` but `CRITERION_CONTRACT_UNVERIFIED` and `6047 ms` elapsed; this is **not PASS**. The one-field JSON smoke previously succeeded, but the actual multi-field criterion/evidence/offset contract has **not been demonstrated**. The old diagnostic discarded the cause category, so the blocker cannot be responsibly attributed to vLLM, model, token limit or prompt without additional authorized evidence. The request has occurred and must **not** be automatically retried.

The redacted offline harness now distinguishes broad failure categories for a **future specifically authorized synthetic run**; GitHub Actions `41181109595` passed **90 tests**. This does not close `B11-02/03/06` or change the enterprise 56-ID gate. Stage11 remains `BLOCKED`; Stage12 `NOT_STARTED`. [Evidence and runbook](10_stage11_criterion_contract_smoke.md).

## B11-03 / B11-06: verified failure of strict synthetic quote grounding — 2026-10-31

The operator's second real-model one-shot synthetic criterion smoke returned HTTP 200, 113 completion tokens, 6010ms and `QUOTE_OFFSET_MISMATCH`, so **the full evidence contract is not yet verified**. The underlying Pydantic shape was accepted through the quote-check, but the redacted result cannot distinguish a fabricated/mutated quote from wrong Unicode offsets. No model/infra root cause was assumed; no raw content was requested.

Commit `fd072f1` adds explicit Unicode codepoint source bounds to prompts and fixed-granularity diagnostic categories, preserving strict source equality and no auto-repair. Seven CI workflows passed with mock and isolated DB data, not live-model inference. Original 56 enterprise acceptance IDs are `PENDING_SERVER`; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. No new actual inference is permitted from the consumed one-request approval. [Runbook](10_stage11_criterion_contract_smoke.md).
