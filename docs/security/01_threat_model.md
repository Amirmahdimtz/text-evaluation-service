# Stage 04 — Threat Model and Trust Boundaries

Status: `IMPLEMENTED_LOCAL_CONTROLS + PROPOSED_ORGANIZATIONAL_TOPOLOGY` (2026-10-24). Scope: FR-08/09/10, NFR-01/02/03/09/11/14; D-002/D-003/D-017. This is **not** evidence of organization-wide No-Egress, deployed IAM or encryption.

## Data-flow / boundaries

```text
TB-1  Internal client --authenticated TLS--> Approved enterprise gateway/IAM (UNSELECTED)
TB-2  Gateway --authenticated and verified principal--> API (FastAPI)
TB-3  API / Core --scoped DB requests--> PostgreSQL (Stage 05)
TB-4  PostgreSQL durable jobs --> Worker (Stage 09; separate service identity)
TB-5  Worker --approved private TLS--> internal Inference (Stage 07/11)
TB-6  Runtime environment / Secret manager --> process configuration (Vault design OPEN)
TB-7  API / Worker / Model --> sanitized internal logs, audit and monitoring
TB-8  Controlled offline artifact importer --> internal verified registry/storage
TB-9  Encrypted DB snapshot --> approved isolated backup/restore boundary
```

Trust assumptions are explicitly NOT deployments. No business endpoint or external inference client exists in Stage 04. Raw and derived content are `CONFIDENTIAL`; tokens and keys are `SECRET`; actor/org information is `RESTRICTED`. The repository is **public**: never commit real samples, org IPs, credentials, endpoints, datasets or architecture-specific confidential details. All sensitive flows require internal transport, purpose limitation, authorization and organizational approval.

## Threat register

Risk uses qualitative severity before controls; residual acceptance remains with named owner. Every future verification is either local or `DEFERRED_TO_STAGE_11`.

| Threat ID | Threat / trust boundary | Risk | Mitigation and enforcement point | Owner | Verification |
|---|---|---|---|---|---|
| TH-01 | Unauthorized identity at TB-1/2 | CRITICAL | Verified identity required; no caller-supplied org claims; default-deny policy; gateway/SSO selection `OD-07 OPEN` | IAM/Security | Local identity negative tests; corporate SSO Stage 11 |
| TH-02 | IDOR / cross-org via TB-2/3 | CRITICAL | Scoped `is_allowed` owner/assignment/org checks; Stage 05 scoped repository queries; Stage 10 enforcement in API/Core | API/IAM | Local cross-scope matrix; real API/DB IDOR Stage 10/11 |
| TH-03 | Prompt/text/model-response leak via TB-5/7 | CRITICAL | Never log payload/exception; event-only JSON format; model logging off pending runtime validation | Security/AI/SRE | Synthetic-marker test local; internal sink inspection Stage 11 |
| TH-04 | Outbound SSRF/exfiltration via TB-4/5 | CRITICAL | Explicit private-IP-only URL validation, no external endpoints, network deny-all egress and DNS control | Network Security | Local rejected URL tests; packet/DNS proof Stage 11 |
| TH-05 | Secrets leaked via TB-6/7 or Git | CRITICAL | `env://` references only; never log secret values; public-tree review; approved Vault/KMS pending `OD-08` | Security/SRE | Local missing-secret and log tests; real Vault/key audit Stage 11 |
| TH-06 | Unsafe configuration/public bind | HIGH | Strict YAML schema, forbidden extra keys, loopback bind by default, fail startup on invalid env/config | Platform Lead | Local invalid config/startup tests; deployment attestation Stage 11 |
| TH-07 | Dependency/artifact compromise TB-8 | HIGH | Exact package versions; offline preflight, SBOM/signature/hash/license policy; external automatic download forbidden | Supply Chain/Legal/MLOps | Local source review; approved artifact checks Stage 11 |
| TH-08 | Worker replay/concurrent cross-scope mutation TB-3/4 | HIGH | Stage 05 constraints, Stage 09 lease/fencing/idempotency, short sessions | Backend/SRE | Local PostgreSQL concurrency Stage 05/09; real recovery Stage 11 |
| TH-09 | Injection in untrusted evaluation text TB-4/5 | HIGH | Treat input as data, no model tools, verified structured output and evidence | AI/Security | Stage 07/08 synthetic cases; internal model attacks Stage 11 |
| TH-10 | Exposed backup/audit TB-7/9 | HIGH | Restricted encrypted backups, no raw logging, approved retention, restore and legal hold `OD-08/12 OPEN` | Security/Data Steward/SRE | Stage 11 restore/encryption test; Stage 12 approval |
| TH-11 | Unauthenticated health/info disclosure TB-2 | MEDIUM | Only static liveness/readiness status; disable OpenAPI/docs by default; never return topology | API/SRE | Local HTTP smoke / no-docs checks |
| TH-12 | Unauthorized artifact imports/models TB-8 | HIGH | Offline signed manifest with SHA-256, provenance/license/approval, internal-only storage | MLOps/Security/Legal | Stage 11 artifact gate |

## Controls actually implemented in Stage 04

`src/infrastructure/security/policy.py`: immutable synthetic Identity/ResourceScope, explicit permissions and org/ownership checks; `validate_internal_endpoint()` uses IP literals in RFC1918/ULA and development loopback, HTTPS outside development, and forbids user-info, fragment, query and missing port. This is **application policy, not firewall**. `src/infrastructure/security/secrets.py`: strict env reference and failure codes; real Vault not selected. `safe_logging.py`: allowlisted event codes only, no arbitrary message/exception interpolation. `src/host/app.py`: correlation UUID generated server-side; no response exception detail; static health; OpenAPI/docs disabled; loopback server; no access logging in controlled entrypoint. `ConfigReader`: strict schema; invalid settings fail closed. Stage 04 does not store text or accept evaluation requests.

## Residual risks / explicit blockers to deployment

`OD-07`: IdP, trusted proxy, token verification, service-to-service identities, reviewer delegations, exact 403/404 policy. `OD-08`: formal data class, data-at-rest encryption, retention/deletion/legal hold, backups and Vault/KMS. `OD-12`: operational SLO/RPO/RTO/limits. `OD-13`: firewall/mTLS/dedicated inference identity and network topology. Public repo R-13 persists. No approved load limits or retention durations are invented. Any production exposure before IAM, network segmentation and secure artifact verification is forbidden. Stage 04 local completion is not Stage 11/12 security approval.
