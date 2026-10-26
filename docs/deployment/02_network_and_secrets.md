# Stage 04 — Network, TLS, Secrets and Supply-chain Boundary

Status: `PROPOSED_POLICY + LOCAL_VALIDATORS`, **NOT DEPLOYED**. Related: D-002/D-017; OD-07/08/12/13. All addresses below are protocol examples, not organizational endpoints.

## Port / connectivity matrix

| From -> To | Direction | Intended protocol / example port | Allowed when | Authentication and confidentiality |
|---|---|---|---|---|
| Client -> gateway | Ingress | TLS 443 (proposed) | Verified internal principal and rate limit | Approved SSO/TLS |
| Gateway -> API | Ingress | private HTTP/TLS (port OPEN) | Only gateway identity, no bypass | TLS/mTLS or approved equivalent |
| API -> PostgreSQL | Internal | Postgres TCP 5432 (default example; OPEN) | Stage 05 scoped DB credentials | Internal TLS, least-privilege DB role |
| Worker -> PostgreSQL | Internal | Postgres TCP (OPEN) | Stage 09 identity | Internal TLS, restricted role |
| Worker -> Inference | Internal | HTTPS 443 (illustrative; OPEN) | Stage 07 private endpoint approved by Security | Approved mTLS/service auth, no external redirects |
| Runtime -> Vault/KMS | Internal | approved internal TLS (OPEN) | Stage 11 approved service identity | Least privilege, audit, rotated credentials |
| API/Worker -> audit sink | Internal | OPEN | Metadata-only, approved sink | TLS/auth and access control |
| All workloads -> public DNS/HTTP(S)/telemetry/model hubs | Outbound | any | **DENY** | Firewall, DNS and proxy enforcement, Stage 11 packet verification |
| Offline artifact importer -> internal registry | Controlled import | OPEN | Signed manifest, license, hash and human approval | Offline transfer, quarantined scan |

Actual egress must be denied by an organizational network policy, not just a configuration flag. Deny DNS resolvers outside approved network. Do not follow redirects to external IPs; allowlist destination, certificate identity and SNI; no internal metadata IP access. The Stage 04 validator accepts only literal RFC1918 IPv4 or ULA IPv6 with HTTPS, and development loopback HTTP; it does not perform DNS lookups and cannot enforce routes, NAT, redirects or firewall rules.

## Secret injection and lifecycle

A reference `env://VARIABLE_NAME` only names a runtime-injected variable. `SecretResolver` uses no persistent file and fails closed on invalid/missing references with redacted code; tests use fake synthetic values only. Environment injection into a production process is conditional on organization security approval; no actual Vault/KMS selected. Secret values must never appear in YAML, code, argv, Docker layer, Git, audit, logs, error response or screenshots. Host environment, file permissions and log collection are trusted only after Stage 11 verification. Replace/create VaultService *only* once approved corporate API exists; do not invent a Vault protocol or path. Require restricted process identity, access control, rotation, revocation, audit and recovery.

## Artifact security and SBOM

Stage 04 dependency manifest pins direct dependencies to exact versions, but does NOT constitute a hash-locked transitive dependency graph or legal license clearance. Prior to organizational install: obtain approved internal wheelhouse including transitive wheels, hash-check each artifact, scan vulnerabilities and licenses, produce SBOM and provenance, use offline installation (`--no-index`) and ban dependency and model auto-download at runtime. A public `pip` or GPU model download into confidential infrastructure is not authorized. Existing Stage 03 model IDs remain CANDIDATE. No real artifact download has occurred.

## Stage 11 verification oracles (recorded separately)

Deny public DNS and outbound TCP/HTTP, confirm packet traces and proxy/firewall logs have zero prohibited connections while synthetic sentinel passes through full E2E; verify internal gateway/SSO/service identities, Vault/KMS TLS/auth/rotation; inspect application/gateway/worker/model/log sinks for leaked sentinel; scan model and package manifest hashes/licenses; confirm encryption and restore. All require Infrastructure+Security approval, isolated environment, resource limit and human owner. Each is `DEFERRED_TO_STAGE_11`, not PASS. No firewall, corporate secret, production environment or model weight was touched in Stage 04.


