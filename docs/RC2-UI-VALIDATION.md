# Acelip Scope RC2 UI validation

**Recommendation: RC2 READY — UI preparation scope.** Version `1.0.0-rc2-dev`.
This is a local development change, not an RC2 release or package approval.

Branch: `codex/rc2-dashboard-simplification`.
Clean main baseline: `6e1c1ffd08613b295051719416373f78507a8e51`.
Implementation: `1c9ae4ff92384976f4f5962cf3099eac411bd684`.
Validation ran on Ubuntu/GNOME/Wayland on September 26, 2026 (local time).
Machine-readable results: [rc2-ui-execution.json](validation/rc2-ui-execution.json).

## RC1 usability finding and baseline

The user installed the public RC1 Flatpak on the real host and confirmed
installation, first launch, identity, System theme default, theme switching and
persistence, CPU and RAM telemetry, and separate cooling readings. CPU temperature
used `k10temp / Tctl`. Expected Flatpak limitations appeared as PARTIAL/UNAVAILABLE.
The usability issue was information density: Overview acted as both a health
summary and a full diagnostic report, especially from Findings downward.

Baseline Book checkpoint `278ac48b-3390-4b95-8f30-16ff72f5f9db` records that
user-confirmed evidence, the planned UI work, branch, starting HEAD and clean
status. Its readback matched. The original **325 regression + 4 Gio** tests passed
before implementation. The Book remains external project-development backup.

## Overview before and after

| RC1 Overview | RC2 development Overview |
|---|---|
| Full central findings list in the main scroll | Counts and at most three Critical/Warning titles |
| Subsystem summaries repeat diagnostic evidence | State plus at most two short summary lines and View details |
| Full-width screen-sharing validation control | Available within Discord / Screen Sharing details |
| AI, export and raw report panels below findings | Existing workflows centralized in Reports |
| Long scroll mixes health, evidence and report actions | Persistent Overview / Findings / Reports tabs |

The header, read-only indicator, health headline and counters, scan selector,
Run scan, Live/pause, all six telemetry cards, graph semantics, two-second refresh
and bounded memory-only telemetry history remain. Counter buttons open Findings
with the matching severity. Overview never creates the complete finding rows.
Preview priority is Critical, then Warning; Info and Unavailable never fill spare
preview slots. A scan with no actionable findings shows a concise no-action
message while the headline still reflects incomplete coverage where appropriate.

Cards preserve useful cooling or filesystem facts and attention/unavailable
counts. Repeated Flatpak explanations collapse to “Flatpak host access restricted”.
Severity and support data are unchanged; sandbox restrictions are not promoted
into errors. Complete details remain available through every View details button.

## Findings architecture and data preservation

One `DashboardState`, sampler and `LiveHistory` serve all three persistent GTK
stack pages. View changes do not collect observations, merge scans, invalidate an
export or replace these objects. Each page has its own scroll container.

Findings starts with **Attention = Critical + Warnings**. “View all findings”
opens that default across subsystems; the severity dropdown also provides All
findings, Critical, Warnings, Info, Unavailable and Passed. Once selected, filters
survive ordinary tab changes. Both filters are presentation-only. Counts show
visible, selected-subsystem and total checks. The empty actionable view says
“No findings currently require attention” and offers Info/Unavailable buttons.

Subsystem detail buttons open Findings with **All findings** for that subsystem.
Rows retain severity, subsystem, title, summary, explanation, coverage, source,
full observation timestamp, Copy and AI explanation. Expanded Details retain
raw evidence, hardware/sensor identities and existing remediation guidance,
including what happened, why it matters, likely cause and suggested next step.
Expanded keys survive filtering and navigation and are pruned only when their
findings disappear from current observations. Focused scan scope replacement and
unrelated observation timestamps retain their existing semantics.

The existing optional screen-sharing panel is a persistent child of Findings,
visible under Discord / Screen Sharing. Explicit consent, start and cancellation
were exercised; navigating elsewhere does not silently start or finish a test.
As before, this manual checklist does not open a capture session or store frames.
Any actual Discord/system-picker consent remains controlled by the user in the
sharing application. No new end-to-end capture result is claimed.

