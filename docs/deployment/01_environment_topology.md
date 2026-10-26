# Stage 04 — Environment Topology and Deployment Preconditions

Status: `PROPOSED_NOT_DEPLOYED`, D-013/OD-13 OPEN. No actual organization DNS, subnet, hostname, address, firewall, Kubernetes/Docker runtime, corporate cert, vault or GPU has been selected or changed. This document records logical isolation, not claimed network evidence.

## Environment-specific placement

| Property | Development | Staging (requires authorization) | Production (requires Stage 11 PASS + Stage 12 approval) |
|---|---|---|---|
| Input | synthetic only | authorized synthetic/de-identified | classified data under approved policy |
| API bind | `127.0.0.1:18080` local (2026-10-24 development port change; pending user-local bind verification) | private ingress behind approved gateway | private ingress behind TLS/IAM gateway |
| DB | not provisioned in Stage 04 | local/isolated Postgres in Stage 05/11 | approved private PostgreSQL cluster |
| Worker/Inference | absent until Stages 09/07 | separate private service identities and network segments | approved isolated service networks and GPU runtime |
| Egress | do not submit confidential data; local app has no outgoing runtime client | firewall default deny, explicit internal allowlist | firewall default deny, DNS/proxy controlled and audited |
| Observability | event-code log, synthetic IDs | approved internal log/metric/audit sink | restricted internal sink, controlled retention |
| Secrets | fake `env://` references in tests | secure injection by approved vault/orchestrator | internal Vault/KMS with rotation/recovery approval |
| Backup | none yet | encrypted/sanitized restore rehearsal | encrypted offline backup, approved RPO/RTO |

## Logical deploy graph (UNVERIFIED)

```text
[Corporate client network] -> [TLS/auth gateway: IAM boundary]
                                  -> [API segment: loopback/container private bind]
                                       -> [PostgreSQL segment (Stage 05)]
                                       -> [Private audit sink]
[Worker segment (Stage 09)] ---------> [PostgreSQL segment]
              |                     -> [Inference GPU segment (Stages 07/11)]
[Controlled import/registry] --------> [Inference artifact storage]
[Protected backup zone] <------------ [PostgreSQL]
[All segments: default DENY internet egress; explicit internal flows only]
```

The initial local application intentionally offers ONLY `/health/live` and `/health/ready`; it has no authentication-enabled product endpoints, no DB, worker or model client. The readiness endpoint tests bootstrap/lifespan only; it must be extended with actual essential dependency checks when those components exist. No security certification is inferred from a private IP validator or YAML flag.

## Deployment preconditions

1. Select platform/host/container constraints (`OD-13`), approved image registry and provenance; provision non-root execution, read-only root where feasible, CPU/memory limits, graceful termination and isolated process identity.
2. Approve TLS gateway/issuer/audience/identity mapping (`OD-07`), certificate chain/service identity, firewall policy, DNS/proxy control, outbound telemetry restriction and internal audit log retention (`OD-08`).
3. Approve encrypted database/backup, retention/legal hold, KMS and disaster-recovery targets (`OD-08/12`) before handling confidential content.
4. Verify signed/offline packages and model artifact SHA-256, legal licensing, SBOM, vulnerability review, registry import and no-auto-download; pin executable versions with hash evidence at approved build boundary.
5. Execute Stage 11 local-to-organization integration, real No-Egress, service auth, TLS, restore, load/E2E and all deferred test ledger entries before Stage 12 release.

## Rollout and rollback proposal

Build immutable approved artifact, sign and scan offline, promote to isolated staging, test health and error redaction with synthetic content, record the exact Git SHA/config hash. Canary or controlled replacement only after the platform is approved. On rollback, restore the previous signed app artifact and compatibility-checked configuration (NO secret values in manifest). Database migrations and model/rubric versions have their own Stage 05/06/12 change plans; never automatically downgrade destructive schema or discard data. Incident triggers: unauthorized egress, identity bypass, secret leak or High/Critical finding -> contain access and block promotion; real operations require explicit organizational authorization.


## Shared-host container network reconnaissance — 2026-10-26 (user observed, read-only)

User reported an **Ubuntu 24.04 shared multi-project host** with a single **RTX 3090 24 GiB**, ~94 GiB host RAM and a ~491 GiB filesystem with 396 GiB free at the observation time. User-local `nvidia-smi` displayed a `VLLM::EngineCore` process using **18,532 MiB of GPU memory** and zero instantaneous GPU utilization; that is **not** proof of inference performance or available load capacity. No model inference, synthetic benchmark, confidential requests, migrations or deployment occurred.

After initial Docker socket `permission denied` for the non-docker-group user, the same user confirmed **sudo-authorized read-only Docker inspection** without granting the account membership in the privileged `docker` group. The reported real container names were `ai-inference-vllm-1` and `shared-postgres-postgres-1` (not `shared-llm` and `shared-postgres` as object names). Postgres: container status **healthy** with only `5432/tcp` shown by `docker ps`, attached to external-named `simorgh-db-net`, a `bridge` network whose `Internal=true`; aliases **`shared-postgres`, `postgres`**. vLLM: container running and bound on host **loopback** `127.0.0.1:8000`, attached to `ai-inference_default` bridge; alias **`vllm`**. `simorgh-db-net` showed only the Postgres container as a member at the time.

User's unauthenticated host-loopback **GET `/health` and GET `/v1/models` both returned HTTP 200**. That establishes *host-side HTTP route availability*, **NOT** successful model generation, exact served model ID, structured output, authentication, internal container-to-container DNS/route reachability, network No-Egress, DB connectivity from the project, TLS/service identity, GPU capacity or cross-project isolation.

**Proposed isolated project placement (not yet deployed):** `/srv/projects/text-evaluation-service/` with its own Compose project, containers, private default network, scoped credentials, per-project Postgres DB/role, and only explicitly approved connections to the two already-existing networks. On `simorgh-db-net`, the scoped database DNS endpoint would be `shared-postgres:5432`; on `ai-inference_default`, the candidate inference DNS endpoint would be `vllm:8000`. DNS aliases only resolve inside networks a client joins; a container's `localhost:8000` is *not* the host's vLLM port. Joining both networks exposes lateral connectivity unless additional controls are approved: an `Internal=true` network is **not** a complete outbound-deny guarantee for a multi-homed app container. Prefer service-specific network identity, service authentication and authorization, resource quotas and protected request/log boundaries before any real use. **Shared Postgres/vLLM configuration, mounts, network membership and secrets are owned by other projects and MUST NOT be changed without separate permission.**

**Program boundary:** Under project decision D-017, this incidental user-submitted **read-only inventory/HTTP observation is NOT a Stage 11 execution or gate PASS**. All real company/model/GPU tests stay `DEFERRED_TO_STAGE_11`, with authorized staging, synthetic data, change approval, resource stop limits and qualified owner. Stage 04 remains `IN_PROGRESS` because actual OSS license/legal signoff and independent raw artifact checks are not complete; Stage 05 remains `NOT_STARTED / NOT_APPROVED`. This note does not decide OD-13 deployment platform formally or grant server deployment permission.
