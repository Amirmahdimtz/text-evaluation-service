# Stage 11 — Enterprise Gate Closure Execution Packet

**Status:** `EXECUTION_PLAN_READY / GATE_BLOCKED` · 2026-10-31. **Scope:** Stage 11 only. Not authorization to deploy, access secrets, run load or handle private source text.

## Verified baseline (not acceptance)

- On Simorgh, operator observed a running existing inference container and installed Python `vllm` distribution `0.10.2`. A host-local model-list endpoint advertised one redacted model ID. These observations do not bind image digest, actual served artifact, license or service identity.
- An independently authorized **single synthetic one-field structured-output inference** returned HTTP 200, valid strict JSON, `finish_reason=stop`, 149ms for that POST, and 70/10 prompt/completion tokens. **Only auxiliary smoke PASS**, not `CriterionInference` or enterprise acceptance.
- Simorgh operator pulled `f001794` and reported **75 offline tests passed (0.62s)** plus a direct CLI default `DRY_RUN_NO_NETWORK`. GitHub Actions criterion/preflight/synthetic jobs on `8259509` each completed successfully. No subsequent real criterion model request was executed.
- The repo's reviewed `src/host/res/appsettings.yaml` has `llm.enabled=false`, `worker.enabled=false`, `http_security.enabled=false`; the documented secure enterprise Worker source resolver/executor remains **not wired**. A separate running vLLM endpoint **does not** constitute the protected application E2E chain.
- All **56** original organization test IDs from [traceability](01_test_strategy_and_traceability.md) remain `PENDING_SERVER`; Stage 11 `BLOCKED` and Stage 12 `NOT_STARTED`. Never upgrade a test ID based on auxiliary observations alone.

## Non-negotiable prerequisites (Wave 0: organizational signoff)

A signed, narrowly scoped **internal** Stage 11 test plan must identify the responsible Infra/SRE, Security/Network, IAM/PKI, DBA/KMS, AI Lead, Data Steward/Legal and Product/SME owners (as applicable); a physically/logically isolated staging target; deployment/registry and license authority; approved synthetic/gold dataset classes; least-privileged test identities; permissible network/packet/log observation; evidence retention; explicit per-test workload/GPU/VRAM and runtime ceilings; abort/recovery windows; and approved technical acceptance thresholds. Record only sanitized decision IDs in public trackers. Keep approvals, immutable artifact hashes, private model IDs, source text, packet captures, keys and logs **inside approved private storage**. A user's chat instruction to finish the stage is **not** a substitute for enterprise network, deployment, data, or privilege authorization.

**Immediate stop:** absent signed scope; unknown whether the serving endpoint is production/shared; auth bypass; unapproved model artifact/license; egress controls not ready; confidential prompt outside approved staging; overload/OOM/no capacity budget; any unexplained data leak; missing backup for an authorized migration; or an unexpected Critical/High vulnerability.

## Dependency-ordered execution waves

