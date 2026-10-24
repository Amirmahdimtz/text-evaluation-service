# Stage 04 — Environment Topology and Deployment Preconditions

Status: `PROPOSED_NOT_DEPLOYED`, D-013/OD-13 OPEN. No actual organization DNS, subnet, hostname, address, firewall, Kubernetes/Docker runtime, corporate cert, vault or GPU has been selected or changed. This document records logical isolation, not claimed network evidence.

## Environment-specific placement

| Property | Development | Staging (requires authorization) | Production (requires Stage 11 PASS + Stage 12 approval) |
|---|---|---|---|
| Input | synthetic only | authorized synthetic/de-identified | classified data under approved policy |
| API bind | `127.0.0.1:8000` local | private ingress behind approved gateway | private ingress behind TLS/IAM gateway |
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
