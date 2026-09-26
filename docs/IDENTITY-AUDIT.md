# Public identity migration audit (historical rename checkpoint)

The final-ID follow-up is audited in [NAMESPACE-VALIDATION.md](NAMESPACE-VALIDATION.md).
The provisional-ID statements below preserve the earlier rename phase only.

Searched all tracked and nonignored source text for `LUCY Diagnose`,
`LUCY-Diagnose`, `lucy-diagnose`, `lucy_diagnose`, `LUCY`, `Lucy`, and `lucy`.
Generated artifacts and private QA evidence are excluded from the public tree.

| Classification | Disposition and scope |
|---|---|
| PUBLIC IDENTITY | Renamed window/header, About and preferences, diagnostic explanations, report headers/JSON metadata, export filenames, AI handoff filename, desktop name/command, publisher, AppStream description and releases, launcher, package paths/names, current README/security/support/packaging documentation and CI artifact name. |
| INTERNAL MODULE | Retained `lucy_diagnose` imports, setuptools package discovery, internal `LucyApplication`/`LucyWindow` classes, CSS color tokens, worker names and `LUCY_HOST_XDG_DATA_DIRS` launcher/runner contract. None is a visible product label. |
| HISTORICAL | Retained V1.2–V1.6 validation documents, v1.4–v1.6 execution JSON, v1.6 AppImage size comparison/artifact names, and the explicit former-name notes in README/CHANGELOG. No Git history rewrite. |
| TEST FIXTURE | Updated current report, desktop, package and executable expectations. Retained synthetic `lucy-host`, `LUCY` hostname collision tests, nonexistent tool/package/service names and fake FUSE mount names. These are test inputs, not personal host data. Migration tests necessarily refer to the old directory. |
| MACHINE HOSTNAME | No personal hostname published. Synthetic privacy fixtures intentionally exercise hostname redaction. Report product metadata is added after host redaction so even a hostname matching the product cannot erase application attribution. |
| PROVISIONAL IDENTIFIER | The existing reverse-DNS ID is retained only in central identity, generated desktop/AppStream/Flatpak metadata and documented commands. No final domain or namespace is asserted. Final namespace remains BLOCKED. |
| MIGRATION / COMPATIBILITY | Old XDG directory in settings and migration docs; installer recognizes its previous managed-file marker; build script accepts the old build-commit environment variable. Existing source checkout path stays unchanged. |
| VALIDATION INTERNALS | Internal QA invocation names, portal handle tokens and fixture identifiers remain stable. User-visible synthetic manual report names now use Acelip Scope. |

The authoritative application ID lives in `lucy_diagnose/identity.json`.
`scripts/render-metadata.py` renders desktop, AppStream and the Flatpak manifest
from identity and a namespace-free manifest template. Runtime modules import it;
no unrelated runtime module repeats the provisional string. The neutral original
project-owned monitor/pulse icon replaces the earlier L-shaped graphic.

Privacy verification uses `scripts/audit-public.py`, plus source review of report
redaction, new identity fields, checked-in QA metadata and retained old-name
matches. No personal home/checkout paths, private addresses, MACs, credentials,
Book endpoints or NAS locations were added. Historical Git content and author
identity remain separate publication gates; clean current text does not clear
those gates. Final executed audit results are recorded in RC1-VALIDATION.md.
