# Stage11 — Product Validation vs Recipient Organization Handover Matrix

**Scope decision:** D-020 (user confirmation 2026-11-02). This is a **proposed responsibility mapping**, not a retroactive modification of the original mandatory test specification. The user owns application creation, repeatable on-prem Simorgh validation and a handoff bundle; the recipient organization owns deployment-platform certification and enterprise governance.

**Definitions:** `PRODUCT_TEST` means we must implement and verify the application-level behavior (with mocked/isolated tests now, and controlled live-model tests once GPU becomes available). `ORGANIZATION_HANDOVER` means primary real-world acceptance depends on recipient-owned corporate IdP, PKI, KMS, network, backup, observability, retention or enterprise operations. **Mixed original test oracles remain split:** even for an organization-owned ID, the product-level assertions must still be tested in our other product suites; even for a product-owned ID, recipient-specific environment checks remain documented as handover prerequisites.

**Evidence policy:** None of the 56 original test IDs is marked `PASS` by this classification. Keep existing original test ledger and statuses unchanged until an accepted technical replacement of the Stage11 gate and explicit user approval. All entries below carry `ORIGINAL_GATE_PENDING`; no organization certification is represented as completed.

**No GPU resource assumption:** shared Simorgh GPU/vLLM was voluntarily stopped for a different project. The mapping is documentation-only and does not authorize live inference, restart, data access, server changes or production deployment.

