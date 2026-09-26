# RC1 publication clearance

Current publication scope: [RC1-PUBLICATION.md](RC1-PUBLICATION.md).
**RC1 PUBLICATION COMPLETE for source + Flatpak. AppImage is withheld.**
The repository/homepage and Issues are public, private vulnerability reporting is
enabled, and all three required remote workflows passed on the tagged release commit.
AppImage-specific compliance/advisory blockers below apply only to that format.
The tag and public prerelease already exist. The closeout preserves both.

The clearance execution evidence below is historical; its artifact hashes and
statements about actions taken apply to that earlier milestone.

Acelip Scope **1.0.0-rc1**, Acelip Development — 2026-09-26.
Branch: `codex/rc1-appimage-clearance`.
Historical artifact source: `fe4b39f18ea76355f7247038e4c29c41605bd603` (clean).
Baseline: `24b96ce9fd670276f870294a6199f220bc843fef`.
Pre-rewrite HEAD: `c9b7e8072bb35ee84653d21dda1072c65cdbcd46`.
Historical post-rewrite HEAD / preceding artifact source: `6c4c33fcbf435879e07f086ba4a92130b8b4d338` (clean).
Retained local safety branch: `backup/pre-publication-history-rewrite`.

**Git-history publication review: PASS. Source + Flatpak RC1 publication:
APPROVED. AppImage publication: BLOCKED / WITHHELD.** The explicitly approved
nine-finding rewrite is complete. No application features changed and no remote
creation, push, tag or publication occurred.
The acceptance outcomes below deliberately distinguish completed review from
permission to distribute. Exact execution evidence:
[rc1-appimage-clearance.json](validation/rc1-appimage-clearance.json). The
[history rewrite record](validation/rc1-history-rewrite.json) and prior
[execution record](validation/rc1-publication-execution.json) is a preserved
pre-rewrite snapshot, including its old artifact hashes and blocked history gate.

| Gate | Outcome |
|---|---|
| All reachable publication history inspected | PASS — seven publication branches including this change; retained private recovery refs excluded |
| Git-history publication review | **PASS — nine approved findings removed; layered rescan passed** |
| Author/committer metadata | PASS — public pseudonym and GitHub noreply address |
| Layered historical secret review | PASS — no real credential detected within stated scope |
| Historical binary/generated-file review | PASS — no binary payloads or removal candidate for bloat |
| Current-tree privacy | PASS — zero unresolved findings |
| Source-tree redistribution | CLEARED; publication-history privacy now PASS |
| Flatpak application redistribution | CLEARED; separately supplied runtime excluded |
| AppImage redistribution | BLOCKED — source mapping/compliance and remaining notice gaps |
| FreeType license/attribution | PASS — main text plus 16 exact contributed notices in rebuilt AppImage; security gate separate |
| Complete third-party notices | BLOCKED overall — known static/FreeType gaps repaired; unidentified components/per-file exceptions remain |
| SBOM | PASS for deterministic CycloneDX 1.6 generation/schema; component-source identification remains incomplete |
| Dependency advisory review | BLOCKED — 245 queries completed; unresolved applicability/backports and coverage |
| Tests and changed packages | PASS — 320 regression + 4 Gio; two identical builds per format; real GTK acceptance |

## Git history

**PASS — nine approved checkout-path findings redacted.** The explicit user
approval covered only the exact findings in the original report. The full
[rewrite map](HISTORY-REWRITE-MAP.md) and [verification record](validation/rc1-history-rewrite.json)
record old/new commits, all nine blob mappings, replacements and per-commit
preservation checks. Original evidence remains in
[rc1-history-audit.json](validation/rc1-history-audit.json), labeled as the
pre-rewrite audit by its original HEAD and now superseded for current readiness.

Pre-rewrite HEAD: `c9b7e8072bb35ee84653d21dda1072c65cdbcd46`.
Immediate post-rewrite HEAD: `6c4c33fcbf435879e07f086ba4a92130b8b4d338`.
Backup: `backup/pre-publication-history-rewrite`, retained at the pre-rewrite HEAD.
Exactly nine blobs in three paths changed, affecting 53 file instances in 28
original commits. Parent propagation rewrote 42 of 43 commits; the root stayed
unchanged. All raw messages, author/committer metadata, dates and unrelated
file contents/modes are preserved. Current source tree before/after rewrite is
identical: `dd831166e7196ccc427e7a3244f6777fb113b069`.

