# Bundled-runtime advisory review

Reviewed 2026-09-26 against the actual pinned Acelip Scope 1.0.0-rc1 AppImage.
**Advisory clearance: BLOCKED.** Available-data review is recorded, but unresolved
applicability/backports and source-ownership/feed-coverage gaps prevent a complete
security clearance. No exploitability claim is inferred from a CVSS score.

## Data and scope

The public OSV API was queried for **224 unique exact primary Git source commits**
from the embedded runtime manifest and **21 installed Python distribution
versions**, including setuptools vendoring: **245 queries, zero query errors**.
The responses produced **635 advisory records**, representing **620 canonical
IDs** after aliases. Raw query bodies/responses and all detailed records are
retained under ignored `var/appimage-clearance/advisories/` with response hashes.
Only public package names, versions and upstream commit IDs were sent.

[The review ledger](validation/rc1-appimage-advisories.json) records all
classifications, including 133 detailed non-kernel records and a compact list of
502 excluded kernel-header IDs. Duplicate OSV/CVE/curl/PSF/GHSA records are not
counted as independent vulnerabilities. Installed gitleaks, grype, trivy, syft,
osv-scanner and cve-bin-tool were unavailable; no scanner installation or
nonexecuted tool result is claimed. Direct OSV queries and primary-source review
were used instead.

