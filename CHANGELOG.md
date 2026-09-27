# Changelog

## Unreleased — 1.0.0-rc2-dev

- Simplified Overview with concise subsystem cards, complete severity counts and
  at most three actionable findings; detailed evidence moved out of Overview.
- Persistent Overview / Findings / Reports navigation. Findings defaults to
  Critical and Warnings, with severity/subsystem filters and helpful empty states.
- Subsystem detail actions open complete filtered findings; screen-sharing manual
  validation lives inside Discord / Screen Sharing details.
- Reports centralizes reviewed Markdown/JSON exports, privacy controls and
  optional AI handoff. Navigation retains observations, timestamps, live history,
  expanded finding details and existing consent requirements.
- Compact layouts and 150% text reflow across the new views; all 13 themes retained.
- Regression and real GTK navigation coverage; see [RC2 UI validation](docs/RC2-UI-VALIDATION.md).
- Development UI preparation only. RC1 remains public and immutable. No RC2 tag,
  package publication or AppImage distribution; AppImage clearance remains blocked.

## 1.0.0-rc1

Published September 26, 2026: the first public release candidate.

- Acelip Scope public identity, published by Acelip Development.
- Unified diagnostics dashboard with Linux-first diagnostics and live telemetry.
- System default + 12 other themes.
- Privacy-filtered Markdown/JSON exports and an optional, consent-based AI
  explanation workflow through reviewed handoff.
- Multi-distro architecture and validation with explicit platform/coverage limits.
- Flatpak packaging; **source + x86_64 Flatpak released** with `SHA256SUMS`.
- Public GitHub repository/homepage and GitHub Issues support route.
- GitHub private vulnerability reporting enabled for confidential security reports.
- Tests, repository security checks and package development workflows passed on
  the tagged release commit; see [publication evidence](docs/RC1-PUBLICATION.md).
- **AppImage intentionally withheld** pending redistribution, source/relinking and advisory
  clearance. Its development build success is not release authorization.
- Apache-2.0; application ID `io.github.acelip_development.acelip-scope`.
- [Public RC1 release](https://github.com/Acelip-Development/acelip-scope/releases/tag/v1.0.0-rc1)
  at tag `v1.0.0-rc1`; post-release closeout changes documentation only.

Earlier preparation entries below preserve their historical decisions and limits.

## RC1 final namespace preparation

Applied final application/developer IDs for the approved Acelip-Development/acelip-scope
target. Prepared repository/homepage/Issues targets without advertising live links.
Added explicit safe host-side Flatpak preference transfer; native/AppImage settings
remain stable. No organization, repository, remote CI or security service created.


## RC1 application license approval

Applied Apache-2.0 and Copyright 2026 Acelip Development to the source, metadata,
About display and packages. Added verified attribution notices and preserved
third-party licenses. Dependency redistribution and publication remain blocked.


## Acelip Scope release candidate preparation

Approved public identity: Acelip Scope by Acelip Development — System diagnostics,
made clear. Renamed launcher, report exports and package artifacts; preserved
preferences with one-time migration. Internal modules and provisional app ID
remain stable. License, final namespace, URLs and publication remain blocked.

Acelip Scope was developed under the working name LUCY Diagnose through the
1.6.0-dev development cycle. Entries below preserve that history.

All versions below are development milestones supported by Git and validation
documents. No public release, Git tag or distribution promise is implied.

## 1.6.0-dev

- Public-facing documentation, centralized identity and explicit release gates.
- Read-only GitHub test/packaging/security workflows with pinned actions.
- Repository privacy checks and stronger report redaction for headers, truncated
  private keys, URI credentials, network shares and arbitrary public addresses.
- Architecture and reproducible epoch in build provenance; portable metadata.
- Accessible control names, explicit focus styling and friendlier unavailable
  messages, while retaining technical evidence.
- Reviewed AppImage removal of unused web engines/help viewer; preserved GTK,
  libadwaita, fonts and runtime notices; retained-consumer dependency checks.
- User-operated save/portal validation and renewed offline/package acceptance;
  exact results and remaining limits are in V1.6-VALIDATION.md.

## 1.5.0-dev

- Flatpak and AppImage packaging, checksums and demonstrated reproducibility.
- Flatpak capability awareness, package-safe state paths and visible provenance.
- Safer explicit export replacement, concurrent-edit protection and async buffer
  lifetime handling; AppImage mount distinguished from host disk capacity.
- 217 regression and 4 Gio integration tests; bounded Ubuntu/Fedora package runs.

## 1.4.0-dev

- Linux package/service/audio/SMART portability hardening and real userspace
  validation on multiple distro families; 176 regression tests.
- Scoped compatibility matrix and Ubuntu/Fedora GTK evidence, with manual gaps
  recorded instead of treating fixtures or containers as full desktops.

## 1.3.0-dev

- Shared platform contract, lazy backend selection and normalized capabilities.
- Linux distro, desktop, package, service and sensor adapters; Windows/macOS
  UNSUPPORTED placeholders; architecture regression guards.

## 1.2.0-dev

- System-first appearance, thirteen runtime themes and local theme persistence.
- Reviewed Markdown/JSON exports and explicit privacy/AI handoff boundaries.

See historical `docs/V1.x-VALIDATION.md` files for original scope and limitations.
