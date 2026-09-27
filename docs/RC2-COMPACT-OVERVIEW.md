# RC2 compact Overview validation

Branch: `codex/rc2-compact-overview`.
Baseline: `49eece41e2308c46a3d5d880cae2adee6c16a971`, inheriting the existing gauge
Overview. This is a focused source UI refinement, not a package or release update.

## Result

The Overview now contains a compact health/coverage header and severity counters,
one desktop scan/status/control row, three primary semicircular gauges, one
unified NVIDIA GPU surface, and six clickable subsystem rows. The Findings
summary panel is removed. Full findings, evidence, timestamps, remediation,
filtering and report/export workflows remain in their existing dedicated views.

CPU, RAM and CPU temperature keep their large textual values and concise state.
Full telemetry notes remain in tooltips. GPU utilization uses the existing gauge;
temperature, VRAM percentage and the available used/total MiB note are secondary
text on the same surface. Missing readings show N/A with the actual access reason,
never a fabricated zero or hardware fault. Collection and thresholds are unchanged.

Subsystem rows are native buttons with icons, aligned name/status/fact columns,
chevrons, accessible names and visible focus. Both click and keyboard activation
open all findings for that subsystem. The compact supporting fact omits repeated
sandbox/unavailable prose; the full summary remains in the tooltip and detailed
findings remain authoritative. Theme colors continue to use centralized tokens.

The inherited health header could show “No detected faults” below “Critical
findings”; the coverage line now describes observations/access without that
contradiction or a claim of full coverage merely because no checks are unavailable.
This changes presentation only, not health/status calculation or retained findings.

## Measured improvement

The same synthetic observations and host System theme were rendered before and
after at normal text scale. Values below are vertical scroll distances from GTK's
scroll adjustment, in logical pixels; the 1366x768 viewport is 676px high after
native window chrome and navigation.

| Window | Before | After |
|---|---:|---:|
| 1366x768 | 545px | **0px** |
| 1366x900 | 413px | **0px** |
| 1920x1080 | 233px | **0px** |
| 720x900 | 782px | **0px** |
| 600x900 | 896px | **251px** |
| 480x900 | 1168px | **437px** |

All six Systems rows are visible at 1366x768. This establishes a substantial
improvement for the measured dataset; longer localized text, larger fonts or
unusually long status messages can still require vertical scrolling. Narrow
windows intentionally stack content and retain vertical scrolling. No Overview
horizontal overflow or clipped controls was found, including at 480px/150% text
with Run scan, Cancel, Live and an active progress message visible together.

## Executed checks

| Check | Result |
|---|---|
| Full unit suite | **334 PASS**, original 332 retained plus two compact-summary checks |
| Gio integration | **4 PASS** |
| Explicit GTK suite | **14 PASS**, no skips; nine existing tests adapted/retained plus five compact Overview tests |
| Source GTK smoke | **PASS** on Ubuntu/GNOME/Wayland |
| Themes | **13 PASS**, all three views (39 captures), persistence and no CSS parsing errors |
| Responsive layouts | **PASS** at 480/600/720/1366/1920px, plus 480/600px at 150% text |
| Keyboard/accessibility | **PASS** practical focus traversal, tab activation, named metric text, keyboard subsystem activation and visible row focus |
| Source host acceptance | **PASS**: navigation retains observations/timestamps, two-second live updates continue, CPU `k10temp / Tctl`, three separate cooling readings |
| Source syntax | **PASS** Python AST and shell syntax |
| Metadata / strict AppStream | **PASS**, no findings |
| Privacy audit / diff whitespace | **PASS**, zero findings |

The GTK suite covers removed Overview findings UI, all severity links, all retained
Findings, subsystem navigation, numeric gauges, available/unavailable GPU states,
pause/resume and stale-sample rejection, scan/cancel controls, export/consent
semantics and unchanged state/history across layout/navigation. Scan-control tests
mock only thread startup; the separate smoke and host harness exercise actual
source scans. GTK accessibility validation is not a formal screen-reader audit.

The new bounds test initially compared minimum button width (including CSS
padding) to content-only width. It was corrected to compare allocated bounds and
also checks full window-relative bounds. Native theme transitions are allowed to
settle before screenshots; all colors and focus styles were visually reviewed on
representative System and Arcanum captures.

Commands run from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -W ignore::DeprecationWarning -m unittest discover -s tests/integration -v
env GDK_BACKEND=wayland GSK_RENDERER=cairo GSETTINGS_BACKEND=memory \
  G_DEBUG=fatal-criticals RC2_QA_OUTPUT=var/compact-overview/final \
  python3 -W ignore::DeprecationWarning -m unittest discover -s tests/ui -v
env GDK_BACKEND=wayland GSK_RENDERER=cairo GSETTINGS_BACKEND=memory \
  G_DEBUG=fatal-criticals ./scripts/launch.sh --smoke-test
env GDK_BACKEND=wayland GSK_RENDERER=cairo GSETTINGS_BACKEND=memory \
  G_DEBUG=fatal-criticals python3 scripts/validation/accessibility-smoke.py \
  --output var/compact-overview/accessibility
env GDK_BACKEND=wayland GSK_RENDERER=cairo GSETTINGS_BACKEND=memory \
  G_DEBUG=fatal-criticals python3 scripts/validation/validate-rc2-host.py \
  --output var/compact-overview/host
python3 scripts/check-source.py
python3 scripts/check-metadata.py --release
appstreamcli validate --strict --no-net data/io.github.acelip_development.acelip-scope.metainfo.xml
python3 scripts/audit-public.py
git diff --check
```

Existing CI already runs the explicit GTK suite under Xvfb. Local validation used
the actual Wayland display with isolated preferences and fatal GTK criticals;
remote CI was not run because this branch was not pushed. Use fresh empty output
directories when repeating the acceptance harnesses.

## Local screenshots and evidence

The existing `RC2_QA_OUTPUT` mechanism produced these application-widget captures
under ignored `var/compact-overview/final/`:

- `rc2-overview-1366x768.png`
- `rc2-overview-gpu-live.png` and `rc2-overview-gpu-unavailable.png`
- `rc2-layout-480-1.5-overview.png`
- `rc2-scan-controls-480-150.png`
- `rc2-subsystem-keyboard-focus.png`
- `rc2-themes/<theme>-<view>.png` (all thirteen themes and three views)

Before/after measurements and matched screenshots are in
`var/compact-overview/before.json`, `after.json`, `before/` and `after/`.
The source host harness has separate real telemetry evidence in `host/`.
These files are local QA, not release assets; no desktop capture was performed.

The diff is confined to Overview presentation, its summary policy, shared gauge
widgets/CSS, the directly affected host navigation helper, tests and this report.
No scanner, collector, thresholds, persistence, report/privacy logic, package
permissions, release history or packaging changes are included. No package was
rebuilt or installed, and no merge, push, tag or release was performed.