The [OSV API](https://google.github.io/osv.dev/api/) is an advisory lookup, not
proof that a manifest component is shipped or that a reported code path is used.
Archive-only GNOME modules, source-less entries, transitive static vendoring and
exact Alpine package patch revisions lack complete coverage. A no-match response
means only no result from that query. Manifest `x-cpe.ignored` entries are
preserved as upstream metadata, **not automatically accepted as false positives**.

## Classifications

| Recorded status | Records | Interpretation |
|---|---:|---|
| FALSE POSITIVE | 503 | 502 kernel-header matches plus the absent fixfiles script; evidence below |
| NOT AFFECTED | 16 | Reviewed absent programs/backends/platform-specific use; includes alias duplicates |
| FIX AVAILABLE | 2 | FreeType and Expat cases with specific upstream fixes; applicability/backport review required |
| REVIEW REQUIRED | 114 | Candidate affected code/version/source association needs further assessment |

These counts describe the exact recorded dataset, not a tally of confirmed
exploitable vulnerabilities. No unknown fix state is labeled NO FIX. AFFECTED
means the applicable vulnerable code/use is established; this review does not
claim that every upstream version-range match meets that test.

## Important findings and evidence

| Component / advisory | Classification and reasoning | Release implication |
|---|---|---|
| FreeType 2.14.3, CVE-2026-50811 | FIX AVAILABLE. Actual API version and exact source precede fix `5a280ecde6f324de0d226261036e736e0cb49a71`; the manifest lists only a ClearType patch. Upstream issue concerns variable-coordinate handling. No malicious-font exploit was executed. | GTK uses font rendering, so this is not dismissed as an unused package. Establish whether caller coordinate counts reach the defect, or use a verified patched runtime/build before clearance. |
| Expat 2.7.1, CVE-2025-59375 and further candidates | FIX AVAILABLE for the identified resource-exhaustion issue (upstream 2.7.2); additional records cover subsequent fixes. Actual `XML_ExpatVersion` is 2.7.1, not inferred from a host package. | XML/config parsing is part of the shipped GUI/runtime stack; backport evidence and trusted/untrusted input boundaries must be assessed. No blanket “unused XML” dismissal. |
| curl 8.21.0 | Upstream lists nine advisories fixed after this version. Actual build uses OpenSSL, HTTP2 and cookies/PSL; its complete feature/protocol output was captured. | Conditional callbacks, pinning, cookies and HTTP2 paths remain REVIEW REQUIRED. Acelip's host diagnostics do not imply every bundled curl feature is invoked. |
| OpenSSL 3.5.8 | NOT AFFECTED by the August 2026 advisories whose affected ranges end before 3.5.8, including CVE-2026-75803. Actual `OpenSSL_version` matches 3.5.8. | This limited version-range conclusion is not a permanent all-advisory guarantee. |
| Python 3.13.15 | OSV/PSF candidates include urllib credential matching and tarfile behavior. Version/source is pinned; release predates these advisory publications. | Acelip does not extract arbitrary tar archives or use urllib HTTPPasswordMgr in its runtime flow; retained Python still needs per-record applicability/patch review. No automatic score-based block for an unused stdlib API. |
| Static launcher libraries | Exact upstream versions are now identified, but Alpine package revision/patch provenance is incomplete. | Full advisory coverage remains REVIEW REQUIRED, distinct from the repaired license copies. |
| Other image/audio/XML/security libraries and tools | Candidate records for TIFF, libxml2/libxslt, libgcrypt, nghttp2, PipeWire, ALSA, sndfile, Wget2 and others remain in the ledger. | Some utilities are physically bundled even when Acelip does not call them. Resolve exact shipped code/patches and plausible use, not just filenames. |

Primary evidence: [FreeType upstream fix](https://github.com/freetype/freetype/commit/5a280ecde6f324de0d226261036e736e0cb49a71),
[FreeType advisory tracking](https://security-tracker.debian.org/tracker/CVE-2026-50811),
[Expat security releases](https://libexpat.github.io/),
[curl 8.21.0 advisory list](https://curl.se/docs/vuln-8.21.0.html),
[OpenSSL affected-version ranges](https://mirror.openssl-library.org/news/vulnerabilities/),
[Python 3.13.15 release](https://www.python.org/downloads/release/python-31315/).

### Reviewed exclusions

- Linux kernel: the 502 matches came from `bootstrap/linux-headers.bst` source
  metadata. No kernel image or kernel module is included. Host-kernel security is
  a different boundary; this is a false positive for AppImage redistribution.
- curl CVE-2026-82208: wolfSSL-specific; actual build reports OpenSSL and has no
  wolfSSL backend. See the [upstream advisory](https://curl.se/docs/CVE-2026-82208.html).
- curl CVE-2026-13608: OpenLDAP SASL; actual protocol list has no LDAP/LDAPS.
- curl CVE-2026-19931: Negotiate/GSSAPI; actual feature list lacks GSS-API/SPNEGO.
- setuptools CVE-2026-59890 / GHSA-h35f-9h28-mq5c: macOS APFS/HFS+ sdist creation;
  this is a Linux runtime that does not build sdists. The
  [upstream advisory](https://github.com/pypa/setuptools/security/advisories/GHSA-h35f-9h28-mq5c)
  describes that narrower condition.
- `fixfiles`, `untgz`, `nghttpx`, `thumbnail`, `rgb2ycbcr` and `cupsd` are absent.
  Only records specifically tied to those absent programs/scheduler code were
  excluded. TIFF/CUPS/library-wide issues are not collectively cleared.

## Release policy and remaining actions

A materially applicable unresolved issue can block release regardless of score.
Conversely, a historical advisory, absent backend or unused API does not by
itself establish material exploitability. Before clearing this image:

1. Resolve unowned native files and static/vendor components so the review covers
   the actual source and patch set, not just primary manifest candidates.
2. Establish fixes/backports or precise non-applicability for the font/XML and
   other unresolved records. Record the build/configuration/call-path evidence.
3. Obtain complete static-launcher package revisions and source/relink materials;
   query those exact revisions and revalidate any changed binary.
4. Re-run recorded queries near a future release date; advisory databases evolve.

No runtime/library was silently upgraded, removed or replaced with host code to
obtain a PASS. This phase's release binaries receive compliance material only.
The private replacement proof is not distributed. Flatpak's **application bundle
redistribution** remains CLEARED; its separately supplied runtime still has an
independent security maintenance boundary. Neither format is publicly authorized
for release by this report.
