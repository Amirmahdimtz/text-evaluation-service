# Security, Privacy and Data Policy — Stage 01

> **Status: PROVISIONAL_SECURITY_SPECIFICATION** · Date: 2026-10-21 · Formal employer/SME acceptance is deferred to Stage 12 (`D-015`); mandatory authorization for protected operations remains in force.  
> Baseline: Implementation Plan §§1.4,3,4,6,7,10/Stage 01 and Architecture Guide. This is a **control requirements specification**, not evidence that controls already exist. Organization-specific IAM, cryptography, retention, topology and RTO remain OPEN.

## 1. Binding confidentiality commitments and trust boundaries

- `SEC-01 / CONFIRMED (D-002)`: All AI inference for confidential text must operate **inside an organization-authorized network and infrastructure**. Do not send original text, segments, prompts, responses, embeddings or derived sensitive content to any external AI Provider. No external tools, internet, SQL or arbitrary code execution for the model.
- `SEC-02 / CONFIRMED (FR-10)`: Treat all user-submitted evaluation text and associated results as **confidential by default** pending formal classification. Security labels below are candidate business policy, not approved tenant taxonomy.
- `SEC-03 / MUST`: Deny-by-default egress, network isolation of the Inference Server, only explicitly approved internal service-to-service flows, test with packet/DNS/log evidence. Internal URL alone is not proof of isolation.
- `SEC-04 / MUST`: Restrict prompt/response, raw text and evidence from ordinary application/worker/model/gateway logs, tracing, error messages, analytics and Git. Do not copy raw samples to public issue trackers, hosted observability, personal laptops or third-party notebooks.
- `SEC-05 / MUST`: Authentication, RBAC **and per-resource Ownership/Org Scope** at API, Service and Repository query/read/write layers; resource UUID is not a credential.
- `SEC-06 / MUST`: Encryption in transport, storage and backups with authorized internal key management; concrete algorithms/certs/rotation intervals depend on organization policy (`OD-08/13`).
- `SEC-07 / MUST`: Every model output is untrusted; parse and validate structured output, verify evidence against original text, reject injected commands and unsupported factual claims.

**Proposed trust-boundary diagram, not deployed infrastructure:**

```text
Authorized internal user / internal service
       -> approved internal TLS Gateway + Identity/RBAC
       -> FastAPI API -> authorized PostgreSQL
       -> durable internal Job -> Internal Worker
       -> restricted internal Inference Server (local model artifact)
                 [deny external egress for confidential data]
  Secure Audit / Metrics Sink (metadata only, no original text)
  Encrypted Backup / Restore Environment (authorized)
```

No assumption is made that a specific Gateway, SSO, Vault, Storage, GPU, topology or Kubernetes cluster exists. Architecture must be verified in Stage 02–04.

## 2. Data classification and inventory

| Data class (candidate) | Examples (no real values) | Default requirement | Decision |
|---|---|---|---|
| `CONTENT_CONFIDENTIAL` | Original text, chunks, transcript, user-provided article | Restricted access, encryption, never public/log/external provider | Classification hierarchy `OD-08` OPEN |
| `DERIVED_CONFIDENTIAL` | Criterion reason, evidence quotes/offsets, weaknesses, generated recommendations, model prompt/response, feedback | Treat as same or higher sensitivity than source pending Security review | `OD-08` |
| `IDENTITY_RESTRICTED` | Owner ID, org ID, reviewer, access context, audit actor | Minimal fields, scope enforcement, retention rules | `OD-07/08` |
| `CONTROLLED_INTERNAL` | Published Rubric version, prompts, model hash, job error codes, sanitized metrics | Restricted modification and internal integrity; public release decision separate | `OD-08/13` |
| `PUBLIC_DOCUMENTATION` | This project’s generic requirement documents without internal addresses, secrets or sample content | May be stored in **public** GitHub repository only after content safety checks | Repo exposure recorded as R-13 |

**Data minimization:** Only approved context metadata and source text needed for evaluation. Avoid unnecessary personal identifiers, access tokens, third-party URLs, location/IP retention, prompt tracing and full stack-trace exposure. A derived report can reproduce sensitive excerpts; never treat it as automatically declassified. Embeddings, caches, tokenization artifacts and temporary files are also within confidential data scope if used.

## 3. Authentication, authorization, and ownership

**AuthN (`SEC-IAM-01`):** Verify issuer/audience/signature/expiry/revocation policy for tokens at the authorized trust boundary. Fail closed on absent/invalid identity. Choice of organization SSO/IdP, claims and session policy = `OD-07 OPEN`.

**AuthZ (`SEC-IAM-02`):** Default deny, least privilege, scoped resource authorization for submit/read/feedback/rubric administration and operational functions. `user_id`/`org_id` from verified authorization context only; never trust an arbitrary request body field. Enforce scope in repository queries and business workflow, not only the HTTP path. Log authorization decisions minimally without text.

**Candidate permission matrix — NOT APPROVED:**

