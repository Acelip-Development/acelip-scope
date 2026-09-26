# Acelip Scope 1.0.0-rc1 publication preparation

**Approved RC1 distribution: source + Flatpak only.**
**AppImage: WITHHELD**, pending its redistribution, advisory, source/relinking
and remaining notice clearance. These are AppImage-only blockers; source and
application-only Flatpak licensing/redistribution remain cleared.

This change updates publication metadata/documentation on `main` from
`e36f05644f3e9997f9bad621f1efa61242e3fe8a`. It creates no tag or GitHub Release,
pushes nothing, and does not change application behavior or dependency contents.
Application ID remains `io.github.acelip_development.acelip-scope` and the
application license remains Apache-2.0.

## Public repository and reporting evidence

| Item | Verified result |
|---|---|
| Repository/homepage | [Acelip-Development/acelip-scope](https://github.com/Acelip-Development/acelip-scope), PUBLIC; GitHub API reports `private: false` and `visibility: public` |
| Public reachability | Anonymous homepage and Issues HEAD requests returned HTTP 200 |
| Public source checkout | Credential-free, shallow HTTPS clone succeeded at the baseline SHA above |
| Normal support | [GitHub Issues](https://github.com/Acelip-Development/acelip-scope/issues), enabled and public |
| Confidential security reporting | GitHub reporting API returned `enabled: true`; use [Report a vulnerability](https://github.com/Acelip-Development/acelip-scope/security/advisories/new), not public Issues |

Repository/security configuration was read, not changed. The reporting URL is
the security contact; no email address was invented. Reporting requires signing
in to GitHub, while public source browsing/cloning does not require repository-
specific access. Central identity now records public visibility and configured
private vulnerability reporting.

## Remote GitHub CI evidence

All three workflows completed successfully on the exact baseline
`e36f05644f3e9997f9bad621f1efa61242e3fe8a`:

- [Tests #5](https://github.com/Acelip-Development/acelip-scope/actions/runs/36273378915): PASS.
- [Repository security checks #5](https://github.com/Acelip-Development/acelip-scope/actions/runs/36273378924): PASS.
- [Package development artifacts #4](https://github.com/Acelip-Development/acelip-scope/actions/runs/36273490732): PASS; its build step creates both development formats twice and verifies checksums.

This is evidence for that tested commit. The new final documentation/preparation
commit has not itself run remotely during this task; no workflow dispatch is
claimed. Local verification is recorded separately below. A green AppImage
build does not authorize that format for RC1 distribution.

## Publication scope and asset selection

The user's explicit approval covers source code and Flatpak. The central release
facts record `rc1_distribution: [source, flatpak]` and scoped publication approval.
The generated checklist places source/Flatpak gates in one section and withheld
AppImage gates in another; AppImage approval cannot be inherited from the approved
formats. AppImage redistribution, advisory clearance and release remain BLOCKED.

When the separately requested publication step occurs, select only source and
Flatpak assets with corresponding checksums. Do not upload the entire development
`dist/` directory, a blocked AppImage, AppImage-specific sidecars, recovery refs or
private local evidence. The local `backup/pre-publication-history-rewrite` ref
remains retained and unpublished. No artifact rebuild or release upload is part
of this metadata-only change.

## Local verification and checkpoint

- **325 regression tests + four Gio integration tests: PASS.** The original
  323 regressions remain; two added checks cover scoped authorization.
- **AppStream: PASS**, exit 0 with no findings (`appstreamcli validate --no-net`).
  Generated metadata consistency and `check-metadata.py --release` also pass.
  Application ID and Apache-2.0 remain covered by their existing assertions.
- **Current-tree privacy: PASS**, 214 tracked/nonignored files, zero findings.
- Scope regression checks ensure approved source/Flatpak gates stay separate from
  AppImage blockers and reject silently expanding RC1 approval to AppImage.

The existing Acelip Scope Book project receives a completion checkpoint after the
final local commit. It records verified public access, enabled private reporting,
exact green CI baseline/runs, source + Flatpak approval, AppImage withholding,
local test/AppStream/privacy results and clean Git status. Readback is verified;
the checkpoint ID and final commit are supplied in the handoff. The Book remains
development backup only.
