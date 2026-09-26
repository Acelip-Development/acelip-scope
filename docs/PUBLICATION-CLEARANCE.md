# RC1 publication clearance

Acelip Scope **1.0.0-rc1**, Acelip Development — 2026-09-26.
Branch: `codex/rc1-publication-clearance`.
Baseline: `24b96ce9fd670276f870294a6199f220bc843fef`.
Rebuilt artifact source: `c4e60a5edf26d27782ed8b365edbf5e4ec179dda` (clean).

**Local audit completed; public publication remains BLOCKED.** No application
features changed. No history rewrite, remote creation, push, tag or publication.
The acceptance outcomes below deliberately distinguish completed review from
permission to distribute. Exact execution evidence:
[rc1-publication-execution.json](validation/rc1-publication-execution.json).

| Gate | Outcome |
|---|---|
| All reachable Git history inspected | PASS (baseline and new local commits; redaction remains blocked) |
| Existing history cleared for publication | BLOCKED — HISTORY REWRITE REQUIRED |
| Author/committer metadata | PASS — public pseudonym and GitHub noreply address |
| Layered historical secret review | PASS — no real credential detected within stated scope |
| Historical binary/generated-file review | PASS — no binary payloads or removal candidate for bloat |
| Current-tree privacy | PASS — zero unresolved findings |
| Source-tree redistribution | CLEARED (license scope); historical privacy remains BLOCKED |
| Flatpak application redistribution | CLEARED; separately supplied runtime excluded |
| AppImage redistribution | BLOCKED — source mapping/compliance and remaining notice gaps |
| FreeType main license text/acknowledgement | PASS — exact text in rebuilt AppImage; contributed-code review remains |
| Complete third-party notices | BLOCKED — static launcher and source-component exceptions unresolved |
| Tests and changed packages | PASS — 315 regression + 4 Gio; two identical builds per format; real GTK acceptance |

## Git history

Read-only `scripts/audit-history.py` traversed every commit tree under every
local ref and scanned every unique blob/path pair, raw commit objects (messages,
identities, dates), and tag objects if present. Baseline: **41 commits, 214 trees,
449 blobs**. Deleted files and renamed paths were included via historical trees;
`git log --all --diff-filter=DR --summary` was also reviewed. No tags, remote refs,
submodules or historical binary blobs were present. Existing branches:
`main`, `codex/v1.4-linux-validation`, `codex/v1.5-packaging`,
`codex/v1.6-public-release`, `codex/rc1-release-prep`; the new clearance branch
is included in subsequent scans. The post-build-commit scan covered 42 commits,
222 trees and 461 blobs. The final documentation commit receives a final local
scan whose result and exact HEAD are recorded in the completion checkpoint.
Reflogs/unreachable abandoned objects are local recovery state, outside the
publication ref closure. Nothing was pruned.

Classification:

- **SAFE HISTORICAL:** LUCY Diagnose product history, old IDs/internal Python
  paths, synthetic privacy fixtures and superseded validation reports.
- **PUBLICLY ACCEPTABLE:** public upstream URLs, project attribution, pseudonymous
  GitHub noreply metadata, synthetic example network/host identifiers.
- **PERSONAL METADATA:** one public account identity, documented below; no private
  email, machine-local mail address or real-name field found.
- **SECRET / CREDENTIAL:** no real credential found. All candidate values were
  examined locally; none is reproduced as a real secret in this report.
- **PRIVATE INFRASTRUCTURE:** nine historical checkout-path occurrences in three
  paths, nine blobs and 28 baseline commits. Values intentionally withheld here.
- **GENERATED ARTIFACT:** sanitized validation JSON is useful project evidence;
  no package, screenshot, database, archive, private export or cache was tracked.
- **REQUIRES REVIEW:** approval of the precise rewrite plan below, and package
  redistribution obligations. No destructive action is authorized by this report.

### Proposed history redaction — not executed

Each row identifies the first affected commit, historical path/line and exact
blob. [Machine-readable history evidence](validation/rc1-history-audit.json)
lists **every affected commit** for every occurrence, not just the introduction.
Problem in every row: a local absolute checkout path. Recommended redaction:
replace the literal with a repository-relative path or portable checkout
placeholder; in the validation helper retain the containment assertion using
its existing relative form. Do not remove the useful files wholesale.