| Capability | Submitter/owner | Domain reviewer | Rubric curator | Security auditor | Service operator |
|---|---|---|---|---|---|
| Submit own evaluation | Allow within authorized scope | Conditional | Conditional | No by default | No by default |
| Read full own text/result | Own scoped | Assigned scoped | No by default | No by default | No by default |
| Read another unit's text | Deny | Deny unless explicit scoped grant | Deny | Deny | Deny |
| Provide reviewer feedback | No by default | Assigned scoped | No by default | No by default | No |
| Draft/Publish/Retire Rubric | No | Review only | Conditional per approval workflow | Audit only | No |
| View sanitized operational metrics | No | No | No | Conditional | Conditional |
| Manage identity/retention/deletion | No | No | No | Conditional governance | Conditional approved runbook |

Roles, cross-unit delegation, break-glass access and tenancy hierarchy require Business/IAM/Security approval (`OD-07`). Enforce IDOR test using guessed UUID and cross-tenant aliases; security-safe `403` vs `404` policy is OPEN.

## 4. Lifecycle, retention and deletion

| Lifecycle step | Required policy/technical control | Open decision and owner |
|---|---|---|
| Intake | Validate encoding/length/allowlisted metadata; classify before persistence; authenticated scope | Input formats `OD-01/02` — Product Owner/Data Steward |
| Processing | Authorized internal-only route; limited memory and concurrency; bounded worker retries | Isolation/TTL/caching `OD-08/10/13` — Security/SRE |
| Storage | Protected source text/reference, results, rubric provenance, feedback, access checks | Encryption method/keys `OD-08` — Security |
| Report retrieval | Resource-scoped access, safe response filtering and audit | Sharing/pseudonymization `OD-07/08` — IAM/Security |
| Active retention | Per-class time and legal hold definitions; explicit retention start/end events | **No period approved** `OD-08` — Legal/Data Steward |
| Deletion | Secure deletion or crypto-shredding across DB, caches, replicas, indexes, search, backups and audit exceptions; verifiable request workflow | Scope, soft/hard delete, right to delete, timeframes `OD-08` — Legal/Security |
| Backup | Encrypted isolated backup; access and restoration authorization, retention and rotation | Frequency, storage site and expiry `OD-08/12` — SRE/Security |
| Disaster recovery | Test authorized restore with sanitized or approved data, integrity/scope checks and incident notification | RPO/RTO targets `OD-12` — Business Owner/SRE |
| Dataset & evaluation | Provenance, consent/legal authorization, labeled copies with access limits, split isolation | Sample size, holdout lifecycle `OD-14` — Data Steward/AI Lead |

**Do not implement automatic destructive deletion or purge yet.** No unapproved time-based TTL may be assumed. Determine retention/backup conflict resolution and legal hold requirements in signed policy first. Audit events may need a separate preservation policy.

## 5. Logging, monitoring and audit evidence

**Allowlist (candidate):** timestamp UTC, correlation_id, actor surrogate, authorized org scope ID, action name, resource opaque ID, criterion code, status transition, model/rubric revision identifiers, safe error codes, performance counters, audit integrity metadata. Avoid inference from detailed metric labels that reveal source content.

**Denylist for ordinary logs/audit/traces/telemetry:** raw original text, quoted evidence, context metadata containing text, entire prompt, generated response, authentication headers, bearer tokens, secrets, connection credentials, stack trace objects that stringify payloads. Scrub exceptions at API/Worker/DB/Inference and gateway; limit log-access RBAC and audit retention.

**Audit-worthy events:** authentication failures/suspicious access, authorized result read, feedback created/edited, rubric publish/retire, policy/admin changes, data export/deletion (only if approved), privileged access/break-glass, job state violations and failed egress attempts. Audit trail tamper resistance, sinks, retention and review cadence `OD-08` OPEN. Avoid logging per-criterion text fragments. Correlation ID must not encode personal data.

## 6. Encryption, secrets, networking and supply chain

- **In transit:** TLS for approved client paths, internal service TLS/mTLS per threat model; exact certificate identity, CAs and rotation OPEN.
- **At rest:** DB/volume and encrypted backup key policy; restrict keys to organization-approved KMS/Vault; no hardcoded tokens or secrets in repo/config.
- **Network:** explicit firewall/DNS/proxy egress allowlist; internet egress for Runtime/Worker restricted; prevent external telemetry and auto model downloads; verify packet traces and request destinations in Stage 04/11.
- **Inference:** model artifacts, tokenizer, dependencies and licenses acquired through approved internal workflow with checksums and provenance; candidate runtime `vLLM` and `Qwen3-14B` are **not** approved.
- **Supply chain:** dependency pinning/review, known-vulnerability scan and offline start, artifact SHA verification, container registry trust; exact CI/deployment platform depends on repository/infrastructure review.
- **Availability:** protect API/DB/Model against oversized text, resource exhaustion and cross-scope idempotency collisions through quotas, bounded retries, admission/backpressure; limits require load tests and `OD-12`.

## 7. Threat scenarios and test oracles

