# Acelip Scope 1.0.0-rc1 publication record

**RC1 PUBLICATION COMPLETE** for the explicitly approved **source + Flatpak** scope.
Publication status: **PUBLIC RC1 RELEASED**. AppImage is **WITHHELD**.

| Field | Released value |
|---|---|
| Product | Acelip Scope |
| Publisher | Acelip Development |
| Version | 1.0.0-rc1 |
| Release date | September 26, 2026, 22:44:08 UTC |
| Repository / homepage | [Acelip-Development/acelip-scope](https://github.com/Acelip-Development/acelip-scope) |
| Release | [v1.0.0-rc1](https://github.com/Acelip-Development/acelip-scope/releases/tag/v1.0.0-rc1), public prerelease |
| Tag | `v1.0.0-rc1` |
| Release commit | `4d2036aa15f08154205da9d293b83565a89bb61a` |
| Annotated tag object | `a63e791c1af889954f2568f76a15a98f42a4e275` |
| License | Apache-2.0 |
| Application ID | `io.github.acelip_development.acelip-scope` |

## Published distribution and verification

| Distribution | Status | Evidence |
|---|---|---|
| Source | RELEASED | Public repository and GitHub source archives at the unchanged release tag |
| Flatpak x86_64 | RELEASED | `acelip-scope-1.0.0-rc1-x86_64.flatpak`, 70,104 bytes, asset ID `591604535` |
| Checksums | RELEASED | `SHA256SUMS`, 104 bytes, asset ID `591604767` |
| AppImage | WITHHELD | Absent from the release asset list; redistribution and advisory review remains incomplete |

Download from the release page above. The published Flatpak SHA-256 is:

```text
672c3247f4c3c61acb5eedf1a86efaea0f8791716d83c264ce1c7748063eef6a
```

The closeout downloaded both existing assets and ran `sha256sum --check SHA256SUMS`:
**PASS**. The computed Flatpak digest matches the published manifest, GitHub asset
digest and approved digest. The checksum file itself hashes to
`dac2befbc8f9ce5cc18acb3d0caba4d4ddba119c1deab56ba04e024c1038613e`.
Installation and checksum commands are in the [README](../README.md#flatpak-for-rc1).

Read-only GitHub API verification on 2026-09-26 confirmed repository
`private: false`, `visibility: public`, Issues enabled, release ID `397420659`,
`draft: false`, `prerelease: true`, and exactly the two attached assets above.
The annotated remote tag resolves to the release commit, matching the local tag.
Anonymous public homepage, Issues and source archive reachability is checked
separately from authenticated API access. Evidence is recorded in
[rc1-closeout.json](validation/rc1-closeout.json).

The explicit publication authorization covers source + Flatpak only, as recorded
in [release facts](validation/rc1-release-facts.json). The closeout creates no
release and uploads, deletes or replaces no assets. Tag and release asset identity
were compared again after the documentation edits: full release and tag API
responses were identical, including asset IDs, sizes, digests and timestamps. The local recovery branch
`backup/pre-publication-history-rewrite` remains at
`c9b7e8072bb35ee84653d21dda1072c65cdbcd46` and remains unpublished.

## Public support and security reporting

Normal support uses public [GitHub Issues](https://github.com/Acelip-Development/acelip-scope/issues).
GitHub private vulnerability reporting is **ENABLED**: the read-only reporting API
returns `enabled: true`. Report vulnerabilities through
[Report a vulnerability](https://github.com/Acelip-Development/acelip-scope/security/advisories/new).
Do not post sensitive vulnerability details in public Issues. No security email
or response-time promise is introduced. See [SECURITY.md](../SECURITY.md) and
[SUPPORT.md](../SUPPORT.md).

## Remote CI

All required workflows completed successfully on the exact release commit
`4d2036aa15f08154205da9d293b83565a89bb61a`:

| Workflow | Result | Evidence |
|---|---|---|
| Tests | PASS | [Run #7](https://github.com/Acelip-Development/acelip-scope/actions/runs/36276042735) |
| Repository security checks | PASS | [Run #7](https://github.com/Acelip-Development/acelip-scope/actions/runs/36276042744) |
| Package development artifacts | PASS | [Run #5](https://github.com/Acelip-Development/acelip-scope/actions/runs/36275805400) |

These results apply to the released commit. The local post-release documentation
commit has not been pushed or run remotely. Development package workflow success
does not authorize AppImage publication.

## Closeout validation and privacy

- Full regression suite: **325 tests PASS**, existing coverage preserved.
- Gio integration: **4 tests PASS**.
- Generated metadata consistency, desktop-entry and `check-metadata.py --release`:
  **PASS**.
- Strict AppStream: **PASS, no findings**, AppStream 1.1.2,
  `appstreamcli validate --strict --no-net data/io.github.acelip_development.acelip-scope.metainfo.xml`.
- Python/shell source syntax: **PASS**.
- Current-tree privacy audit: **PASS, 215 files, zero findings**.
- Git-history privacy review: **PASS** for publication history. The prior layered
  review and exact rewrite remain in [PUBLICATION-CLEARANCE.md](PUBLICATION-CLEARANCE.md)
  and [rc1-history-rewrite.json](validation/rc1-history-rewrite.json). Closeout also
  rescans the release ancestry with the repository privacy rules. Retained recovery
  refs and private local snapshots are excluded; no all-refs erasure is claimed.

Only documentation and release-state evidence changed after the tagged commit.
Application functionality, identity, workflows, tests, licensing files, build
scripts and staged package resources are unchanged. No packages were rebuilt.
The verified digest identifies the existing released Flatpak; it is not a claim
that a future build from the documentation HEAD would have identical provenance
or bytes.

## AppImage and known limitations

**AppImage is not distributed with 1.0.0-rc1.** Third-party redistribution and
advisory review remains incomplete. Corresponding-source closure, static relinking
obligations, complete component/notice mapping and advisory clearance remain
**BLOCKED**, as does AppImage publication. This is a distribution-clearance limit,
not an application failure. Development build instructions remain available.
These blockers do not reopen the completed source + Flatpak publication.

RC1 targets Linux x86_64. Windows/macOS diagnostics remain UNSUPPORTED placeholders.
Flatpak needs its separately supplied GNOME runtime and deliberately restricts
host services, package databases, raw devices and network access. Missing tools,
permissions and non-systemd sessions limit diagnostic coverage. Userspace/fixture
validation is not independent desktop certification; audio detection does not
prove playback and ScreenCast properties do not prove capture. Privacy filtering
is best effort and exports still require review. AI explanations are an optional,
user-controlled handoff. No new GUI or package acceptance run is claimed here.

## Post-release Git and project checkpoint

The closeout branch is `codex/rc1-post-release-closeout`, starting at the release
commit; its documentation commit follows the immutable release tag. The commit
containing this record is the closeout documentation HEAD. Exact final SHA, clean
Git status and verified checkpoint ID are recorded in the completion handoff and
the existing Acelip Scope Book project after commit.

The durable checkpoint records released source/Flatpak, the verified digest,
release/tag, CI, private reporting, privacy results and remaining AppImage blockers;
it is read back to verify persistence. The Book remains project-development backup
only and is not part of the Acelip Scope application.
