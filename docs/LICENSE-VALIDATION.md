# RC1 Apache-2.0 license validation

Version remains **1.0.0-rc1**, branch `codex/rc1-release-prep`.
Baseline: `1ad52a4d5030d21fbf9112558167069e08ba86ac` (clean), with 274 regression
and 4 Gio integration tests reverified before edits.

**Application license: PASS — Apache-2.0.**
**Copyright 2026 Acelip Development.**
**Dependency redistribution clearance: BLOCKED. Publication: BLOCKED.**

Root LICENSE is byte-identical to the official Apache standard text. Project
NOTICE contains verified attribution and the unmodified pinned CUPS notice.
Source/package metadata, AppStream, About/preferences/build information and
README now declare Apache-2.0; third-party licenses remain separate. AppStream's
CC0-1.0 metadata license is unchanged. No mass source-header changes were made.

288 regression and 4 Gio integration tests pass. New tests cover the exact license
bytes, SPDX/copyright, AppStream, Python metadata, About, README, license gate,
absence of current unresolved-license placeholders, CUPS notice integrity,
package staging/provenance and relocatable runtime license links.

A local wheel built offline with setuptools 78.1.1 reports License-Expression
Apache-2.0 and contains byte-identical LICENSE and NOTICE. No host package was
installed. The minimum source wheel backend is setuptools 77 for PEP 639 support.

AppStream raw validation exits 3 for `url-homepage-missing` (warning) and
`developer-id-missing` (information), with no application-license finding.
Development metadata validation, desktop validation, actionlint 1.7.12,
Python/shell syntax and current-tree privacy audit pass.

Both package formats require rebuilding: they embed changed AppStream/identity,
About/build information, LICENSE and NOTICE; AppImage also fixes runtime license
link relocation. Final package execution and hashes will be recorded after the
clean source commit. Prior artifacts will be archived outside current `dist/`.

See [LICENSING-NOTES.md](LICENSING-NOTES.md) and the
[notice inventory](validation/rc1-license-inventory.json) for actual evidence,
selected component versions/licenses and unresolved redistribution questions.
The inventory covers 303 notice groups, 1,453 absolute links and two NOTICE files.
Retained texts are not a full SBOM or corresponding-source/attribution clearance.
The FreeType overview references license texts absent from its notice subtree;
that gap remains explicitly unresolved.

Remaining publication gates: dependency redistribution/source/relinking/attribution
clearance and runtime advisory review; final application/developer namespace;
repository/homepage/support URLs; security contact; remote GitHub CI; Git-history
publication review; and explicit publication authorization. The application
license blocker alone is cleared.

The Book remains external development infrastructure. Completion checkpoint and
final clean HEAD are recorded in the task handoff. No push, tag, publication or
GitHub Release is authorized or performed.
