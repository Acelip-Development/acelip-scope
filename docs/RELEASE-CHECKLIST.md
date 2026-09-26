# Release checklist

**RC1 PUBLICATION COMPLETE — source + Flatpak. AppImage remains WITHHELD.**

The gate tables below use `scripts/release-checklist.py` and
`validation/rc1-release-facts.json`. The publication-status table and explicit
AppImage source/relinking rows are manually maintained closeout evidence; retain
these supplements when refreshing generated gates. No release tooling changed.
PASS applies only to the stated scope. Full evidence:
[RC1-PUBLICATION.md](RC1-PUBLICATION.md) and
[rc1-closeout.json](validation/rc1-closeout.json).

## Verified RC1 publication status

| Gate | Status | Evidence / limit |
|---|---|---|
| RC1 source publication | **PASS** | Public repository, unchanged release tag and anonymous tagged source archive HTTP 200 |
| RC1 Flatpak publication | **PASS** | Release asset `591604535`, 70,104 bytes; downloaded and SHA-256 verified |
| RC1 checksum publication | **PASS** | Release asset `591604767`, `SHA256SUMS`; downloaded manifest verifies the Flatpak |
| v1.0.0-rc1 tag | **PASS** | Local and remote annotated tag resolve to `4d2036aa15f08154205da9d293b83565a89bb61a` |
| v1.0.0-rc1 GitHub Release | **PASS** | [Public prerelease](https://github.com/Acelip-Development/acelip-scope/releases/tag/v1.0.0-rc1), ID `397420659`, published 2026-09-26 22:44:08 UTC |
| Remote Tests workflow | **PASS** | [Tests #7](https://github.com/Acelip-Development/acelip-scope/actions/runs/36276042735), release commit |
| Remote Repository security checks | **PASS** | [Security #7](https://github.com/Acelip-Development/acelip-scope/actions/runs/36276042744), release commit |
| Remote Package development artifacts workflow | **PASS** | [Packaging #5](https://github.com/Acelip-Development/acelip-scope/actions/runs/36275805400), release commit |

## RC1 source + Flatpak

| Gate | Status | Evidence / limit |
|---|---|---|
| Application name | **PASS** | Acelip Scope |
| Publisher | **PASS** | Acelip Development |
| Tagline | **PASS** | System diagnostics, made clear. |
| Application license selected | **PASS** | Apache-2.0 |
| Application ID | **PASS** | io.github.acelip_development.acelip-scope |
| Developer ID | **PASS** | io.github.acelip_development |
| Target repository namespace | **PASS** | Acelip-Development/acelip-scope |
| Remote repository created | **PASS** | PASS: existing PUBLIC Acelip-Development/acelip-scope repository verified; no settings changed. |
| Homepage reachable | **PASS** | PASS: public repository homepage reachable without credentials. |
| Support/issues reachable | **PASS** | PASS: GitHub Issues enabled and publicly reachable for normal support. |
| Security reporting configured | **PASS** | PASS: GitHub API reports private vulnerability reporting enabled. Report privately through /security/advisories/new; do not use public Issues for vulnerability details. |
| Repository public/reachable | **PASS** | PASS: API reports public; anonymous homepage, Issues and tagged source archive HEAD requests return 200. Earlier credential-free clone evidence is preserved in Git history. |
| CI green on GitHub | **PASS** | PASS at 4d2036aa15f08154205da9d293b83565a89bb61a: [Tests #7](https://github.com/Acelip-Development/acelip-scope/actions/runs/36276042735), [Repository security checks #7](https://github.com/Acelip-Development/acelip-scope/actions/runs/36276042744), [Package development artifacts #5](https://github.com/Acelip-Development/acelip-scope/actions/runs/36275805400). Local closeout is not pushed or remotely tested. |
| Automated tests green | **PASS** | PASS: full 325 regression tests and all 4 Gio integration tests re-run for closeout; coverage unchanged. |
| Flatpak builds and launches | **PASS** | PASS: historical launch/GTK acceptance retained; package workflow #5 passed at the release commit. Released bundle downloaded and checksum verified; no new launch/rebuild claimed. |
| Checksums verified | **PASS** | PASS: published Flatpak and SHA256SUMS downloaded; sha256sum --check passes, digest matches GitHub and approved 672c3247f4c3c61acb5eedf1a86efaea0f8791716d83c264ce1c7748063eef6a. |
| Builds reproduced | **PASS** | Local artifact reproducibility recorded; remote package run #4 independently built twice and compared checksums. No rebuild in this metadata-only step. |
| Manual save flow tested | **PASS** | Historical user-operated native/Flatpak save evidence retained; no new manual acceptance claimed. |
| Privacy review complete for current tree | **PASS** | PASS: current tracked/nonignored tree audited after closeout edits; zero findings. See validation/rc1-closeout.json. |
| Git-history publication review | **PASS** | PASS: prior layered publication-history review retained; 564 released-ancestry blobs rescanned with zero findings. Recovery refs retained and excluded. |
| Source licensing clearance | **PASS** | CLEARED: Acelip source Apache-2.0 and retained upstream license material; approved source publication. |
| Flatpak redistribution clearance | **PASS** | PASS: actual bundle has 73 project files, LICENSE/NOTICE, zero native libraries; GNOME runtime is separately supplied. |
| Source + Flatpak notices | **PASS** | PASS: project LICENSE/NOTICE retained; app-only Flatpak obtains GNOME libraries separately. AppImage-only obligations are excluded from this scope. |
| Screen-sharing status documented | **PASS** | See NAMESPACE-VALIDATION.md for current evidence; earlier validation reports preserve prior scope |
| Audio status documented | **PASS** | See NAMESPACE-VALIDATION.md for current evidence; earlier validation reports preserve prior scope |
| SMART status documented | **PASS** | See NAMESPACE-VALIDATION.md for current evidence; earlier validation reports preserve prior scope |
| Strict AppStream validation | **PASS** | PASS: appstreamcli validate --strict --no-net exits 0, no findings; release metadata and generated consistency checks pass. |
| README complete | **PASS** | PASS: public release page, actual Flatpak filename/checksum/install commands, source availability and AppImage withholding documented. |
| CHANGELOG complete | **PASS** | PASS: first public 1.0.0-rc1 features, identity, Apache-2.0, source + Flatpak release and intentional AppImage withholding recorded; historical entries preserved. |
| Clean final Git tree | **PASS** | Closeout committed locally on codex/rc1-post-release-closeout; final clean status and exact HEAD recorded in the Book checkpoint and completion handoff. Release tag is unchanged. |
| Book checkpoint written | **PASS** | Existing Acelip Scope project reused for final PUBLIC RC1 RELEASED checkpoint after the documentation commit; exact HEAD, clean status and readback-verified checkpoint ID in completion handoff. |
| RC1 source + Flatpak publication authorized | **PASS** | PASS: explicit user authorization covers source + Flatpak only. Public tag and GitHub prerelease now exist; no AppImage authorization. |

## AppImage — withheld from RC1

| Gate | Status | Evidence / limit |
|---|---|---|
| AppImage builds and launches | **PASS** | Historical development build/launch and remote packaging PASS; AppImage remains outside approved RC1 distribution. |
| AppImage redistribution clearance | **BLOCKED** | BLOCKED: FreeType/static primary notice gaps repaired; 1567 unmapped ELF files, incomplete source/relink duties and component exceptions remain. |
| AppImage advisory clearance | **BLOCKED** | BLOCKED: reviewed candidate advisories still have applicability/backport/coverage gaps; excludes AppImage from RC1. |
| AppImage corresponding-source closure | **BLOCKED** | BLOCKED: full corresponding-source closure, per-file/vendor ownership, exact Alpine revisions and static relinking remain unresolved. |
| AppImage static relinking obligations | **BLOCKED** | Static launcher source/relink materials remain incomplete; successful development builds do not close these duties. |
| AppImage notices | **BLOCKED** | Known required supplements (24 files), original notices and links verified. Overall completeness BLOCKED by unresolved ownership/per-file exceptions. |
| AppImage publication | **BLOCKED** | WITHHELD FROM RC1: redistribution/advisory and source/relinking clearance remain blocked. A green packaging job does not authorize AppImage distribution. |

## Other platforms

| Gate | Status | Evidence / limit |
|---|---|---|
| Windows/macOS package release | **NOT APPLICABLE** | Diagnostics remain UNSUPPORTED placeholders; Linux-only release candidate |
