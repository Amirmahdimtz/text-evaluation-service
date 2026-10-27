# Stage06 — Rubric Security & Organization Integration Tests Deferred under D-017

All entries `PENDING_SERVER / DEFERRED_TO_STAGE_11`, **NOT PASSED**. The local Stage06 schema, validation, PostgreSQL publication-race, version pinning and immutable trigger tests have already been executed and PASSED independently in synthetic GitHub Actions [run 40519890093](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40519890093); none of these local tests are falsely deferred.

| ID | Domain | Execution owner | Required approval/environment | Acceptance oracle |
|---|---|---|---|---|
| S06-S11-01 | Actual corporate Rubric publishers, SSO/service IAM, least privilege and tenant scope | IAM + Security + Rubric Curator | Selected trusted verified IdP, configured secured principal mapping, staging-only accounts | Unauthorized Draft/Publish/Retire, cross-tenant reads and spoofed actors denied; audit actor sourced from verified identity, not body/header |
| S06-S11-02 | Rubric lifecycle audit, retention, tamper resistance and replay | DBA + Security + Data Steward | Approved staging database and secured internal audit sink, retention/backup/KMS policy OD-08 | All attempted and completed transitions auditable without business text; real audit retention/recovery and historical immutable snapshots verified |
| S06-S11-03 | Real submission consumes approved immutable Rubric revision | AI Quality + API Security + DBA | Stage08/10 service with approved staging, no real classified data without authorization | Evaluation pins exact organization/type/version/checksum; retire/new version never silently alters historical report; no cross-org substitution |
| S06-S11-04 | Approved internal corpus and model groundedness where applicable | AI Quality + Data Steward + Domain SMEs | Authorized reference corpus, vLLM, approved internal data and Stage11 calibration protocol | Applicability/abstention consistently avoid false factual verification or novelty claims; evidence provenance and model-driven rubric choice cannot bypass version binding |

**Final SME/business authorization:** OD-03, OD-04 and OD-06 remain OPEN/PROPOSED; under confirmed D-015, only a qualified final Stage12 sign-off can authorize actual Official/Business-Approved Rubrics. The synthetic `status='published'` rows in Stage06 CI refer to technical persistence states in an ephemeral test database, **never to sanctioned production Rubrics**.

**No operational authorization:** This ledger grants no permission to access Simorgh shared PostgreSQL, enterprise IAM, corporate model server, real confidential text, production keys/networking or external AI. Stage07 NOT_STARTED; the current local stage verdict is documented in [Stage06 validation](06_stage06_rubric_validation.md).