| Original Stage11 test ID | Proposed primary responsibility | Focus / retained boundary | Original gate evidence |
|---|---|---|---|
| `S11-AI-01` | `PRODUCT_TEST` | Real GPU/driver inventory | `PENDING_SERVER` |
| `S11-AI-02` | `PRODUCT_TEST` | Actual internal weights and license | `PENDING_SERVER` |
| `S11-AI-03` | `PRODUCT_TEST` | Live Qwen2.5 inference | `PENDING_SERVER` |
| `S11-AI-04` | `PRODUCT_TEST` | Live Qwen3 inference | `PENDING_SERVER` |
| `S11-AI-05` | `PRODUCT_TEST` | Expert golden dataset | `PENDING_SERVER` |
| `S11-AI-06` | `PRODUCT_TEST` | Actual generation quality | `PENDING_SERVER` |
| `S11-AI-07` | `PRODUCT_TEST` | Model-vs-human rating | `PENDING_SERVER` |
| `S11-AI-08` | `PRODUCT_TEST` | Evidence relevance, hallucinations | `PENDING_SERVER` |
| `S11-AI-09` | `PRODUCT_TEST` | Real prompt injection and long-context cases | `PENDING_SERVER` |
| `S11-AI-10` | `PRODUCT_TEST` | Real GPU load and VRAM | `PENDING_SERVER` |
| `S11-SEC-11` | `ORGANIZATION_HANDOVER` | Corporate firewall/DNS, TLS and enterprise network audit; app-level no-leak checks stay product-owned | `PENDING_SERVER` |
| `S11-E2E-12` | `PRODUCT_TEST` | Deployed internal end-to-end chain | `PENDING_SERVER` |
| `S04-S11-01` | `ORGANIZATION_HANDOVER` | Corporate firewall/DNS/packet policy; the product still needs private-only inference configuration | `PENDING_SERVER` |
| `S04-S11-02` | `ORGANIZATION_HANDOVER` | Corporate IdP provisioning/revocation; signed-JWT verification remains a product test | `PENDING_SERVER` |
| `S04-S11-03` | `ORGANIZATION_HANDOVER` | Corporate Vault/KMS identity and operations; safe secret references stay product-owned | `PENDING_SERVER` |
| `S04-S11-04` | `ORGANIZATION_HANDOVER` | Corporate PKI, mTLS and network trust chain; app must not disable auth | `PENDING_SERVER` |
| `S04-S11-05` | `ORGANIZATION_HANDOVER` | Corporate log/trace/metric sinks; product-safe logging still needs tests | `PENDING_SERVER` |
| `S04-S11-06` | `PRODUCT_TEST` | Approved artifacts not imported or selected | `PENDING_SERVER` |
| `S04-S11-07` | `ORGANIZATION_HANDOVER` | Enterprise container/network segmentation; application tenant isolation stays product-owned | `PENDING_SERVER` |
| `S04-S11-08` | `ORGANIZATION_HANDOVER` | Corporate retention, legal-hold and backup policy; app encryption stays product-owned | `PENDING_SERVER` |
| `S04-S11-09` | `PRODUCT_TEST` | GPU/runtime unavailable | `PENDING_SERVER` |
| `S04-S11-10` | `PRODUCT_TEST` | Production-like performance/DR unavailable | `PENDING_SERVER` |
| `S05-S11-01` | `ORGANIZATION_HANDOVER` | Corporate DB role, identity and PKI configuration; scoped repository tests stay product-owned | `PENDING_SERVER` |
| `S05-S11-02` | `ORGANIZATION_HANDOVER` | Corporate backup, key rotation/retention and KMS; AEAD round-trip and tenant denial remain product-owned | `PENDING_SERVER` |
| `S05-S11-03` | `PRODUCT_TEST` | Production-size multi-worker and GPU-backed queue capacity/deadlocks depend on Stage09 runtime, OD-10/12/13 | `PENDING_SERVER` |
| `S05-S11-04` | `PRODUCT_TEST` | Full route/gateway identity/role checks and database scope integration not implemented until Stage10 | `PENDING_SERVER` |
| `S05-S11-05` | `PRODUCT_TEST` | Authentic staging migration and backup/forward-fix depend on approved deployment, signed artifacts and realistic data shape | `PENDING_SERVER` |
| `S06-S11-01` | `ORGANIZATION_HANDOVER` | Corporate Rubric publisher identity/role mapping; rubric checksum/lifecycle behavior is product-owned | `PENDING_SERVER` |
| `S06-S11-02` | `ORGANIZATION_HANDOVER` | Enterprise audit sink/retention and recovery; immutable Rubric persistence is product-owned | `PENDING_SERVER` |
| `S06-S11-03` | `PRODUCT_TEST` | Real submission consumes approved immutable Rubric revision | `PENDING_SERVER` |
| `S06-S11-04` | `PRODUCT_TEST` | Approved internal corpus and model groundedness where applicable | `PENDING_SERVER` |
| `S07-S11-01` | `PRODUCT_TEST` | Real pinned vLLM and candidate model unavailable in local CI | `PENDING_SERVER` |
| `S07-S11-02` | `ORGANIZATION_HANDOVER` | Corporate TLS/network credentials and firewall; provider endpoint restrictions are product-owned | `PENDING_SERVER` |
| `S07-S11-03` | `PRODUCT_TEST` | Model/trace/logging stack only runs in enterprise | `PENDING_SERVER` |
| `S07-S11-04` | `PRODUCT_TEST` | Tokenizer budget and model-specific decoding/thinking are not verifiable by MockTransport | `PENDING_SERVER` |
| `S07-S11-05` | `PRODUCT_TEST` | Real OOM, concurrency, failover and latency cannot be measured locally | `PENDING_SERVER` |
| `S07-S11-06` | `PRODUCT_TEST` | Actual supply-chain model/OS attestation and legal authorization require enterprise import | `PENDING_SERVER` |
| `S08-S11-01` | `PRODUCT_TEST` | Approved gold-label Persian speech/media/research evaluation corpus, adjudication and versioned reference labels | `PENDING_SERVER` |
| `S08-S11-02` | `PRODUCT_TEST` | Approved internal reference corpus with frozen provenance, approved vLLM/models and SME review | `PENDING_SERVER` |
| `S08-S11-03` | `PRODUCT_TEST` | Approved pinned tokenizer/runtime, measured GPU/context and long documents | `PENDING_SERVER` |
| `S08-S11-04` | `PRODUCT_TEST` | Authorized organization network/IAM/TLS model access and synthetic prompt-injection corpus | `PENDING_SERVER` |
| `S08-S11-05` | `PRODUCT_TEST` | Approved OD-03/04/09/11 decisions and review adjudication | `PENDING_SERVER` |
| `S08-S11-06` | `PRODUCT_TEST` | Stage09/10 worker/controller, authorized staging IAM, encrypted evidence and production-representative database | `PENDING_SERVER` |
| `S09-S11-01` | `PRODUCT_TEST` | Authorized organization staging DB and schema/backup policies, test-only org accounts | `PENDING_SERVER` |
| `S09-S11-02` | `PRODUCT_TEST` | Real internal vLLM, GPU capacity and approved synthetic load | `PENDING_SERVER` |
| `S09-S11-03` | `PRODUCT_TEST` | Approved authenticated protected-text/KMS resolver and scoped service identity integrated in Stage10 | `PENDING_SERVER` |
| `S09-S11-04` | `ORGANIZATION_HANDOVER` | Organization monitoring sink, on-call and alert ownership; queue metrics/robustness stay product-owned | `PENDING_SERVER` |
| `S09-S11-05` | `PRODUCT_TEST` | Approved Stage10 submission API, reviewer policy and signed Rubric | `PENDING_SERVER` |
| `S09-S11-06` | `PRODUCT_TEST` | Production-representative signed images, service secrets, network No-Egress and failure injection window | `PENDING_SERVER` |
| `S10-S11-01` | `ORGANIZATION_HANDOVER` | Corporate IdP, key rollover/revocation and active user lifecycle; JWT verification remains product-owned | `PENDING_SERVER` |
| `S10-S11-02` | `ORGANIZATION_HANDOVER` | Corporate KMS/rotation and retention; encryption, AAD and access checks remain product-owned | `PENDING_SERVER` |
| `S10-S11-03` | `PRODUCT_TEST` | Approved TLS/mTLS reverse proxy, ingress policy, WAF/security headers, sanctioned No-Egress test window | `PENDING_SERVER` |
| `S10-S11-04` | `PRODUCT_TEST` | Approved isolated organization staging DB, RLS/reviewed database role, retention and eventual controlled migration procedure | `PENDING_SERVER` |
| `S10-S11-05` | `PRODUCT_TEST` | Actual internally pinned model/Worker, authorized protected-source resolver, approved candidate Rubric and synthetic gold requests | `PENDING_SERVER` |
| `S10-S11-06` | `PRODUCT_TEST` | Approved reviewer assignment lifecycle, signed reviewer roles, OD-06 workflow and explicit business privacy/review policies | `PENDING_SERVER` |
| `S10-S11-07` | `PRODUCT_TEST` | Production-like load/soak, defined tenant rate/queue quotas and log/metrics/privacy policies | `PENDING_SERVER` |

