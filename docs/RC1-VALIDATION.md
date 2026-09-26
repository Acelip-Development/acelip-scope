# Acelip Scope release candidate acceptance

Public identity: **Acelip Scope**, by **Acelip Development**.
**System diagnostics, made clear.**

Branch `codex/rc1-release-prep`, baseline `ab1c24c07b5b3a09c957ad5934d3befa147227fc`.
The original 254 regression and 4 Gio integration tests were re-run before editing.
Identity and migration coverage brings the regression suite to 274 tests, plus
4 Gio integration tests. Preflight package acceptance passed for both formats, including migration,
About identity, reports and all 13 themes; both builds reproduced byte-for-byte.
The 1.6.0-dev preflight evidence is in `validation/rc1-preflight.json`.
All code/build gates passed before the release-candidate version transition. Publication remains blocked independently.

The local directory and Python modules remain unchanged. The retained application
ID is provisional, with no domain ownership claim. The Book remains external
project infrastructure; its stable project record was reused and the pre-rename
checkpoint was verified before changes. No application dependency was added.

See [PREFERENCE-MIGRATION.md](PREFERENCE-MIGRATION.md),
[IDENTITY-AUDIT.md](IDENTITY-AUDIT.md) and [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md).
Final artifact, reproducibility and launch results will be recorded here after
execution. Historical manual picker/frame/audio/SMART limits remain exactly as
recorded in V1.6-VALIDATION.md; no new manual or hardware certification is implied.
