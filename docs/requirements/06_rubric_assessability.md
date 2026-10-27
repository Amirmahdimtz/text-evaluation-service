# Stage06 Rubric Assessability and Publication Boundary

**Source of candidate criterion names, weights, anchors, instructions, evidence requirements and applicability:** [Stage01 Rubric Catalog](02_evaluation_rubrics.md) (18 criteria, three evaluation domains). All of these policy values are `PROPOSED`; no SME/Customer/business-approved publication is claimed.

## Candidate technical contract

- Each Rubric is `rubric-candidate-v1`, `approval_status=PROPOSED`, has a nonempty stable `code` and `candidate-X.Y` version, exactly 6 scored anchors **0..5** per criterion and integer total weight **100** across a domain. `required` is strictly boolean. Duplicate criterion codes and mismatched domains are rejected.
- Each criterion must include: code, name, operational definition, positive integer weight, required flag, six observable score-anchor descriptions, evaluation instructions, evidence requirements and applicability rules. No criterion may be scored without actual valid evidence. Structured outputs in later stages must distinguish `assessed`, `not_assessed` and supported `not_applicable`.
- Candidate coverage semantics remain placeholders: `insufficient_evidence = not_assessed`, `non_applicable = record_explicit_justification`, `required_missing = flag_for_human_review`. **No final coverage threshold, rounding, denominator or required-result publish policy** has been approved (OD-03/04/09/14). The system must not invent them.
- Version checksum: SHA-256 over UTF-8 JSON with sorted dictionary keys, no insignificant spacing and original Unicode retained, produced from strictly validated candidate model. A consumer validates checksum and ID/type/version before accepting a Published test snapshot.
- Technical state machine on synthetic isolated PostgreSQL: `draft → published → retired`. This is an infrastructure test of state transitions. Stage05 DB trigger prevents modifying or deleting Published/Retired contents; old Evaluation rows remain linked by immutable foreign key. New criteria or weights always require a **new** version.
- Publishing in this implementation is **not wired to an HTTP route**, and Stage05 DB engine enforces `TES_ENVIRONMENT=development`, PostgreSQL loopback and a `tes_stage05_` database. The `actor_id` passed in tests is synthetic. Corporate publisher IAM, approval workflow and any real Rubric release are blocked until Stage10/11 and final SME/business sign-off under D-015/OD-03/06/07/08.

## Applicability and abstention boundaries by domain

| Domain | Assessable **from supplied authorized text** | Not assessed / forbidden without additional authorized evidence |
|---|---|---|
| Speech | Coherence of argument, textual structure, clarity, writing and text-supported reasoning using exact original spans | Recording/speaking performance without audio; STT errors as automatic text weaknesses; political opinion conformity; audience suitability without verified audience information |
| Media | Written tone and message clarity, writing quality, textual structure and evidence-backed audience-language matching | Campaign reach, audience response, conversion/real-world effectiveness with no measured analytics; approved style/channel/audience suitability with no corresponding verified metadata |
| Research | Internal coherence, explicit methodological description, text-supported reasoning, academic writing, formal citation consistency | Existence/quality of external references without approved trusted corpus; factual truth/experiment reproducibility without verification; novelty without authorized, version-pinned corpus or SME review |

The Stage01 criterion-level `applicability_rules` govern more specific cases. Missing evidence must not silently become a score of zero. Political/organizational opinion conformity is not a scoring criterion. The model must never browse or send confidential text to a public provider. No internal corpus is implemented or approved at Stage06.

## Catalog and version inventory (synthetic fixtures only)

| Evaluation type | Candidate code | Version | Criteria | Total weight | Status |
|---|---|---|---:|---:|---|
| `speech` | `speech_quality` | `candidate-0.1` | 6 | 100 | `PROPOSED` |
| `media` | `media_quality` | `candidate-0.1` | 6 | 100 | `PROPOSED` |
| `research` | `research_quality` | `candidate-0.1` | 6 | 100 | `PROPOSED` |

Authoritative **test-only** fixtures: [stage06_candidate_rubrics.json](../../tests/fixtures/stage06_candidate_rubrics.json). The fixtures copy the Stage01 names, weights, required flags, definitions and 0–5 anchor texts; their JSON packaging, provisional coverage values and synthetic IDs are implementation conventions only. They are **not** loaded into any production/shared database as a migration or at application startup.

## Security and ownership

- A future business submission must resolve an exact Published and organization-scoped Rubric version through Core Service and persist its immutable `rubric_version_id` using Stage05's composite tenant/type FK. `RubricService.resolve_published_async` returns an immutable binding with version/checksum for that purpose. This stage does **not** add a user-facing submit endpoint (Stage10).
- Stage06 publication/retirement is conditional on a trusted caller and test-only DB. Genuine manager permission, SSO, delegated approval, role/event audit sink, retention and `OD-06` admin endpoint scope remain OPEN. These may not be circumvented by unverified user input.
- Keep all data synthetic; verify real on-premise behavior only under D-017 in Stage11 and release signatures/SME approval only under D-015 in Stage12.
