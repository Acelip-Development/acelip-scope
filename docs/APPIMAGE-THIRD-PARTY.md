# AppImage redistribution review

Acelip Scope 1.0.0-rc1. Technical review as of 2026-09-26, not legal advice.
**AppImage redistribution remains BLOCKED.** This review repairs identified
notices and adds reproducible evidence; it does not turn missing provenance into
clearance. Source licensing and the application-only Flatpak remain CLEARED.

## Decisions

| Obligation | Outcome | Evidence / remaining work |
|---|---|---|
| License texts | BLOCKED overall; identified supplements verified | Exact FreeType contributed notices and static-launcher primary texts added; unmapped payload/per-file exceptions prevent a universal claim |
| Source mapping | BLOCKED | Every payload file/link is indexed; many native files lack authoritative source ownership/build attestations |
| Source availability | BLOCKED | Eight exact upstream source archives retained with hashes; complete runtime patches/build graph and launcher Alpine revisions remain missing |
| Relinking/replacement | BLOCKED overall | Tested extracted/repacked image with modified Cairo; static libfuse relink and full LGPL source obligations remain |
| NOTICE | BLOCKED overall; known additions verified | Existing CUPS/e2fsprogs/setuptools notices preserved; FreeType and mimalloc omissions corrected; unresolved ownership prevents completeness |
| SBOM | PASS for generation/format; identification incomplete | Deterministic CycloneDX 1.6, file hashes and explicit unmapped group; schema validation is not license/source clearance |
| Advisories | BLOCKED | Exact-version/source queries and manual primary-source review completed within stated coverage; applicability/backports/coverage gaps remain |

The final package execution record and hashes are recorded after clean builds in
PUBLICATION-CLEARANCE.md. No dependency binary, feature, runtime lock, runtime
pruning rule, host-library assumption or Flatpak permission was changed.

## Actual payload inventory

The baseline was freshly extracted from the verified AppImage, rather than
inferred from its manifest: SHA-256
`ac9755c2bd52fca17b198511ebf813630222dc1424784ecce97f06c100ed149f`.
It contains 20,976 file/link entries and 2,231 regular ELF files. The embedded
manifest has 404 records but only 351 unique module names; neither count is a
count of shipped libraries. Duplicate bootstrap records, build-only inputs,
pruned modules and static vendoring must not be counted as verified components.

`scripts/appimage-compliance.py` records every file/link, SHA-256, ELF machine,
SONAME, NEEDED entries and build ID, installed Python METADATA/RECORD, source
records, license evidence and obligations. Unmapped files remain explicit.
Nested vendored Python distribution records take precedence over a parent
setuptools RECORD. PyGObject/Pycairo import directories have explicit mappings.
Source-family associations use reviewed rules in
`packaging/compliance/components.json`; they are labeled SOURCE CANDIDATE where
complete build ownership is not attested. No version is inferred from a `.so`
ABI suffix. Conflicting/missing version evidence remains null/REVIEW REQUIRED.

The deterministic output files are:

- `dist/appimage-components.json`: complete file ledger, source/obligation records
  and unresolved paths, tied to the final AppImage hash.
- `dist/appimage-sbom.cdx.json`: CycloneDX 1.6, with component and file records.
- `dist/THIRD-PARTY-LICENSES.md`: generated human-readable component/upstream/text
  index, avoiding a second hand-maintained dependency list.
- Embedded equivalents: `usr/share/licenses/acelip-scope/compliance/`.

The three self-describing generated files are explicitly excluded from their
own file hashes to avoid recursion; the external SBOM's artifact hash covers
the complete image. Unexpected files in that directory are still inventoried.
The launcher prefix is separately represented by its pinned SHA-256 and static
component records. The standard file SBOM includes unknown ownership instead of
silently omitting it; it is not a fully identified component-source SBOM.

Binary API probes independently confirmed GTK 4.22.5, libadwaita 1.9.4, Pango
1.57.1, Cairo 1.18.4, HarfBuzz 11.4.5, FreeType 2.14.3, OpenSSL 3.5.8, curl
8.21.0, Expat 2.7.1, dynamic zlib 1.3.1 and zstd 1.5.7. NSS_GetVersion reports
**3.101.4**, more precise than the manifest module CPE's 3.101; the source ref
also names 3.101.4. Source records retain discrepancies rather than flattening
all versions to an unverified label. Portal interaction uses the shipped Gio/
DBus/GTK paths; no invented standalone libportal component is added when absent.