| Wave | Owning roles | Action and acceptance evidence | Blockers / representative original test IDs |
|---|---|---|---|
| 0 — Authorization and decisions | Infra/SRE, Security, Data Steward/Legal, Product/SMEs | Written staging scope, data rights, allowed commands, test identities, resource abort thresholds, metric/quality/SLO/RPO/RTO threshold approval and evidence custody. No active test until cleared. | `B11-01`, `B11-03`, `B11-08`, `B11-09`; OD-03/04/08/09/11/12/13/14 |
| 1 — Immutable runtime and model | MLOps, Security, Legal | Private signed app/container image digest; exact vLLM runtime and revision; immutable **both** candidate model+tokenizer+chat template+quantization, checksum/license, offline import/SBOM/scans; serving identity independently associated with deployed artifact. | `B11-02`; `S11-AI-01..04`, `S04-S11-06`, `S07-S11-01/06` |
| 2 — Real criterion contract, then AI quality | AI Lead, Data Steward, SMEs | With **fresh explicit permission for an additional request**, run the fixed synthetic real `CriterionInference` contract probe **once**, then separately approved two-model, three-domain blind golden benchmark. Require exact quote/offsets, abstention, schema failures, numerator/denominator, expert ratings, thresholds and meaningful CIs; do not infer model quality from a one-field smoke. | `B11-03`; `S07-S11-04`, `S11-AI-05..09`, `S08-S11-01..06` |
| 3 — Security, identities and privacy | Network Security, IAM/PKI, KMS, SecOps, DBA | Security-owner-observed firewall/DNS/packet **No-Egress** evidence, TLS/mTLS and identity denial, key isolation, org/tenant/actor authorization, encrypted source/feedback/evidence, log/telemetry redaction and private audit review. No security PASS without real negative cases. | `B11-04/05/07`; `S11-SEC-11`, `S04-S11-01..09`, `S10-S11-01..03` |
| 4 — Protected end-to-end chain | Software Architect, Security, DBA, AI Lead, QA | **Only after approved source resolver and protected Worker/SSO/KMS integration exists**, test authenticated API → authorized encrypted source → fenced Worker → pinned on-prem model → evidence-backed result → authorized report, with cross-org denial, failure/cancel/retry and idempotency. No direct endpoint bypass. | `B11-06`; `S11-E2E-12`, `S05-S11-*`, `S06-S11-*`, `S09-S11-*`, `S10-S11-04..06` |
| 5 — Capacity, DR, operations | SRE, DBA, MLOps, Product Owner | Only with isolated, resource-budgeted load window and approved thresholds: p50/p95/p99, throughput, queue/backpressure, GPU peak VRAM/OOM, long context, restart/lease fencing, error budget, recovery/backup restore/RPO/RTO, monitoring/on-call. | `B11-08/10`; `S11-AI-10`, `S04-S11-10`, `S07-S11-05`, `S09-S11-03/04/06`, `S10-S11-07` |
| 6 — Independent gate review | Approved Security/AI/Infrastructure/Business gate owners | Reconcile **all 56 original test IDs** to immutable private run IDs, result/retest evidence and signed applicable thresholds. Review Critical/High defects and documented remediations. Stage 11 `DONE` **only if all mandatory gate conditions actually PASS**. Otherwise retain `BLOCKED`. | `B11-01..10`, [full 56-ID ledger](01_test_strategy_and_traceability.md) |

The wave mappings above are **illustrative groups**, not a replacement for the complete, authoritative 56-ID ledger. Some tests overlap waves; retain every original test ID exactly once in final evidence.

## Already available, safe operator commands (no network/model inference)

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage11_criterion_contract_smoke.py \
  tests/test_stage11_synthetic_inference_smoke.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_criterion_contract_smoke.py
```

The final command is **default no-network**. It prints `DRY_RUN_NO_NETWORK` and sends no inference prompt. These tests **have already passed on Simorgh** (75 tests); repeat only if new code changes warrant regression.

### Additional real synthetic contract request — separate approval required

The reviewed existing script is `scripts/verification/stage11_criterion_contract_smoke.py`. Only an operator with **renewed, specifically scoped one-request approval** and confirmed approved loopback endpoint may run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_criterion_contract_smoke.py \
  --port 8000 --execute-approved
```

This makes **one** metadata GET and **at most one** real model POST with a fixed synthetic Persian text, real application JSON Schema, `max_tokens=320`, no retry, and sanitized output. The CLI's duration is socket bounded, not guaranteed whole-process timeout. A successful result is **auxiliary contract evidence**, not a full `S07-S11-01`/`S11-AI-06` PASS. If failure/timeout occurs, stop; no automatic second attempt, model reload, secret access, data expansion, or GPU load.

## Acceptance evidence and gate invariant

For each original test ID the authorized organization reviewer must privately retain: stable run ID and UTC time; approved scope/owner and independent reviewer; exact source/app/DB/worker/model/tokenizer/data/rubric/metric version references; resource and data permissions; acceptance threshold; bounded invocation/stop conditions; actual result (`PASS` / `FAIL` / `BLOCKED`); sanitized observations and denominators; failures/defect IDs; retest linkage; independent signoff. **Never publish internal IDs, artifact hashes, confidential prompts/results or raw telemetry to the public repository.** Public docs may include only reviewed redacted counts/status and approved evidence references.

**Release invariant:** any `PENDING_SERVER`, missing approved oracle, missing signed No-Egress, unresolved Critical/High without organization-approved treatment, or unsigned gate owner prevents `DONE`. A successful CLI, online endpoint, synthetic LLM response, 75 unit tests, or public GitHub CI alone cannot satisfy Stage 11. Stage 12 must **not start** until Stage 11 is independently accepted and production changes separately approved.