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


## Full-text license analysis from user-supplied evidence — 2026-10-25

**Evidence origin:** User pasted a JSON-shaped record containing `text`, wheel filename, archive entry, claimed SHA-256 and byte count for **29 LICENSE files across 27 exact-version Wheels**. This evidence was semantically read **from the submitted text**, not independently retrieved from the user's local ZIP/Wheel bytes. The 29 hex digests below were verified for expected SHA-256 *syntax* (64 lowercase hex characters) and coverage; they are **user-claimed values, NOT independently recomputed from the on-disk Wheel archives**. Do not confuse this with a cryptographically verified provenance or a signed license approval. Full copyrighted license text is deliberately **not** added to Git.

**Text-to-metadata outcome:** `TEXT_TO_METADATA_PRELIMINARY_CONSISTENT_27_OF_27`. Thirteen MIT claimants include a MIT grant, copyright retention and warranty disclaimer. Eight BSD-3-Clause claimants include the non-endorsement provision. The BSD-2-Clause package `pygments` contains two redistribution conditions. `colorama`'s local generic BSD license classifier resolves **provisionally** to BSD-3-Clause based on actual submitted three-clause text. `packaging`'s `LICENSE` expressly offers a choice between Apache-2.0 and BSD-2-Clause (not both obligatorily for users), with both detailed terms in `LICENSE.APACHE` and `LICENSE.BSD`; the authorized organization has **not** selected an option. `opentelemetry-api` contains the Apache 2.0 grant, notice and redistribution sections. `certifi` contains an **MPL-2.0 notice and retrieval URL for Mozilla-derived CA bundle content**, rather than the entire MPL-2.0 text; recipients' rights, covered-source access and bundle provenance require distribution-scenario review. `typing-extensions` contains PSF-2.0 terms and historical Python license terms including Zero-Clause BSD; the presence of historical terms is **not evidence that all components in the current package are multiply licensed**.