## Reports and preferences

Reports contains the existing Markdown/JSON export format and privacy controls,
background preview preparation, reviewed-save action, optional AI handoff and
local unredacted report. No report-history system was added. Format/privacy or
scan changes still invalidate stale export previews. AI preparation still requires
fresh consent for the exact preview and does not execute or transmit commands.
The header Preferences button opens the retained panel within Reports.

GTK tests exercise real preview generation, both export formats, save-action
routing with the file-picker boundary mocked, exact finding Copy content with the
clipboard boundary mocked, and fresh AI consent. The four real Gio tests cover
file writing, replacement protection, invalid destinations and concurrent edits.
The real-host harness prepares a sanitized preview but does not save or copy it.

## Responsive layout, themes and accessibility

Validated all three pages at **1740×1000**, **1366×900**, **600×900** and
**480×900**, plus **600×1000** and **480×1000** with **150% text scaling**.
The sample Overview screenshot is 1366×1000. Vertical scrolling remains expected
on narrow/short windows; ordinary content has no horizontal overflow. FlowBox cards
stack naturally, while scan/filter/export/AI/manual-action rows reflow vertically.
One shared compact Adwaita breakpoint avoids competing row breakpoints. Expanded
consent labels and section headings wrap, including in the sharing controls.

All **13 themes** rendered Overview, Findings and Reports (39 captures) without
CSS findings: System, Dark, Light, Arcanum, Slate, Ion, Verdant, Frostline, Ember,
Nocturne, Cinder, Mauveglass and Midnight Circuit. System remains the fresh-install
default; the selected theme was persisted and read back from isolated preferences.
Representative System, Light and Midnight Circuit screenshots were visually inspected.

Keyboard checks exercise GTK Tab/move-focus traversal, focus on the tab switcher,
keyboard activation of all tabs and focusable filters. Existing focus styling
remains. Severity has explicit text and symbols; it does not depend on color.
Navigation, filters, detail actions and wrapping consent controls have accessible
names. Layout assertions check window/content minimum widths with expanded panels,
not just collapsed screenshots. Runs use `G_DEBUG=fatal-criticals`.
This is practical GTK accessibility validation, not a formal screen-reader/WCAG audit.

## Executed checks

| Check | Result |
|---|---|
| Full regression | **332 PASS**: original 325 plus 7 presentation-policy tests |
| Gio integration | **4 PASS** |
| Explicit GTK integration suite | **8 PASS**, no skips; navigation, data retention, filters, sharing, exports, themes, keyboard and responsive views |
| Source GTK smoke on Wayland | **PASS**, live samples, themes, exports, consent and cancellation |
| Real-host source acceptance | **PASS**, Full Scan and navigation with continued two-second telemetry |
| Generated/desktop/release metadata | **PASS** |
| Strict AppStream | **PASS, no findings** |
| Python/shell syntax and actionlint | **PASS** |
| Current-tree privacy | **PASS, zero findings** |

Commands (GUI commands require an accessible desktop; they install no packages):

```sh
python3 -m unittest discover -s tests -v
python3 -W ignore::DeprecationWarning -m unittest discover -s tests/integration -v
env GDK_BACKEND=wayland GSK_RENDERER=cairo GSETTINGS_BACKEND=memory \
  G_DEBUG=fatal-criticals RC2_QA_OUTPUT=var \
  python3 -W ignore::DeprecationWarning -m unittest discover -s tests/ui -v
env GDK_BACKEND=wayland GSK_RENDERER=cairo G_DEBUG=fatal-criticals \
  ./scripts/launch.sh --smoke-test
env GDK_BACKEND=wayland GSK_RENDERER=cairo GSETTINGS_BACKEND=memory \
  G_DEBUG=fatal-criticals python3 scripts/validation/validate-rc2-host.py \
  --output var/rc2-host-new-run
python3 scripts/check-source.py
python3 scripts/check-metadata.py --release
appstreamcli validate --strict --no-net data/io.github.acelip_development.acelip-scope.metainfo.xml
python3 scripts/audit-public.py
```

