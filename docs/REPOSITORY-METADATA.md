# RC1 repository metadata milestone

Acelip Scope **1.0.0-rc1**; metadata update on `main` from
`fb5f4a650cc4b0a526fc88a107022be41caf003e`.

| Field | Value / verification |
|---|---|
| Repository/homepage | https://github.com/Acelip-Development/acelip-scope |
| Support/issues | https://github.com/Acelip-Development/acelip-scope/issues |
| Visibility | **Private**, confirmed by authenticated GitHub repository API; unchanged |
| Issues | Enabled; authenticated HEAD request to the Issues endpoint succeeded |
| URL access | Requires repository access; anonymous/public reachability is not asserted |
| Application ID | `io.github.acelip_development.acelip-scope`, unchanged |
| Developer ID | `io.github.acelip_development`, unchanged |
| License | Apache-2.0; LICENSE/NOTICE and third-party grants unchanged |
| Security reporting | **UNRESOLVED / private-repository-limited**; contact remains null and configured flag false |

The central `identity.json` records all three real URLs, verified readiness flags
and private visibility. Generated AppStream now carries homepage, vcs-browser and
help links; Python package metadata carries matching Homepage/Repository/Issues
URLs. Tests compare both outputs with the central identity and verify staged
package resources. Tests for uncreated/unverified repositories still use explicit
unready fixtures and continue to require that their links stay suppressed.
No application behavior, application ID, dependencies or sandbox permissions
changed. No email address or private reporting route was invented.

Validation for this milestone:

- **323 regression tests and four Gio integration tests: PASS.**
- **AppStream: PASS**, `appstreamcli validate --no-net` exits 0 with no findings;
  the missing-homepage warning is resolved. Generated metadata consistency and
  desktop-entry validation also pass.
- The broader `check-metadata.py --release` gate still exits 1 because
  `security_contact` and `security_reporting_configured` remain unresolved.
  This is separate from the clean AppStream result.
- **Current-tree privacy: PASS**, zero findings after all edits.
- GitHub API calls were read-only; repository visibility/security settings were
  not changed. No push, tag, release or publication was performed.

Existing `dist/` packages were not rebuilt. Their prior artifact hashes and
acceptance evidence remain historical and are not claimed to include this new
metadata. Canonical builds stage the updated identity/metainfo automatically;
no extra runtime libraries or licenses are added by this milestone.

The release checklist now distinguishes verified private repository/Issues
access from unresolved confidential reporting, remote CI for this commit,
AppImage redistribution/advisory obligations and publication authorization.
Historical validation documents retain their earlier scope. The existing Acelip
Scope Book identity is reused for a completion checkpoint with final commit,
validation results and clean status; its readback ID is in the task handoff.