## FreeType contributed-code resolution

The exact upstream source commit is
`0a0221a1347e2f1e07c395263540026e9a0aa7c7`. Its downloaded source archive is
hash-pinned in `packaging/compliance/source-archives.json`.
`FT_Library_Version` returned 2.14.3 and `FT_Get_Module` confirmed BDF, PCF,
TrueType, autofitter and CFF drivers. ELF dependencies and undefined symbols
confirm dynamic zlib and HarfBuzz use (`inflate*` and `hb_*`). Consequently:

| Code | Treatment |
|---|---|
| Main engine | Existing unmodified FTL and FreeType Team acknowledgement retained; FTL route selected |
| BDF/PCF drivers and shared hash code | All distinct copyright/grant/disclaimer blocks from the relevant source/header files retained verbatim |
| HarfBuzz-derived autofit code | Exact Old MIT-style notices, including distinct copyright blocks, retained |
| gzip | Uses external zlib; external zlib text retained. Internal copied-zlib source is not claimed statically embedded merely because it exists upstream |
| MD5/debug and source-only tools | Public-domain MD5 does not impose a notice requirement; no extra binary ownership is inferred for unshipped tools |

Sixteen distinct complete source-comment notices cover 20 relevant source/header
files. Identical blocks are stored once; different copyright dates/text are not
merged. `license-assets.json` records each exact source path, source hash,
byte offsets, upstream commit and extracted-text hash. These are unmodified
upstream blocks, not paraphrases. They are copied to
`usr/share/licenses/acelip-scope/third-party/freetype/contributed/`.
The known contributed-code notice gap is resolved once final package byte checks
pass. **This does not fix FreeType's separate advisory finding.**

The runtime manifest lists `enable-cleartype-subpixel.patch`; exact complete
runtime build provenance remains unavailable. FTL binary redistribution requires
acknowledgement, not a blanket source offer. The retained upstream archive is
identified as unmodified upstream source, not misrepresented as the exact patched
runtime source. No FreeType library was rebuilt in this change.

## Static launcher

Pinned launcher commit: `75849dce7cc37e4319b633df1f116ca895c71a12`.
Prefix SHA-256: `1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf`.
The matching upstream debug file passed GNU debuglink CRC validation; symbols
were used to locate version functions in the actual launcher. Private compiler
paths were not copied to public reports/SBOMs.

| Embedded component | Version evidence | Selected license / obligation |
|---|---|---|
| Launcher | Exact pinned source/release hash | MIT; original notice retained |
| libfuse | 3.15.0; pinned build recipe/archive hash; version bytes | LGPL-2.1-only for include/lib/build files; exact mount.c patch makes this a modified library |
| squashfuse | 0.5.2; pinned recipe/archive and binary string | BSD-2-Clause; full notice including author attributions copied |
| musl | 1.2.5; matching debug compile-unit provenance | MIT with per-file notices in full COPYRIGHT; exact Alpine patch revision unresolved |
| mimalloc | 2.1.7; matching `mi_version` symbol returns 217 | MIT; previously omitted from upstream launcher notice list, now explicitly attributed |
| zstd | 1.5.6; matching `ZSTD_versionString` points to exact literal | BSD-3-Clause option selected; distinct from runtime's dynamic 1.5.7 |
| zlib | 1.3.2; matching `zlibVersion` and copyright literal | Zlib; distinct from runtime's dynamic 1.3.1 |

Full primary license copies are bundled under
`usr/share/licenses/acelip-scope/third-party/appimage-runtime/`, with byte hashes
and upstream archive provenance. The original launcher LICENSE is not altered;
project NOTICE supplements its omissions. The exact libfuse mount patch is also
retained. Public workflow-log retrieval returned HTTP 403 without authentication;
no credentials were sought. The Dockerfile uses mutable Alpine 3.21 repositories.
Exact APK revisions/build inputs are therefore not claimed known.

Static libfuse triggers LGPL-2.1 section 6 combined-work obligations. Retaining
its source plus launcher source is progress, but **a complete reproducible
patched-library rebuild/relink route is not established**. All required library
source/modifications/build scripts and sufficient relinkable work must be
available under a valid option; a list of URLs alone is insufficient.

## Reciprocal licenses and source delivery

