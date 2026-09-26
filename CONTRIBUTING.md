# Contributing

Acelip Scope source is licensed under [Apache-2.0](LICENSE).
The [repository](https://github.com/Acelip-Development/acelip-scope) is public,
with final app ID `io.github.acelip_development.acelip-scope` and developer ID
`io.github.acelip_development`. Public source checkouts and GitHub Issues are available. Security reports use
[private vulnerability reporting](https://github.com/Acelip-Development/acelip-scope/security/advisories/new). Do not change visibility,
publish history or enable services without authorization.

`lucy_diagnose/identity.json` centralizes the namespace, target repository URL and
homepage/support/security strategies. `public_urls()` requires separate remote
creation/reachability flags before emitting links. Set those flags only after
actual verification; public URLs and enabled private reporting are now verified.
RC1 publication approval covers source + Flatpak only; AppImage is withheld.

## Setup and checks

Use Python 3.11+ and, for GUI work, distribution PyGObject/Pycairo, GTK 4.10+
and libadwaita 1.5+. See [dependencies](docs/DEPENDENCIES.md). No host packages are
installed by app/build scripts; dependency installation is the developer's choice.

```sh
python3 scripts/check-source.py
python3 -m unittest discover -s tests -v
python3 -W ignore::DeprecationWarning -m unittest discover -s tests/integration -v
python3 scripts/audit-public.py
python3 scripts/render-metadata.py --check
python3 scripts/check-metadata.py
./scripts/launch.sh --smoke-test
```

Gio integration needs the GUI bindings but no display. GTK smoke needs a display;
CI's Xvfb run is a headless smoke check, not independent desktop validation.
The core regression suite includes Linux-family fixtures and architecture checks.
AppStream development checking permits only explicitly unresolved identity tags;
`python3 scripts/check-metadata.py --release` validates public identity/AppStream
readiness; it does not override the format-specific AppImage release blockers. Fetch the checksum-pinned optional actionlint tool with
`python3 scripts/fetch-actionlint.py`, then run `var/tools/actionlint`.

## Architecture and safe diagnostics

Read [PLATFORM-ARCHITECTURE.md](docs/PLATFORM-ARCHITECTURE.md). Shared models,
reports, privacy and UI use the platform abstraction. Linux paths, subprocesses
and host probes belong in `lucy_diagnose/platform/linux/`. Windows/macOS remain
UNSUPPORTED placeholders; do not make shared code import Linux probes eagerly.

Every probe must be read-only, bounded in time/output, cancellable where relevant
and normalized to supported/partial/unavailable/unsupported coverage. Missing
tools or sandbox restrictions are not generic health errors. Keep raw technical
evidence in Details and explain the user-visible consequence. Never add sudo,
polkit escalation, repairs, service activation, package installation or fallback
to a broader permission profile. Document any probe network traffic.

## Themes and accessibility

Add theme tokens in `themes/catalog.py`; use semantic severity tokens, readable
text and non-color labels. Preserve System as the first-run default. Exercise
all graph states, keyboard focus, meaningful accessible names, compact/wide
layouts and increased text scale. Use the existing GTK smoke harness; tests that
mirror a constant without checking behavior are not useful.

## Privacy and review

Filter copies rather than mutate observations. Test both JSON and Markdown,
secrets in environment/header/URI forms, home/host identifiers and edge cases.
Use obviously synthetic fixture data. New actual credentials must never be
allowlisted as fixtures. The repository auditor prints locations/rules, not
matched secret values. Check Git history separately before public publication;
removing a working-tree string does not remove its historical blobs.

PR descriptions should state the problem, resulting behavior, focused validation
and limits. Distinguish host execution, userspace execution, fixtures and untested
behavior. Do not attach raw journals, credentials, personal paths or unreviewed
screenshots. Keep builds/caches/reports out of Git. Do not change the name,
publisher, licensing, permissions or release policy without explicit approval.