| First affected commit | Path | Line | Blob | Affected commits |
|---|---|---:|---|---:|
| `a1f5c91fbd2c1d1a979b75f1542e984fd4ab4b9d` | `README.md` | 19 | `a0ecc6bc571784a9ebcfab31505a46b8b755a4d2` | 4 |
| `42dee619838f30d911b9b931043e87d918e545c5` | `docs/V1.2-VALIDATION.md` | 3 | `9fe1c77d389da27ba62d93f11f5d92b067213099` | 19 |
| `ac51ab16d777060209cbe3236e2bb747aa88aab1` | `README.md` | 22 | `17baaef8754c7969c9c7861fa8cc1ab164938619` | 2 |
| `c1b6064278005915bb7b1841e8c72da985b2d02d` | `README.md` | 23 | `393c3f4032589e5a3e2f13324df7c8d52272a829` | 8 |
| `c1b6064278005915bb7b1841e8c72da985b2d02d` | `scripts/validation/package-smoke.py` | 42 | `e999d7fb88f0d9ce6f9a4e17d138dc602cb5d4b6` | 6 |
| `42dee619838f30d911b9b931043e87d918e545c5` | `README.md` | 13 | `47e78eea7742e73e4514a1fb18f2543ea543f96c` | 5 |
| `7a35ee2bc80656e4d947de03cbf341ff91d6cce3` | `README.md` | 13 | `6d8aa8e5afa65ac7768d306339d3f26ee4274f96` | 5 |
| `325f81fb844036d8939a61e41786fb471b12ac80` | `README.md` | 13 | `ca225e14b9cd1762c4dacc636335d87e5ee26e22` | 1 |
| `1d58bbb6a116562c6fc27e6a861e6ae8f7b7f900` | `README.md` | 13 | `46a8025a36e7ea85a3e871d26fcc62ef545938ba` | 3 |

Scope: redact those blobs in **all containing refs**, then recreate every
reachable descendant commit whose tree or parent changes, through the final
clearance tip. All five existing branches contain affected ancestry; rewriting
only the new tip would leave the leaks publishable via old branches. Preserve
private recovery refs outside the eventual published ref set if a later approved
rewrite uses them. Do not push recovery branches containing old objects.
Author metadata need not change. No `filter-repo`, `filter-branch`, BFG, rebase,
reset, tag replacement or force-push was run. **HISTORY REWRITE REQUIRED; explicit
user approval is required before executing this proposed operation.**

## Author metadata

All unique values across reachable history (author and committer identical):

| Field | Unique value |
|---|---|
| Author name | `vetdadtryin` |
| Author email local part | `123786953+vetdadtryin` |
| Author email domain | `users.noreply.github.com` |
| Committer name | `vetdadtryin` |
| Committer email | Same local part and domain as author; joined with the standard at-sign |

**PASS** for privacy classification: GitHub privacy address and public handle;
no personal mailbox, machine-generated local address, unwanted real-name field
or obsolete alternate identity found. This establishes what would be exposed;
it does not prove the account owner prefers public association. Raw metadata is
retained in ignored local audit evidence and included in the private handoff.
No metadata rewrite was performed.

## Secret scan

| Tool/pattern layer | Scope | Result / reviewed false positives |
|---|---|---|
| Existing `audit-public.py --history` | All reachable baseline blobs | Nine checkout-path findings; no other unresolved finding |
| New `audit-history.py` | Raw commits, tags if any, all unique blobs and historical path associations, including binary strings | Same nine privacy findings; no real secret identified |
| Provider formats | AWS AKIA/ASIA, GitHub legacy/fine-grained, OpenAI/Anthropic-style, Google/Slack patterns | Three historical provider-key matches are the same deliberately synthetic privacy-test value |
| Generic credential formats | Bearer/Basic auth, password/key/token assignments, database URL userinfo, OAuth/session/cookie/JWT patterns | Nine assignment and three authorization matches: synthetic privacy tests and runtime-generated portal token code |
| Key material | Private-key blocks and SSH public-key encodings | Sixteen baseline block-marker matches are fake test strings; no encoded private key or SSH credential found |
| Infrastructure/privacy | Local username/homes/checkouts, private-address prefixes, MAC patterns, emails, NAS/host/database/Book references | Synthetic test values, release versions, public URLs and ordinary backup mentions reviewed; nine real checkout references remain |
| Dedicated scanners | `gitleaks`, `trufflehog`, `detect-secrets` PATH availability checked | NOT AVAILABLE; no packages installed and no scanner run falsely claimed |

