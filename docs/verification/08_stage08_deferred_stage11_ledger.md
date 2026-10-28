# Stage08 — D-017 organization integration / golden-quality test ledger

All items `PENDING_SERVER / DEFERRED_TO_STAGE_11`, **not PASSED**. Mandatory locally reproducible synthetic scoring/validation/offset tests are already PASS in [run 40646409387](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40646409387), so they are NOT improperly deferred.

| ID | Owner | Required enterprise resources and approval | Acceptance oracle |
|---|---|---|---|
| S08-S11-01 | AI Quality + SMEs | Approved gold-label Persian speech/media/research evaluation corpus, adjudication and versioned reference labels | MAE/Agreement and evidence/abstention relevance vs signed benchmark; no invented accuracy claims |
| S08-S11-02 | AI/MLOps + Data Steward | Approved internal reference corpus with frozen provenance, approved vLLM/models and SME review | Research novelty/reference truth only assessed with trustworthy approved corpus; unverified-source abstention correct |
| S08-S11-03 | AI/MLOps + SRE | Approved pinned tokenizer/runtime, measured GPU/context and long documents | No window overflow/semantic truncation, controlled global synthesis and evidence-offset correctness with full long contexts; thresholds approved |
| S08-S11-04 | Security + AI Lead | Authorized organization network/IAM/TLS model access and synthetic prompt-injection corpus | No text exfiltration, tool invocation or rubric mutation, no secret leakage in engine/model logs, safe response semantics |
| S08-S11-05 | PO/SMEs + AI Lead | Approved OD-03/04/09/11 decisions and review adjudication | Final rounding/coverage/required policy implemented and verified, deterministic independently reproducible official scores, only approved versions published |
| S08-S11-06 | Platform Release + Security | Stage09/10 worker/controller, authorized staging IAM, encrypted evidence and production-representative database | End-to-end correct metadata persistence, DB numeric policy fit, scoped result access, encrypted raw and evidence, audit/no raw logs |

**Boundary:** No corporate GPU/vLLM, data, raw logs, shared Simorgh DB or external provider was called by Stage08 CI. Official scores are NOT permitted until all applicable product/security gates and Stage12 SME signoff. Stage09 NOT_STARTED.