The host harness requires an empty output directory and uses isolated preferences
and a NON_UNIQUE source application. The GTK test suite has separate test session-
bus identities and no automatic diagnostic scans. The CI Tests workflow now runs
the explicit UI suite under Xvfb, in addition to its existing smoke/accessibility
checks. That changed workflow has been syntax-validated locally; it has **not**
run remotely because this branch is not pushed.

## Real-host observations

The final source harness ran on `GdkWaylandDisplay`. CPU telemetry retained
**k10temp / Tctl**, while subsystem evidence separately retained Tctl and Tccd1.
Cooling remained **3 separate readings: coolant, pump RPM and fan RPM**. The live
CPU temperature at capture was 62.6 °C; sensor identity, not an identical reading
under a different workload/time, is the acceptance condition. RAM and GPU metrics
continued to update in the native source build.

The Full Scan produced 89 retained observations (28 Passed, 53 Info, 4 Warnings,
1 Critical, 3 Unavailable). Navigation preserved the full snapshot and timestamps;
live history continued to five samples without another scan. Source access is
broader than Flatpak access, so these counts are not a comparison of sandbox coverage.
The real-host record stays in ignored `var/rc2-host-final/validation.json`.

## Screenshots

Screenshots render only the application widget tree. No desktop capture session
was opened. The five requested representative files use explicitly labeled
**SAMPLE DATA**, avoiding private host evidence in the full Findings screenshots:

- `var/rc2-overview.png`
- `var/rc2-findings-actionable.png`
- `var/rc2-findings-all.png`
- `var/rc2-subsystem-details.png`
- `var/rc2-compact.png`

Additional evidence: `var/rc2-findings-empty.png`, `var/rc2-keyboard-focus.png`,
`var/rc2-layout-*.png`, `var/rc2-expanded-150-*.png`, and `var/rc2-themes/*.png`.
**REAL HOST** Overview: `var/rc2-host-final/rc2-host-overview.png`.
These local QA files are ignored, not packaged or added to Git.

## RC1 preservation and remaining limits

Read-only GitHub verification confirms `v1.0.0-rc1` still resolves to
`4d2036aa15f08154205da9d293b83565a89bb61a`. Public prerelease ID `397420659`,
Flatpak asset `591604535` and checksum asset `591604767` retain their recorded
sizes, digests and update timestamps. AppImage is absent. The installed RC1 Flatpak
remains at deployment commit
`7e9ef850786691eeaf53a7c357a85abb65c22724f18b331484f5b3a5c62aea58` before and after
validation. No installation, asset upload, tag mutation or release action occurred.
RC1 publication documents and release evidence are unchanged. Development AppStream
adds the RC2-dev entry while retaining the original RC1 release entry.

No RC2 packages were rebuilt or installed; their build/install/release acceptance
remains separate. Windows/macOS remain unsupported. This work does not add actual
screen capture, establish receiver output/playback, grant SMART access, certify
other desktops or clear AppImage redistribution/source/relinking/advisory blockers.
The history-recovery branch remains intact. No push, tag or publication is performed.

A completion checkpoint in the existing Acelip Scope Book project records the
final documentation HEAD and clean Git status after commit; its readback-verified
ID is supplied in the task handoff. The Book is not an application dependency.

## Changed files

The two local implementation/documentation commits change these 22 files:

```text
.github/workflows/tests.yml
CHANGELOG.md
README.md
data/io.github.acelip_development.acelip-scope.metainfo.xml
docs/PACKAGING.md
docs/RC2-UI-VALIDATION.md
docs/validation/rc2-ui-execution.json
lucy_diagnose/dashboard.py
lucy_diagnose/identity.json
lucy_diagnose/themes/base.css
lucy_diagnose/ui/analysis_panel.py
lucy_diagnose/ui/export_panel.py
lucy_diagnose/ui/sharing_panel.py
lucy_diagnose/ui/widgets.py
lucy_diagnose/ui/window.py
scripts/render-metadata.py
scripts/validation/package-smoke.py
scripts/validation/validate-gui.py
scripts/validation/validate-rc2-host.py
scripts/visual-check.py
tests/test_dashboard_rc2.py
tests/ui/test_rc2_navigation.py
```
