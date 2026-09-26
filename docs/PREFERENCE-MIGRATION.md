# Preference continuity across identities

The complete persisted schema is `theme`, `live_graphs` and `report_privacy`.
These cover the saved appearance/UI and report-privacy choices. AI consent is
intentionally ephemeral for each preview; no stored standing consent exists to
migrate. Unknown/obsolete fields, diagnostic reports, logs, caches and credentials
are never imported. Fresh installs use System theme and sanitized reports.

## Native and AppImage

Native source checkouts retain `var/preferences.json`. AppImage retains
`$XDG_CONFIG_HOME/acelip-scope/preferences.json`. Their location does not depend
on the GTK application ID, so the namespace change does not create a new store.
The existing automatic folder migration from `lucy-diagnose` still works:
existing new settings win; otherwise compatible old preferences are validated,
atomically published, verified and retired once. Invalid/symlinked old files
are not imported; failed writes preserve the source for retry.

## Flatpak: explicit host transfer before first launch

[Flatpak uses app-specific XDG storage](https://docs.flatpak.org/en/latest/conventions.html#xdg-base-directories).
The old working name and provisional Acelip builds both used the same app ID,
`org.lucydiagnose.LucyDiagnose`. The final ID is
`io.github.acelip_development.acelip-scope`. A new sandbox cannot read the old
ID's private config without additional access. No broad or transitional
filesystem permission is added here.

Close both app versions and run from the checkout **before first launch**:

```sh
python3 scripts/migrate-flatpak-preferences.py --dry-run
python3 scripts/migrate-flatpak-preferences.py
```

The opt-in host helper checks these locations under the selected home root:

1. Destination: `.var/app/io.github.acelip_development.acelip-scope/config/acelip-scope/preferences.json`.
2. Preferred source: `.var/app/org.lucydiagnose.LucyDiagnose/config/acelip-scope/preferences.json`.
3. Older source, only if the preferred source is absent:
   `.var/app/org.lucydiagnose.LucyDiagnose/config/lucy-diagnose/preferences.json`.

Existing destination settings always win, including invalid data. No file is
replaced. Symlinked source/destination locations are rejected. If a newer source
is invalid, migration stops instead of resurrecting older preferences. Missing
sources produce normal System defaults without writing a new file. The helper
uses the same validation and atomic exclusive creation as runtime settings,
creates private files, preserves old-install preferences, and reports failures
without printing values. Repeated runs do not change an existing destination;
a concurrent destination creation wins. `--home` supports isolated QA fixtures.

The old install can still be used or removed independently; the helper never
uninstalls it, removes app directories or copies diagnostic data. These are
intentional compatibility references in a host tool, not obsolete IDs shipped
as active package metadata. The host helper is not installed into either package.

A future published Flatpak remote can offer an EOL/rebase transition, which
requires the replacement ID to exist in that remote; this local bundle has no
such update path. See [Flathub maintenance](https://docs.flathub.org/docs/for-app-authors/maintenance).
Running the helper before first launch prevents new default settings from taking
precedence over older choices. This is an explicit local transfer, not automatic
cross-sandbox access or a claim that a remote migration has been configured.