**Coverage:** 56 unique original IDs, `40` proposed `PRODUCT_TEST`, `16` proposed `ORGANIZATION_HANDOVER`. The sum and uniqueness are checked against the repository's authoritative Stage11 ledger above.

## Immediate GPU-free product checks

- Keep offline Python and isolated PostgreSQL regression suites green (`request validation`, `RS256/JWT`, `AES-256-GCM`, `tenant scoping`, `idempotency`, `Worker leasing/fencing`, `Rubric binding`, `grounded evidence`, `reproducible provisional scoring`).
- Finish operator-facing configuration/runbook and synthetic fixture reproducibility without enabling real inference.
- Once shared GPU becomes available, separately authorize and measure pinned-model tri-domain criterion correctness, human-labeled quality, and full protected API/DB/Worker/LLM/report flow. Do not infer these from synthetic CI.
- Supply the recipient organization with all `ORGANIZATION_HANDOVER` check descriptions and unresolved integration prerequisites, including SSO, keys, network egress enforcement, logging, retention, backup and production monitoring. These items do **not** disappear from the original audit trail.

## Acceptance restriction

Current `Stage11=BLOCKED`, `Stage12=NOT_STARTED`. The original product plan's 56-ID gate and Stage12 requirements have not been silently rewritten; this document proposes which party is responsible for each check under the updated delivery boundary. Product implementation completion and recipient's production certification must be reported separately.