**General obligations, conditional on intended use:** MIT/BSD copyright, disclaimers and license text should be preserved on distribution; BSD-3-Clause includes non-endorsement. Apache-2.0 requires providing the license, identifying modified files and any relevant shipped NOTICE attributions. MPL-2.0 is file-level copyleft on covered content with source-availability obligations for distributions covered by its terms; it does not automatically force unrelated proprietary source disclosure. PSF terms include copyright/license retention and a brief change summary when applicable to distributions of qualifying derivative changes. SPDX `OR` means a license choice, not `AND`. These are textual/legal observations, **not an organizational legal approval**. Authoritative references: [Mozilla MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/), [SPDX OR meaning](https://spdx.github.io/spdx-spec/v2.2.2/SPDX-license-expressions/), [PSF 2 source](https://github.com/python/cpython/blob/main/Doc/license.rst).

### License entry digest ledger — values reported by user, not on-disk independently verified

| Package | License entry basename | Reported bytes | Reported SHA-256 |
|---|---|---:|---|
| `annotated-doc` | `LICENSE` | 1086 | `fff170779a6acbf65abdb405c087f1cee1786691e4a96a4034517e4a504a0cdf` |
| `annotated-types` | `LICENSE` | 1083 | `fe1049884b1a0d9342901e88e07f32925d24b3121d9972b6a6805fb9824b095d` |
| `anyio` | `LICENSE` | 1081 | `5361ac9dc58f2ef5fd2e9b09c68297c17f04950909bbc8023bdb82eacf22c2b0` |
| `certifi` | `LICENSE` | 989 | `e93716da6b9c0d5a4a1df60fe695b370f0695603d21f6f83f053e42cfc10caf7` |
| `click` | `LICENSE.txt` | 1475 | `9a8ad106a394e853bfe21f42f4e72d592819a22805d991b5f3275029292b658d` |
| `colorama` | `LICENSE.txt` | 1491 | `cac35c02686e5d04a5a7140bfb3b36e73aed496656e891102e428886d7930318` |
| `fastapi` | `LICENSE` | 1086 | `4ec89ffc81485b97fec584b2d4a961032eeffe834453894fd9c1274906cc744e` |
| `h11` | `LICENSE.txt` | 1124 | `37db5bb85926db28a427a25867f10b1232003aea1be69ccb851138adb8e6f361` |
| `httpcore` | `LICENSE.md` | 1518 | `fdcb59154c74cbaba16a11242f7740bea9f23d6feb5547917d8c5f94a80392a5` |
| `httpcore2` | `LICENSE.md` | 1599 | `c4df125c807b0613501e943a5c92496dd11d2c16604ce396097a8dde396304d9` |
| `httpx` | `LICENSE.md` | 1508 | `4ec59d544f12b5f539a3a716fd321ac58ccd8030b465221f2c880200cdf28d8d` |
| `httpx2` | `LICENSE.md` | 1589 | `7e7d6dbaf7fe160d39fd6e84fd02c33cab96bcbea34d36998d545bceb4a19c30` |
| `idna` | `LICENSE.md` | 1541 | `1a9a4f0e3d479a27240ddd59a9137a66ab4a0f9dfdc8ca6188cc0bfd85187f04` |
| `iniconfig` | `LICENSE` | 1098 | `3409fa91f7ace557894632676656e32264fe5ef7581535725dc9a23774551bd4` |
| `opentelemetry-api` | `LICENSE` | 11357 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| `packaging` | `LICENSE` | 197 | `cad1ef5bd340d73e074ba614d26f7deaca5c7940c3d8c34852e65c4909686c48` |
| `packaging` | `LICENSE.APACHE` | 10174 | `0d542e0c8804e39aa7f37eb00da5a762149dc682d7829451287e11b938e94594` |
| `packaging` | `LICENSE.BSD` | 1344 | `b70e7e9b742f1cc6f948b34c16aa39ffece94196364bc88ff0d2180f0028fac5` |
| `pluggy` | `LICENSE` | 1110 | `d6b65e6c213a5d0b577911d34d6e5949b9f59d76c238c5071a2f3fc16cfb2606` |
| `pydantic` | `LICENSE` | 1129 | `a9e186f3ca16b5eef84318e7a701721351a00cb7b8ae3a4394b67b49e3529ef3` |
| `pydantic-core` | `LICENSE` | 1101 | `fbe7f615f18d135c07000e5a86325db27f42c7729699ef166ac1f7a3f4586bf4` |
| `pygments` | `LICENSE` | 1331 | `a9d66f1d526df02e29dce73436d34e56e8632f46c275bbdffc70569e882f9f17` |
| `pytest` | `LICENSE` | 1091 | `ca836a5f9ecca3b2f350230faa20a48fb8b145653b5568d784862df864706b9b` |
| `pyyaml` | `LICENSE` | 1101 | `8d3928f9dc4490fd635707cb88eb26bd764102a7282954307d3e5167a577e8a4` |
| `starlette` | `LICENSE.md` | 1518 | `dcb95677a02240243187e964f941847d19b17821cf99e5afae684fab328c19bf` |
| `truststore` | `LICENSE` | 1086 | `33be7b7e8fa4fd19b1760e1a8ed8a668bdab852c91b692dd41424bcb725a9fca` |
| `typing-extensions` | `LICENSE` | 13936 | `3b2f81fe21d181c499c59a256c8e1968455d6689d269aa85373bfb6af41da3bf` |
| `typing-inspection` | `LICENSE` | 1090 | `804b59b25f2c31bd278f9202a19ae49a3945aa2664387e2d0a128c7cacc61ec3` |
| `uvicorn` | `LICENSE.md` | 1526 | `efe1acf3e62fb99c288b0ec73e5a773b7268ef4320fe757ea994214e4b63c371` |

**Remaining real acceptance prerequisites:** (1) independently compare the user-created local license-text JSON against the exact `-06/wheelhouse` ZIP-entry bytes and recorded hashes; (2) review missing/nested 3rd-party notices, bundled data and software, particularly certifi certificate data and compiled distributions; (3) determine the company's **internal-only deployment vs redistribution to other legal entities**; (4) qualified company legal/security reviewer to record a real per-package SPDX determination, relevant chosen `packaging` license alternative, applicable obligations and evidence references; (5) preserve the original blank `-06/license-review.json`, only write approved legal decisions to a separately authorized and reviewed copy; (6) independently inspect original SBOM, CVE and digest JSON evidence if required by acceptance. All **27 authorizations remain `REVIEW_REQUIRED`**, no fictitious `reviewed_by` or `APPROVED` fields. Local tests and last OSV no-findings scan remain `PASS_USER_LOCAL_REPORTED`; **Stage04 `IN_PROGRESS` / Stage05 `NOT_STARTED / NOT_APPROVED`**, company tests `DEFERRED_TO_STAGE_11` under D-017.


## Linux development test Image license review scope difference — 2026-10-27

User observed **27 installed Linux distributions** in the Stage04 Docker development test Image, including **`pip==26.2.2`**. Of these, 26 dependency names and exact versions match the previously reviewed Windows evidence, after PEP 503-style separator normalization. `colorama==0.4.6` appears only in the Windows license list and is **not** part of the Linux development test Image; **`pip==26.2.2`** appears only in this Linux full installed-distribution list and must receive its own version-exact license/compliance review **if included in a distributable image**. A runtime-only shipping image must be audited against its **own exact contents**, including OS packages and toolchain, not the Windows 27-package denominator. All qualified license and redistribution decisions remain **`REVIEW_REQUIRED`**; matching metadata does not approve real use or distribution.