| ID | Threat | Required mitigation / oracle | Owner; stage |
|---|---|---|---|
| TH-01 | Prompt injection in quoted source text | Treat input as data; forbid user text to override rubric/system policy; no model tools or internet; adversarial tests | AI Lead + Security; 07/08/11 |
| TH-02 | IDOR / cross-tenant leakage | Deny unauthorized owner/unit read/write/feedback and indistinguishable response policy | IAM + Security; 04/10/11 |
| TH-03 | Prompt/response leaked by model server logs | Turn off/truncate payload logging; inject synthetic marker, inspect all internal sinks | Security + SRE; 04/07/11 |
| TH-04 | External endpoint/telemetry / artifact download | Network deny-by-default; DNS and packet trace demonstrate no prohibited destination | Network Security; 04/07/11 |
| TH-05 | Fake evidence or invented scientific truth | Verify quote spans, schema and unsupported claims; abstain/route to review | Research SME + AI Lead; 08/11 |
| TH-06 | Worker concurrency/replayed job overwrite | Atomic claim, fencing token, idempotency; simultaneous worker and late commit tests | Architect/SRE; 05/09/11 |
| TH-07 | Secret exposure through repository/log | Secret scanner, safe examples, restricted credentials and redaction tests | Security; all stages |
| TH-08 | Backup/media exfiltration or key compromise | Encrypt backup, IAM, approved restore and key rotation drill | Security/SRE; 04/11 |
| TH-09 | Sensitive data in public documentation | No original organizational samples/IPs/accounts; review staged diff before Git push | Technical Lead/Security; Stage 01 |
| TH-10 | Unauthorized use of Golden Dataset | provenance/consent approval, isolated storage, holdout restrictions, audit | Data Steward/AI Lead; 01/03/11 |

**Prompt injection tests:** synthetic test texts may contain requests to ignore scoring rules, emit credentials, call HTTP endpoints, or assign 5/5. Expected: evaluator treats these as quoted content, does not execute them and does not alter policy. This is a specification, not executed model-security evidence.

## 8. Security open decisions and mandatory gates

| Decision | Required answer | Approver |
|---|---|---|
| `OD-07` | IdP/SSO, claims, roles/ownership, unit hierarchy, service identities, delegated reviewer access, 403/404 | IAM Owner + Product Owner + Security |
| `OD-08` | Data classification, legal basis, retention/deletion, log/audit policy, encryption & key rotation, backup | Security/Privacy + Legal/Data Steward + SRE |
| `OD-12` | SLA/SLO, RPO/RTO, incident escalation, recovery/availability requirements | Product Owner + SRE |
| `OD-13` | Approved Datacenter/GPU/network trust boundary, artifact import, outbound policy, runtime | Infrastructure + Security |
| `OD-14` | Golden Dataset access/label privacy, scientific claim constraints, metrics thresholds | SMEs + Data Steward + AI Lead |

**Gate now:** Required security controls are **documented only**, not configured or proven. Stage 01 documental gate `S1-G03` has passed documentation review; formal employer acceptance is **DEFERRED_TO_STAGE_12**, not `S1-G06` or a Stage 01 blocker (`D-015`). **Operational prerequisite:** authorization and enforced safeguards must exist *before* access to real confidential data, credential changes, destructive operations or Production deployment. Operational No-Egress, restore, encryption, model logging and IDOR tests are `PENDING_SERVER` in Stages 04/10/11; none are PASSED.

Related requirements: FR-01/06/07/08/09/10/11/12; NFR-01..14. See [product](01_product_requirements.md), [acceptance](03_acceptance_criteria.md), [open decisions](05_open_decisions.md).

## Stage11 implementation clarification — minimal dependencies, same security guarantees (2026-10-31)

The confidentiality obligations `SEC-01..07` and tenant/resource scope are **unchanged**. A standard production-capable deployment does **not** inherently require a newly developed Vault/KMS service or SSO server. The actual controls required are trusted token issuance/validation and revocation or equivalent short-lived-token policy, secure key custody/versioning/rotation, authenticated encrypted transit where a trust boundary exists, encrypted content and backups, verified Deny-by-default No-Egress, and proven redaction/isolation.

Existing `SignedIdentityVerifier` (RS256) and `EncryptedContentService` (AES-256-GCM with authenticated context) should be reused if approved. Current `SecretResolver` accepts `env://` references to injected environment variables, **not a certified KMS integration**. The existing ciphertext design does not independently prove safe historical decryption across key rotations. Those lifecycle controls must be designed and exercised before any protected rollout. A single host with strict loopback isolation may omit redundant per-hop mTLS only when its trust boundary is actually verified. A public/client-facing gateway must use approved TLS and authentication; no plaintext cross-boundary path is accepted.

Technology choices here remain **`PROPOSED`**, not proof that server settings, No-Egress, corporate key or IAM policies are implemented. See [pragmatic baseline](07_pragmatic_stage11_baseline.md) and [blockers](../verification/06_release_blockers.md). Stage11 remains `BLOCKED`.