## 2026-10-24 independent dependency review amendment

The previous local environment resolved `starlette==0.50.0`, which is within the affected range of publicly reported **CVE-2026-54283 (HIGH)**. Requirements now explicitly pin `fastapi==0.148.0` with `starlette==1.9.0` (plus dev-only `httpx2==2.16.0`) and the safety checker rejects known-vulnerable Starlette pins. Release/PyPI metadata review supports this dependency range, but newly resolved binaries were **not installed/tested** by the assistant due to sandbox package-index restrictions; they require a clean Windows environment rerun. `scripts/verification/audit_stage04_dependencies.py` inventories the installed dependency closure, license metadata and installed RECORD SHA-256, **without external requests**; this is NOT equivalent to a validated vulnerability scan, standard approved SBOM or trusted upstream artifact hash. Full accepted lock/wheel hash manifest, offline package source provenance, business/legal license approvals and package CVE audit are still outstanding for Stage 04's local supply-chain gate. See [independent readiness review](../verification/04_stage04_independent_review.md). No production, Vault or corporate network access has been used.


## Stage 04 local package supply-chain tooling (2026-10-24)

See [runbook](../verification/04_stage04_supply_chain_runbook.md). `requirements-audit.txt` pins dedicated local scanning tools `pip-audit==2.10.1` and `cyclonedx-bom==7.5.0`; neither is a runtime dependency. `run_stage04_supply_chain.ps1` targets the user-approved Windows `.venv-review`, records the installed 27-package closure, performs strict public-advisory scan when permitted, generates a CycloneDX 1.6 SBOM and downloads exact-version wheelhouse to a **local Git-ignored** evidence directory. `review_stage04_supply_chain.py` enforces coverage, wheel SHA256 and optional independently sourced PyPI release digest checks, and explicitly reviewed SPDX license decisions; **no business text or real protected artifact is submitted**. 15 synthetic tests PASS in an isolated assistant Python 3.13 environment; network package/SBOM execution on the actual user Windows environment is **NOT_RUN** in this interaction. PyPI-reported SHA256 matching does **not** imply a signed publisher provenance attestation; model/organization artifacts and internal registry verification belong to Stage 11. Existing Stage 04 `IN_PROGRESS`, no Stage 05 entry.


## 2026-10-26 — Shared Docker network aliases and security-boundary caveats

**Read-only evidence:** existing `simorgh-db-net` = Docker bridge `Internal=true`, currently attached Postgres container alias `shared-postgres` / `postgres`; separate `ai-inference_default` bridge with vLLM alias `vllm`. Host publishing for vLLM is loopback-only `127.0.0.1:8000`; Postgres had no host-published `5432`. Host-local unauthenticated `GET /health` and `GET /v1/models` returned HTTP 200. API model response body, actual generation and container-level access policies are **UNVERIFIED**.

**Not-yet-authorized routing proposal:** after appropriate stage/approval, a dedicated project Compose could join specifically named **existing external networks** to resolve `shared-postgres:5432` and `vllm:8000`. A private Compose network remains recommended for service-to-service flows; joining the shared bridges also creates lateral exposure, so least-privilege identity, DB grants and egress policies must be applied and independently tested. `Internal=true` on one network is not an outbound firewall for a multi-network container. Never mount Docker socket into app; never add untrusted user to docker group as a routine workaround; do not publish shared vLLM/DB on `0.0.0.0` without change approval. **No exact connection string, secret, live model prompt, source configuration or service changes were produced.** Actual No-Egress, TLS, service auth and connection tests stay `DEFERRED_TO_STAGE_11` per D-017.


## Read-only model alias differentiation — 2026-10-26

On `ai-inference_default`, current Docker membership contains only `ai-inference-vllm-1`; `shared-llm` was emitted instead by a separate `GET /v1/models` query and is an API model ID, **not** a container alias. When a project integration is later authorized, the candidate network path is `http://vllm:8000/v1` **from a container attached to that network**, using served ID `shared-llm`. Host-loopback status observations do not prove reachability from the future project, authenticated service transport, No-Egress, private output logging or actual Qwen3 model provenance. Stage11 controls remain deferred; no network/services modified.
