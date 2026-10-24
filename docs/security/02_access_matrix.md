# Stage 04 — Provider-independent Access Policy and Matrix

Status: `PROPOSED_ROLE_MATRIX / IMPLEMENTED_POLICY_PRIMITIVE` (OD-07 OPEN, D-009 OPEN). The following are *candidate* roles, NOT existing corporate IdP roles. D-017 authorizes fixture validation only; actual identity integration belongs to Stage 11 and business routes to Stage 10.

## Identity and scope contract

An authenticated principal has immutable `user_id`, `organization_id`, an explicitly granted permission set, and resource assignments. These fields must be mapped from a **cryptographically verified** identity context at the organization-approved gateway or backend (SSO and claims mapping not yet selected). Never trust request body, `X-User`, `X-Org` or unverified bearer claims. Missing actor/organization, failed authentication, unknown operation or failed assignment: DENY. Service-to-service identity must have dedicated credentials and least-privilege permissions; no anonymous trust in an internal network. A resource may be read only by same-organization owner or explicitly assigned reviewer; reviewer feedback additionally requires assignment and separate permission. No implicit superuser or cross-organization role.

## Candidate authorization matrix

| Candidate role | `evaluation:submit` | `evaluation:read` | `feedback:create` | `rubric:manage` | `metrics:read` |
|---|---|---|---|---|---|
| Owner/submitter | Own authorized org | Owner only | DENY | DENY | DENY |
| Assigned reviewer | DENY by default | Explicit assignment, same org | Explicit assignment, same org | DENY | DENY |
| Rubric curator | DENY | DENY | DENY | Conditional, approved scope/workflow | DENY |
| Security auditor | DENY | DENY | DENY | DENY | Conditional sanitized only |
| Service operator | DENY | DENY | DENY | DENY | Conditional sanitized only |
| Anonymous/invalid identity | DENY | DENY | DENY | DENY | DENY |

These roles are **not automatically constructed** from permissions. Callers require verified grants; none is assigned by default. The Stage 04 `is_allowed()` primitive validates permissions, same organization, owner/assignment for read, assignment for feedback, and denies unknown operations. It intentionally does not implement full corporate RBAC, admin approval, SSO parsing or repository query scoping yet. `rubric:manage` and `metrics:read` must have approved operation-specific scope and auditing before routes are exposed; absent routes cannot be abused in Stage 04.

## Enforcement contract by stage

- Gateway/IAM (Stage 11): validate token issuer, audience, signature, expiry, revocation/session policy and secure forwarded identity; reject anonymous by default. Role mapping `OD-07` pending.
- Stage 04: provider-neutral policy functions with local synthetic identity fixture. `False` means no permission, never infer from group name or supplied UUID.
- Stage 05: all DB read/write queries must include trusted `organization_id` and owner/assignment predicates; API-only checks are insufficient.
- Stage 10: FastAPI controller obtains trusted principal from verified boundary, Core enforces policy, and repository scopes queries. Uniform 401 for no identity, 403 or non-oracular 404 for unauthorized resource per `OD-07` selection. Do not disclose resource existence through timing or errors.
- Stage 11: internal SSO, gateway trust chain, service account impersonation, IDOR/cross-org E2E and audit sink verified with authorized identities.

## Local security test oracles

Unauthenticated actor -> deny. Guessed resource UUID from same org/non-owner -> deny. Different org even assigned -> deny. Assigned reviewer same org with `evaluation:read` -> allow read. Reviewer without `feedback:create` or without assignment -> deny feedback. Unknown operation -> deny. Missing org -> deny. Real IAM and tenant policies require OD-07 approval; failure is always deny, with error body free of protected identifiers/text.