Baseline pattern counts and exact matched object/line locations are in local
`var/publication-audit/history.json`. `rc1-history-audit.json` contains publishable
counts and redaction coordinates. The new audit/verification scripts and tests
add pattern definitions and synthetic key markers; those are not credentials.
The FTL supplement adds exact upstream public mailing-list addresses, permitted
only for the expected path **and SHA-256**, with tampering tests. No directory-wide
credential exclusion was added. These are layered pattern/content inspections,
not a mathematical guarantee of the absence of an unrecognised or encrypted
secret; no entropy scanner was available.

## Historical binaries

**PASS.** All 449 baseline blobs were text (no NUL-bearing blob), and filename
and magic review found no Flatpak/AppImage, PNG/JPEG/WebP screenshot, logs, SQLite,
archives, bytecode, generated test export, build cache or large binary. SVGs are
text source assets. Historical deleted collector files and stylesheet were
ordinary project source. Tracked `docs/validation/*.json` are sanitized validation
and license evidence, not private reports; retain them. No binary-removal list is
needed. Only the nine text redactions above are proposed.

## Current-tree privacy

**PASS.** Current tracked and nonignored source audit: zero unresolved findings.
No local homes, private hostnames/Book endpoints, real credentials, private IP/MAC,
NAS locations, diagnostics exports or generated package binaries were introduced.
AppImage byte scan also found no current home or checkout path; the packaged
application files match current source byte-for-byte, except recorded build
provenance. The app-only Flatpak's 73 files pass the packaged privacy check.
Upstream runtime test data and public license contacts are third-party material,
not private diagnostic exports. `.gitignore` now also excludes editor state,
local environment/Book integration files, caches, coverage and temporary exports.
Tests confirm build manifests, source fixtures and required license assets remain
trackable. No blanket `*.json`, source-directory or license exclusion was added.

Flatpak was installed into a dedicated project-local test store. Its disposable
QA directory was mapped to the normal per-app data location by Flatpak, then
moved intact into ignored project evidence; this differs from the initially
intended project-local output mapping. Synthetic harness preferences stayed in
that dedicated QA directory. Existing user settings were not used as fixtures.

## Dependency inventory

See the authoritative [licensing notes](LICENSING-NOTES.md) and
[component inventory](validation/rc1-redistribution-inventory.json). The exact
AppImage has **20,976 file/link entries**, **2,231 regular ELF files**, **21 Python
distribution metadata records**, **404 runtime manifest modules**, and **303
component notice groups plus the common-text store**. Presence of a manifest
module or retained notice alone does not establish that its payload ships.
The full local inventory includes file SHA-256s, links, ELF dependency edges and
all nested source records. **Definitive file-to-component/source ownership is
still BLOCKED**; ambiguous rows use REVIEW REQUIRED instead of invented licenses.