LGPL-2.1 dynamic libraries include GTK/libadwaita/GLib/Pango/PyGObject and other
native components. Their copies/source obligations remain even when the loader
accepts replacements. LGPL-3.0 (including vendored autocommand's declared LGPLv3)
adds its own GPLv3-based combined-work requirements. Cairo/Pycairo retain their
LGPL/MPL alternatives; choosing one route must be documented and completed,
not treating both as simultaneous or interchangeable obligations.

GPL programs/libraries actually present include bash, coreutils, grep, sed,
readline and mixed e2fsprogs material. Separate aggregation does not automatically
relicense the Apache application. GPLv2 section 3 or GPLv3 section 6 source
delivery, exact modifications and build instructions still apply to those works.
MPL-covered NSS/NSPR and Python vendoring require covered source availability and
recipient information under their exact grants. CDDL/EPL references in the notice
superset cannot be asserted shipped or absent without the missing file/vendor
mapping. Font/icon licenses retain their attribution, reserved-name and any
share-alike/font-source duties. No blanket Apache label is applied to them.

No proprietary EULA or reverse-engineering prohibition is introduced. Recipients
may modify covered libraries and reverse engineer to debug those modifications
as their applicable licenses permit. The Apache application grant remains
separate from all third-party grants.

A deterministic `dist/appimage-source-supplements.tar` contains eight exact
upstream source archives (FreeType, launcher and its six libraries), archive
hashes, provenance and the known libfuse patch. Build it offline from the verified
cache with:

```sh
python3 scripts/compliance-source-bundle.py \
  --cache var/appimage-clearance/upstream \
  --output dist/appimage-source-supplements.tar
```

The script refuses a mismatched input or existing output. This is **not complete
corresponding source** for the whole AppImage and is not a written offer.
The remaining runtime source archives, exact distribution patch contents/build
graph, static vendored ownership and Alpine revisions are explicit blockers.
Before a future authorized release, provide a verified complete source sidecar
and applicable replacement/relink instructions alongside binaries. Do not promise
a source offer without implementing its exact license-specific terms.

## Tested extraction/replacement/repacking mechanism

The existing launcher supports `--appimage-extract`; AppRun explicitly uses its
bundled loader and library path. In a private extracted copy, a non-loaded ELF
section was added to Cairo using `objcopy` with a separate output file. The
library hash changed, while its ABI/code remained compatible. GTK smoke passed;
loader diagnostics confirmed initialization of that modified library. Repacking
and running the new private AppImage also passed GTK smoke.

A reproducible outline (work only on your own disposable copies) is:

```sh
./acelip-scope-1.0.0-rc1-x86_64.AppImage --appimage-extract
# Place your ABI-compatible library build at the corresponding path in squashfs-root.
# Keep all applicable license/source/NOTICE materials with your modifications.
./squashfs-root/AppRun --smoke-test
mksquashfs squashfs-root filesystem.squashfs -noappend -all-root -no-xattrs \
  -comp zstd -processors 2 -mkfs-time 1 -all-time 1 -no-progress
# Concatenate the verified original 944632-byte launcher prefix and new filesystem.
python3 - <<'PY'
from pathlib import Path
import hashlib
original = Path('acelip-scope-1.0.0-rc1-x86_64.AppImage')
with original.open('rb') as stream:
    prefix = stream.read(944632)
assert hashlib.sha256(prefix).hexdigest() == '1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf'
output = Path('modified.AppImage')
with output.open('xb') as stream:
    stream.write(prefix)
    stream.write(Path('filesystem.squashfs').read_bytes())
output.chmod(0o755)
PY
APPIMAGE_EXTRACT_AND_RUN=1 ./modified.AppImage --smoke-test
```

The private proof artifact was not copied to `dist/`. This is an executed
replacement/repacking test for one compatible modification, **not** proof that
all LGPL obligations, arbitrary replacements, or static launcher relinking are
satisfied. No production library or user preference was replaced.

## Reproduction and evidence

```sh
python3 scripts/appimage-compliance.py extracted-AppDir \
  --artifact dist/acelip-scope-1.0.0-rc1-x86_64.AppImage --output dist
```

Canonical builds invoke the generator offline after staging exact notices.
Outputs have sorted records and no wall-clock timestamp, random ID or local
checkout path. Five regression checks cover file completeness/unknown ownership,
repeat generation/self-reference, license tamper rejection, nested vendor
ownership, and SBOM hashes/dependency references. The full generated SBOM was
validated against the official CycloneDX 1.6 schema using already-installed
jsonschema; no package was installed. Advisory findings and coverage limits are
in [DEPENDENCY-ADVISORIES.md](DEPENDENCY-ADVISORIES.md).
