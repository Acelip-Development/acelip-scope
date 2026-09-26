# RC1 final namespace preparation

Product **Acelip Scope**, publisher **Acelip Development**.
Version **1.0.0-rc1**, license **Apache-2.0**, branch `codex/rc1-release-prep`.
Baseline `c0015975a2a0ac542c9b886f91f90d64d532a50d` was clean; all 288 regression
and 4 Gio integration tests were reverified before editing.

## Approved targets versus live services

| Field | Approved target / current state |
|---|---|
| Application ID | `io.github.acelip_development.acelip-scope` — PASS |
| Developer ID | `io.github.acelip_development` — PASS |
| GitHub namespace | `Acelip-Development/acelip-scope` — PASS as a target only |
| Repository URL target | `https://github.com/Acelip-Development/acelip-scope` |
| Homepage strategy | Use that repository after creation/reachability verification |
| Support strategy | GitHub Issues, derived as repository target plus `/issues` |
| Security strategy | GitHub private vulnerability reporting if available and enabled after creation |
| Remote repository created | BLOCKED — not created in this change |
| Homepage/support reachable | BLOCKED — not yet created or verified |
| Security reporting configured | BLOCKED — no contact/route advertised |

The organization and repository are not represented as existing. No separate
website, personal email or organization email was invented. `identity.json`
contains the approved repository target and the homepage/support/security
strategies; `planned_urls()` derives the future routes. `public_urls()` requires
separate remote-created and reachability flags before outputting public links.
These flags are false. AppStream omits all target URLs until the appropriate
remote checks pass. Approved namespace is not proof of remote ownership/existence.

Desktop, AppStream, icon exports, Flatpak manifest filename/ID, GTK application
ID and package provenance use the final ID. Internal Python modules stay stable.
AppStream's developer field now includes the approved developer ID and name;
Apache-2.0 remains the project license, with CC0-1.0 for metadata only.

## Validation scope

311 regression tests currently pass (all 288 originals retained, 23 new tests).
New coverage checks ID validity, AppStream developer/launchable identity,
manifest/desktop/icon alignment, staged package absence of obsolete IDs, target
URL generation and gating, and complete preference-transfer chains/failure cases.
Package rebuild/launch, reproducibility and final acceptance will be recorded
below after execution from the clean implementation commit.

AppStream now reports only `url-homepage-missing` (warning), raw exit 3.
`developer-id-missing` is resolved; project license and final IDs validate.
The warning is retained rather than masked with a nonexistent homepage.

## Preference continuity

Native `var/` and AppImage XDG preferences remain at their existing locations.
The final Flatpak ID has a new sandbox config root. Before first launch, close
both apps and run `python3 scripts/migrate-flatpak-preferences.py` on the host.
This explicit helper copies only validated preferences when the destination is
absent, preserves old-install preferences, rejects unsafe/invalid sources and
never broadens package permissions. Fresh installs retain System defaults. It is
not a silent automatic cross-sandbox migration; see
[PREFERENCE-MIGRATION.md](PREFERENCE-MIGRATION.md) for commands and precedence.
There is no persisted AI consent; fresh per-preview consent remains required.

## Obsolete-ID audit

Searched the current tracked/nonignored tree for the old application/desktop/
Flatpak ID `org.lucydiagnose.LucyDiagnose` and provisional-namespace statements.

- Current runtime and generated package metadata: old ID removed; final ID used.
- Host preference migration helper: intentional historical source ID only;
  this script is not copied into packages.
- Migration documentation/tests: explicit old-to-provisional-to-final lineage.
- Historical RC1/license/V1.2–V1.6 reports, inventory/execution snapshots and
  file lists: retained as evidence of what was built at that time. Updated
  historical report banners point to this current namespace report.
- Existing ignored artifacts/QA directories: historical private outputs, not
  current package contents. New artifacts replace `dist/` only after preserving
  prior files and hashes in a separate ignored archive.

The generic internal module name `lucy_diagnose` is not an application ID and
remains unchanged. No old-ID desktop/manifest resource remains in `data/` or the
active Flatpak manifest. No Git history or author identity was rewritten.

## Remaining publication gates

Remote organization/repository creation; homepage and Issues reachability;
private security configuration; remote GitHub CI; Git-history publication review;
dependency redistribution/source/relinking/attribution clearance (including the
recorded FreeType license-text question) and runtime advisory review; publication
authorization. The approved IDs, publisher/name/tagline, namespace target and
Apache-2.0 license do not clear those independent gates.

No Git remote was configured, no push/tag/release/publication performed, and no
GitHub organization or repository was created. The Book remains development
backup only; completion checkpoint and final HEAD are reported in the task handoff.
