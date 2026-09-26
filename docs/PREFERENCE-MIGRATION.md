# Preference continuity

Native source checkouts retain `var/preferences.json`; no directory rename is
needed. Packaged builds use `$XDG_CONFIG_HOME/acelip-scope/preferences.json`.
Flatpak retains the provisional application ID and its sandbox XDG roots, so its
previous `$XDG_CONFIG_HOME/lucy-diagnose/preferences.json` remains accessible.

- An existing new file always wins, including an invalid file or symlink; normal
  validation/default behavior applies without importing old choices over it.
- If only the old file exists, compatible theme, live-graph and report-privacy
  choices are validated, written privately and atomically published without
  overwriting a concurrently created new file. The old file is removed only
  after verifying the new contents and checking the old contents are unchanged.
- Invalid legacy JSON, non-object data and symlinks are not imported. Failed
  writes preserve the old file and use validated legacy choices in memory;
  migration can retry next launch. Unknown/obsolete keys are not copied.
- Neither file: normal defaults, including System theme and sanitized reports.

The three fields above are the complete persisted preference schema. AI consent
is deliberately ephemeral and specific to each preview; migration does not
create standing consent or enable AI transmission. There are no persisted
provider credentials or diagnostic reports in this file. Existing bounded logs
and caches are not copied. The old directory itself is left intact to avoid
removing unrelated files. Changing the final Flatpak ID later requires a separate
sandbox migration review; this change makes no host filesystem permission grant.