Application code, original themes/CSS, SVG, fixtures and documentation are
project-owned/generated based on source history. There are no third-party fonts
or raster art in the source tree. The Apache-2.0 LICENSE is unchanged, SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`;
project attribution remains **Copyright 2026 Acelip Development**. AppStream
metadata retains CC0-1.0 and third-party assets retain their upstream grants.

## FreeType resolution

**PASS for the known main-license-text gap.** Manifest source is FreeType 2.14.3,
commit `0a0221a1347e2f1e07c395263540026e9a0aa7c7`, with the distribution's named
ClearType patch. AppImage contains `libfreetype.so.6.20.6`. Exact upstream FTL
text is now inside the rebuilt image at
`runtime/share/licenses/freedesktop-sdk/freetype/docs/FTL.TXT`, matching source
SHA-256 `5a5ee54c5001bbad1cdc1a57cc3dd4c42199b2da09d39c7ee41fab002d02967f`.
NOTICE acknowledges the FreeType Team. The selected route is FTL, not both FTL
and the alternative GPL. **Full component clearance remains REVIEW REQUIRED**
for BDF/PCF/hash, gzip and HarfBuzz-derived terms referenced in the overview but
not all preserved in that component notice subtree. See licensing notes for
exact upstream source and obligations. Flatpak's app bundle contains no FreeType.

## Flatpak redistribution

**CLEARED** for the inspected application bundle only. Direct project-local
installation of the rebuilt bundle confirms 73 app files, no ELF payloads,
no embedded Python dependencies, exact project LICENSE/NOTICE, final application
ID and separate `org.gnome.Platform/x86_64/50` metadata. No runtime licenses were
copied unnecessarily. Runtime maintainers distribute their runtime separately;
redistributing that runtime ourselves would require its own clearance.
Default launcher/build-info and real packaged GTK acceptance passed, including
all scans, 13 themes, preferences, consent safeguards and Gio exports. Strict
AppStream still reports the missing homepage while the repository is uncreated.

## AppImage redistribution

**BLOCKED.** Inspection used `unsquashfs` directly on the newly built artifact,
with the offset checked against the pinned launcher. All original runtime notice
bytes are preserved; **1,453 relocated notice symlinks** resolve within the image.
Only FTL text was added; NOTICE and build provenance changed; no payload file was
removed and all other file contents/link targets match the baseline extraction.
Real launcher extraction-and-run plus packaged GTK acceptance passed. This is
not a fresh FUSE-mount-path or independent-desktop certification.

Remaining actions: establish authoritative binary/source ownership; collect exact
source, distribution patches and build scripts for bundled GPL/LGPL components;
choose and demonstrate compliant source-delivery and replacement/relinking routes;
verify static launcher library versions/full license copies/relink materials;
reconcile contributed-code, font, icon, MPL and codec terms. COPYING presence
alone is not clearance. Bundled GPL tools do not automatically relicense the
Apache application; their separate redistribution duties still apply.

## NOTICE/attribution

Project LICENSE/NOTICE match source in both artifacts. CUPS's notice body is
unchanged and hash-verified; GNOME Project attribution is grounded in upstream
Adwaita COPYING. e2fsprogs and both setuptools NOTICE files remain intact.
The FreeType acknowledgement is explicit. **Complete third-party notice clearance
is BLOCKED**, because the static launcher's notice links to library terms rather
than containing all exact license copies, and component exceptions remain under
review. README already links LICENSE, NOTICE and LICENSING-NOTES concisely.

## Repository size

Baseline `.git` allocated size: about **4.3 MiB**; reachable decoded objects:
**2,786,804 bytes**. At the clean package-source commit, `.git` allocated size is
**4,544 KiB**, apparent size **1,191,116 bytes**, and reachable decoded objects
**3,180,414 bytes** (725 loose objects; 3,264 KiB allocated object storage).
Final HEAD size is additionally captured in the completion checkpoint.
Largest baseline blob: license inventory **113,729 bytes**; next historical
runtime-size evidence **61,142 bytes**. Largest tracked file after this review is
the comprehensive redistribution inventory (about **299 KiB**), then the previous
license index and **61,074-byte** Linux validation evidence. No meaningful bloat
requires a rewrite. Package artifacts remain ignored and outside Git.

## Changed artifacts and verification

Both formats built twice from the same clean source and epoch. Checksums and
both manifests are byte-identical across independent builds. Updated artifacts
are in `dist/`; previous artifacts are preserved in ignored local backup.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `acelip-scope-1.0.0-rc1-x86_64.flatpak` | 69,952 | `53b06c537d427dedd1aca44b0eac74410e9b0324bbd6d8fa63bc53fcb4246581` |
| `acelip-scope-1.0.0-rc1-x86_64.AppImage` | 261,544,440 | `3e6ec77f0043f39ca7179c09c0c49ae529350fe55a07e1747523da80bffb55eb` |

315 regression tests (the original 311 plus four publication checks) and four Gio
integration tests pass. Syntax, metadata generation consistency, local actionlint,
package byte/notice checks and current-tree privacy pass. The new tests cover
exact FTL bytes/acknowledgement, narrowly bounded public-license exceptions,
deleted/renamed/binary/commit-message scanning and ignore boundaries. No manual
picker, capture, audio or hardware acceptance is newly claimed. Build timestamps
and NOTICE changed Flatpak bytes; AppImage also gains the FTL file. No runtime
library, application code, theme, identity or dependency version changed.

## Remaining blockers

1. Explicitly approve and execute the documented historical checkout-path
   redaction across affected refs, then rerun all history/privacy checks.
2. AppImage component/source ownership, full static launcher notices, source
   delivery/relinking obligations and component-specific attribution remain
   BLOCKED. FreeType main FTL gap is fixed; contributed-code review is not.
3. Exact-runtime advisory review remains open, separate from licensing.
4. GitHub repository creation, homepage/Issues reachability, private vulnerability
   reporting and remote CI remain unperformed and blocked.
5. Strict public-release AppStream validation awaits a verified homepage.
6. Explicit publication authorization remains absent.

The Book is development backup only. Existing project identity was reused;
verified baseline checkpoint `63339151-89c2-4240-ba41-5689c1744160` records the
starting SHA, tests, IDs, license, artifacts, status and gates. Completion is
recorded after the final local commit with actual HEAD, clean status, results and
checkpoint readback. Its verified ID is supplied in the task handoff. No remote
publication action is implied by that checkpoint.