`git filter-repo` was unavailable. An exact Git object-plumbing procedure built
candidate blobs/trees/commits, checked every mapped commit and current tree,
scanned candidates, then atomically updated six branches with expected old IDs:
`main`, `codex/v1.4-linux-validation`, `codex/v1.5-packaging`,
`codex/v1.6-public-release`, `codex/rc1-release-prep`, and
`codex/rc1-publication-clearance`. No file/commit was deleted and no identity was
normalized. No host package installation, filter-branch, reset, reflog expiry or
pruning occurred. `git fsck --full --strict` passes with exit 0 and no errors.

All history reachable from those six publication branches was scanned by both
existing audit implementations: **43 commits, 226 trees, 470 blobs**, zero
approved path literals remaining and zero unresolved privacy findings. The
subsequent documentation and AppImage compliance commits are also scanned before
final checkpointing, adding `codex/rc1-appimage-clearance` to the seven-branch
publication scope.
The publication scope intentionally excludes the retained backup branch,
private `refs/codex/*` tree snapshots, reflogs and unreachable recovery objects.
They remain local and must not be published. An unscoped `--all` scan will still
see the deliberately retained original findings; no local erasure is claimed.

Legitimate LUCY Diagnose history, public upstream contacts/URLs, synthetic
fixtures and sanitized validation evidence remain. No new real credential or
private infrastructure finding was discovered. Source licensing and package
redistribution gates remain separate from this history/privacy PASS.

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

**Post-rewrite PASS:** both existing scanners were rerun against all six
publication branches without changing their rules/exclusions. No real credential
was found. The nine checkout findings fell to zero; all credential-pattern
counts stayed unchanged and retain their reviewed synthetic meanings. New
mapping/report files were also scanned before the final checkpoint.

The table below preserves the **pre-rewrite** layered-scan scope and reviewed
false positives, rather than claiming the old nine findings still occur in
publication history:

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
`var/publication-audit/history.json`. New scans are under `var/history-rewrite/`. `rc1-history-audit.json` contains publishable
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
needed. The nine approved text redactions have now been applied; no other historical content was changed.

## Current-tree privacy

**PASS.** Current tracked and nonignored source audit: zero unresolved findings.
No local homes, private hostnames/Book endpoints, real credentials, private IP/MAC,
NAS locations, diagnostics exports or generated package binaries were introduced.
The rebuilt AppImage byte scan also found no current home or checkout path; the packaged
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
AppImage has **21,004 file/link entries**, **2,231 regular ELF files**, **21 Python
distribution metadata records**, **404 runtime manifest modules**, and **303
component notice groups plus the common-text store**. Presence of a manifest
module or retained notice alone does not establish that its payload ships.
The current [AppImage review](APPIMAGE-THIRD-PARTY.md) supersedes the earlier
manifest-only ownership inventory. `dist/appimage-components.json` records 108
component/group records and 21,001 file/link entries, plus three explicitly
excluded self-describing index files. Of these records, 77 are source families,
21 installed Python distributions, seven static launcher components and three
administrative groups. **1,567 ELF files remain explicitly unmapped.** The full
ledger includes file SHA-256s, links, ELF dependency edges and source candidates. **Definitive file-to-component/source ownership is
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
and the alternative GPL. **Contributed-code notice review now PASS:** binary probes confirm BDF/PCF and
HarfBuzz/system-zlib use; 16 exact complete notice blocks from 20 applicable
source/header files are retained under the supplemental third-party subtree.
The original main text and acknowledgement remain exact. FreeType
CVE-2026-50811 is a separate unresolved advisory gate. Flatpak's app bundle
contains no FreeType.

## Flatpak redistribution

**CLEARED** for the inspected application bundle only. Direct project-local
installation of the rebuilt bundle confirms 73 app files, no ELF payloads,
no embedded Python dependencies, exact project LICENSE/NOTICE, final application
ID and separate `org.gnome.Platform/x86_64/50` metadata. No runtime licenses were
copied unnecessarily. Runtime maintainers distribute their runtime separately;
redistributing that runtime ourselves would require its own clearance.
Default launcher/build-info and real packaged GTK acceptance passed, including
all scans, 13 themes, preferences, consent safeguards and Gio exports. Source AppStream now validates cleanly with the real repository URLs; the
recorded package acceptance here predates that metadata update.

## AppImage redistribution

**BLOCKED.** Inspection used `unsquashfs` directly on the newly built artifact,
with the offset checked against the pinned launcher. All original runtime notice
bytes are preserved; **1,453 relocated notice symlinks** resolve within the image.
This phase adds 28 compliance files: 24 exact license/source supplements, their
hash/provenance catalog and three generated inventory/index files. Existing
NOTICE and `_build.json` changed; all dependency/application code and all other
payload bytes/links are unchanged. No payload file was removed.
Real launcher extraction-and-run plus packaged GTK acceptance passed. This is
not a fresh FUSE-mount-path or independent-desktop certification.

