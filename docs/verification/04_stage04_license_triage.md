# Stage 04 — OSS license metadata triage for 27 dependencies (2026-10-25)

**Basis:** user-provided PowerShell output of the `.stage04-evidence-20261024-06/license-review.json` public-metadata fields. The file's `stage04-license-review-v1` format and 27-decision count were validated on the user's Windows workstation; the original full JSON and wheel `LICENSE`/`NOTICE` file bytes were **not provided for independent inspection**. This is **preliminary license triage only**, not legal permission, qualified audit approval or artifact authenticity. No confidential application text or reviewer identifying data is included.

**Triage gate:** `ALL_27_REVIEW_REQUIRED` / Stage 04 `IN_PROGRESS` / Stage 05 `NOT_STARTED`. Do not infer signed approval from a nonempty `license_metadata` field.

## Installed, version-exact metadata

| Package | Installed version | Local declared license metadata | Required follow-up | Status |
|---|---|---|---|---|
| `annotated-doc` | `0.0.5` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `annotated-types` | `0.8.0` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `anyio` | `4.15.1` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `certifi` | `2026.10.23` | `MPL-2.0` | MPL file-level source availability/notice on distribution; inspect covered files and modifications | `REVIEW_REQUIRED` |
| `click` | `8.5.0` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `colorama` | `0.4.6` | `License :: OSI Approved :: BSD License` | Generic BSD classifier only; upstream 0.4.6 describes BSD-3-Clause; inspect actual LICENSE | `REVIEW_REQUIRED` |
| `fastapi` | `0.148.0` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `h11` | `0.16.0` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `httpcore` | `1.0.9` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `httpcore2` | `2.16.0` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `httpx` | `0.28.1` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `httpx2` | `2.16.0` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `idna` | `3.20` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `iniconfig` | `2.3.1` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `opentelemetry-api` | `1.45.1` | `Apache-2.0` | Apache LICENSE and NOTICE, modified-file notices when applicable | `REVIEW_REQUIRED` |
| `packaging` | `26.3` | `Apache-2.0 OR BSD-2-Clause` | Dual license OR; reviewer must record selected alternative and notices | `REVIEW_REQUIRED` |
| `pluggy` | `1.7.0` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `pydantic` | `2.13.5` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `pydantic-core` | `2.46.5` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `pygments` | `2.21.0` | `BSD-2-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `pytest` | `9.0.3` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `pyyaml` | `6.0.3` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `starlette` | `1.9.0` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `truststore` | `0.10.5` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `typing-extensions` | `4.16.0` | `PSF-2.0` | PSF notices and change-summary terms to inspect | `REVIEW_REQUIRED` |
| `typing-inspection` | `0.4.4` | `MIT` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |
| `uvicorn` | `0.48.0` | `BSD-3-Clause` | Inspect exact wheel LICENSE/NOTICE and distribution obligations | `REVIEW_REQUIRED` |

**Category totals (exact user-provided metadata):** MIT **13**, BSD-3-Clause **8**, generic BSD classifier **1**, BSD-2-Clause **1**, Apache-2.0 **1**, Apache-2.0 OR BSD-2-Clause **1**, MPL-2.0 **1**, PSF-2.0 **1**: **27**. Every metadata value is nonempty. No real per-package authorized license decision has yet been presented.

## Official-source corroboration for the nontrivial cases

- **certifi 2026.10.23**: the [PyPI release](https://pypi.org/project/certifi/2026.10.23/) declares `MPL-2.0`. The [Mozilla license](https://www.mozilla.org/en-US/MPL/2.0/) and [FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) explain file-level copyleft. For any distribution of covered source/executable files, check license notification and how recipients obtain the covered source and modifications. Unrelated proprietary source is not automatically subject to the MPL solely from combining it with covered code.
- **packaging 26.3**: [PyPI release](https://pypi.org/project/packaging/26.3/) states `Apache-2.0 OR BSD-2-Clause`. [SPDX OR semantics](https://spdx.github.io/spdx-spec/v2.2.2/SPDX-license-expressions/) describe a choice of terms; a qualified reviewer must record the **chosen valid alternative** and applicable terms. Do not silently convert `OR` to `AND`.
- **colorama 0.4.6**: the installed metadata only reports a generic `BSD License` classifier. Its [specific PyPI release description](https://pypi.org/project/colorama/0.4.6/) states `BSD 3-Clause`. `BSD-3-Clause` is a **normalization candidate only** pending inspection of the exact 0.4.6 `LICENSE` file.
- **typing-extensions 4.16.0**: [PyPI release](https://pypi.org/project/typing-extensions/4.16.0/) lists `PSF-2.0`; examine the actual [PSF-2.0 text](https://spdx.org/licenses/PSF-2.0.html) and relevant notice/change provisions.
- **opentelemetry-api 1.45.1**: [specific PyPI release](https://pypi.org/project/opentelemetry-api/1.45.1/) lists `Apache-2.0`; inspect the version's license/NOTICE and [Apache 2.0 redistribution clauses](https://www.apache.org/licenses/LICENSE-2.0).
- **Other entries:** MIT/BSD license metadata remains **local installed-metadata claims**, not independently verified license-file evidence for all listed versions. When redistributing code, preserve relevant copyright, license text and disclaimers (see [BSD-3-Clause](https://opensource.org/license/bsd-3-clause)); this is a **general obligation description**, not a blanket legal sign-off.

## Evidence and authorization checklist

1. Inspect **every one of the exact 27 wheel artifacts'** actual `LICENSE*`, `COPYING*`, `NOTICE*` and nested notices, plus corresponding versioned source release where needed. Record file paths, version, source URL, checksum reference and any bundled subcomponents; absent or conflicting notices must be investigated.
2. Determine whether deployment is **internal to one legal entity** or software/artifacts are distributed to another party, including customers and vendors. Capture the actual planned deliverables/images and whether test/dev dependencies are shipped. Do not infer runtime scope solely from package names.
3. For each component document SPDX expression (and chosen OR alternative when applicable), applicable obligations, copyright holders, source/license text evidence, reviewer authority and explicit decision. **Do not auto-populate `APPROVED`, `reviewed_by` or fabricated evidence.** Keep the collector's original template as immutable historical evidence; any authorized decisions belong in a distinct review copy.
4. Match the eventual authorized license record against **the same `-06`** inventory, OSV audit, CycloneDX SBOM, wheelhouse, `wheel-hashes.json` and `pypi-digests.json` using the existing offline `evaluate` command. Its `PASS_LOCAL_EVIDENCE_ONLY` cannot verify legal authority or signed publisher provenance, and does not approve Stage 05 by itself.
5. Corporate deployment, runtime model provenance and real No-Egress verification remain `DEFERRED_TO_STAGE_11` under D-017; Stage 04's *local* gate remains open until independently reviewed local supply-chain/legal evidence is complete.

**Provenance distinction:** The five public releases above corroborate their *declared license expressions or descriptions*; no assistant reading of the 27 raw wheel files, all copyright notices, or company distribution contract is claimed.


## Exact 27-wheel license entry presence inspection — 2026-10-25

The user ran a **read-only .NET ZipArchive walk** on the real immutable `.stage04-evidence-20261024-06/wheelhouse`. The supplied console output listed **27 individual versioned wheels**, each with **at least one `LICENSE` file** under its `*.dist-info/licenses/` directory. A total of **29 matching license entry paths** were observed, because **`packaging-26.3` contains `LICENSE`, `LICENSE.APACHE` and `LICENSE.BSD`**. This is consistent with its declared `Apache-2.0 OR BSD-2-Clause` license expression but **does not by itself establish which option the authorized reviewer selects**. Specific requested exceptions have actual file paths: `certifi-2026.10.23.dist-info/licenses/LICENSE`, `colorama-0.4.6.dist-info/licenses/LICENSE.txt`, `typing_extensions-4.16.0.dist-info/licenses/LICENSE`, and `opentelemetry_api-1.45.1.dist-info/licenses/LICENSE`.

**Gate detail:** `LICENSE_ENTRY_PRESENCE_27_OF_27_PASS_USER_LOCAL_REPORTED` only. The actual extracted license bytes, full contents, copyright names, embedded third-party licenses and Notice obligations were **not** provided; entry listing is **not** a legal or full artifact review. It cannot prove that the text matches the claimed SPDX identifier, includes complete notices, or satisfies the organization's distribution terms. Every package remains `REVIEW_REQUIRED`; the raw template remains unchanged. No new source code or dependency version changes are authorized by this result.

**Next evidence handoff:** A bounded local read-only extraction of just the public `LICENSE`/`LICENCE`/`COPYING`/`NOTICE` entries from all 27 already SHA256-checked wheels, producing a **standalone local JSON document outside the Git repository** with filenames, entry paths, byte lengths, per-license SHA256 and exact UTF-8 text. Preserve the original wheelhouse, invent no reviewer identity or approval. The assistant may inspect the license text upon sharing this intentionally public-only evidence; it cannot determine company distribution/legal policy in place of a qualified reviewer. Actual internal-only usage vs delivery to another legal entity remains an unresolved input for downstream obligation review.

**Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED / NOT_APPROVED`**; the `-06` OSV clean/supply-chain scans and 70/70 user-local Windows tests remain separately recorded. The real company-controlled No-Egress/SSO/model artifact provenance tests remain `DEFERRED_TO_STAGE_11` per D-017.