Remaining actions: establish authoritative binary/source ownership; collect exact
source, distribution patches and build scripts for bundled GPL/LGPL components;
choose and demonstrate compliant source-delivery and replacement/relinking routes;
verify static launcher library versions/full license copies/relink materials;
reconcile remaining font, icon, MPL and codec terms. FreeType contributed notices
and primary static texts are now present; whole-image NOTICE completeness still
depends on unresolved ownership. COPYING presence
alone is not clearance. Bundled GPL tools do not automatically relicense the
Apache application; their separate redistribution duties still apply.

## NOTICE/attribution

Project LICENSE/NOTICE match source in both artifacts. CUPS's notice body is
unchanged and hash-verified; GNOME Project attribution is grounded in upstream
Adwaita COPYING. e2fsprogs and both setuptools NOTICE files remain intact.
The FreeType acknowledgement is explicit. **Complete third-party notice clearance
is BLOCKED overall**, because unmapped components and per-file exceptions remain.
The six identified static-library primary texts, including previously unlisted
mimalloc, are now packaged and hash-verified. Exact runtime build recipes were
recovered; ten source/recipe archives are retained, but complete source/relink
compliance is not established. README already links LICENSE, NOTICE and LICENSING-NOTES concisely.

## Repository size

Baseline `.git` allocated size: about **4.3 MiB**; reachable decoded objects:
**2,786,804 bytes**. At the clean package-source commit, `.git` allocated size is
**4,544 KiB**, apparent size **1,191,116 bytes**, and reachable decoded objects
**3,180,414 bytes** (725 loose objects; 3,264 KiB allocated object storage).
These are pre-rewrite measurements. The retained safety history increases
local object storage after rewriting; no objects were pruned. Final state is
captured in the completion checkpoint.
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
| `acelip-scope-1.0.0-rc1-x86_64.flatpak` | 70,128 | `6e9549ad676982600888a67b657b38cb97a0e6fc076fb224dbfcecd8f3d08a48` |
| `acelip-scope-1.0.0-rc1-x86_64.AppImage` | 263,387,640 | `f92f62190862bfd193079cb77a2b4c1126f41d22f98f0e0cc5d2ba4ea0096096` |

320 regression tests (original 315 preserved, five meaningful compliance checks)
and four Gio integration tests pass. Both real packaged GTK harnesses passed
identity, diagnostics, 13 themes, preferences, exports and privacy. Both formats,
component inventories and CycloneDX outputs reproduced byte-for-byte from clean
`fe4b39f`. The official CycloneDX 1.6 schema and dependency references validate.
A private modified-Cairo extract/repack test also passed GTK smoke; it is not a
claim of universal LGPL or static relink compliance. No manual picker/capture/
playback/hardware acceptance is newly claimed. No dependency binary changed.

Release sidecars are in `dist/`: component JSON, CycloneDX JSON, generated
THIRD-PARTY-LICENSES.md, advisory ledger, runtime-build provenance and the source
supplement. `SHA256SUMS.compliance` covers these six sidecars; `SHA256SUMS` covers
the packages. The ten-archive source supplement reproduced with SHA-256
`318c7c00063604f611f15b5fac51a3c6fbf60aeb891b7bb24797a3a9e7b30713`.
It is explicitly incomplete corresponding source, not a written offer.

## AppImage-only blockers and publication boundary

1. AppImage component/source ownership, remaining per-file notices, source
   delivery/relinking obligations and component-specific attribution remain
   BLOCKED. FreeType main/contributed notices and identified static primary texts
   are repaired; exact per-file/vendor ownership and full source closure remain.
2. Advisory clearance remains BLOCKED after 245 exact-source/Python queries and
   primary-source review. Resolve applicable defects/backports and coverage gaps;
   do not equate every candidate advisory with an exploitable application flaw.
3. AppImage release remains withheld. Successful development packaging does not
   establish AppImage redistribution or advisory clearance.

The repository is public and confidential GitHub vulnerability reporting is
enabled. Tests, repository security and development packaging CI passed at the
recorded baseline; [RC1-PUBLICATION.md](RC1-PUBLICATION.md) links the runs. User
publication approval covers source + Flatpak only. The blockers above do not
block that released scope. Tag/Release publication is complete; current evidence
is in the publication record linked above.

The Book remains development backup only; the existing Acelip Scope project was
reused. Pre-clearance checkpoint `f40bbc08-8a14-429a-8c90-085a80b887b7` was written
and read back before changes. The final checkpoint is written/read back after
the local documentation commit with current HEAD, hashes, individual clearance
states and clean status; its ID is supplied in the task handoff. The safety
branch remains unchanged and unpublished. This metadata preparation performs no
remote mutation, tag or GitHub Release creation.
