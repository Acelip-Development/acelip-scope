# Licensing notes

## Application grant

**Acelip Scope source/license: Apache-2.0.**
**Copyright 2026 Acelip Development.**

The owner approved Apache License 2.0 for this project. The root [LICENSE](../LICENSE)
is the unmodified [Apache Software Foundation standard text](https://www.apache.org/licenses/LICENSE-2.0.txt),
including the unchanged appendix placeholders. Its SHA-256 is
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The project copyright appears separately in NOTICE, README, central identity and
About/build information. Existing files do not use universal copyright headers;
no repetitive header sweep was performed.

**Third-party dependencies/assets retain their respective licenses.** The
application grant does not replace upstream licenses, grant third-party rights,
or clear redistribution. AppStream's existing CC0-1.0 metadata license remains
specific to that metadata. Original application Python/CSS, theme palettes and
neutral SVG are project-authored; no external raster/logo, sound or font was added.

## Scope and evidence

Reviewed the existing pinned GNOME Platform 50 x86_64 runtime, its `manifest.json`,
Python distribution metadata, complete `share/licenses/` tree, packaging scripts,
pruning manifest and pinned AppImage launcher license. No dependency was upgraded.
Exact runtime commit:
`b1935f7a673108616d4fd84564f15cefc9f637481472a8d4d2f0945375d41f4b`.

The [notice inventory](validation/rc1-license-inventory.json) records 303 component
notice groups, known manifest versions, notice hashes and the scope of review.
It includes notices for some components removed by the existing prune manifest;
a notice's presence alone does not prove that component is shipped. It is not a
complete binary-to-source SBOM or a legal clearance. Files under `common/` are
shared license texts referenced by component links.

The table below records selected direct/runtime components and the inspected
terms. License families do not override per-file exceptions. Relative evidence
paths are under the pinned runtime's `share/licenses/` unless specified otherwise.

| Component | Version / evidence | License and attribution | Redistribution implications / open questions |
|---|---|---|---|
| Python / stdlib | 3.13.15, runtime manifest | PSF and per-component notices, `freedesktop-sdk/python3/` | Retain full notices; review included stdlib third-party terms. |
| GTK4 | 4.22.5, manifest; `gnome/gtk/` | Upstream LGPL family; retained COPYING is LGPL-2.0 and subdirectories have their own notices | Do not infer one exact SPDX expression from COPYING alone; source-level grant/version and dynamic-link/source compliance remain review items. |
| libadwaita | 1.9.4, manifest; `gnome/libadwaita/COPYING` | LGPL-2.1 text; upstream project grant applies | Preserve LGPL and copyright notices; corresponding source/replaceability review outstanding. |
| PyGObject | 3.56.3, distribution metadata | LGPL-2.1-or-later; `gnome/pygobject/`, plus pythoncapi-compat subproject notice | Retain subcomponent notices and comply with LGPL source/relinking obligations. |
| Pycairo | 1.29.1, metadata and `freedesktop-sdk/pycairo/COPYING` | LGPL-2.1-only OR MPL-1.1 | Preserve both supplied texts; document compliant redistribution route before publishing. |
| GLib/Gio | 2.88.3, manifest; `gnome/glib/LICENSES/` | Component-specific LGPL-2.1, MPL, permissive and documentation terms | Do not label the entire component with one license; retain subproject notices and resolve shipped-file scope. |
| Cairo | 1.18.4, manifest; `gnome/cairo/COPYING` | LGPL-2.1 OR MPL-1.1; other utility/test terms retained | Review chosen compliance route and which ancillary files ship. |
| Pango | 1.57.1, manifest; `gnome/pango/COPYING` | LGPL text retained | Verify source-level version/permissions and corresponding-source obligations. |
| HarfBuzz | 11.4.5, manifest; `freedesktop-sdk/harfbuzz/COPYING` | Old MIT with per-file/subdirectory exceptions | Preserve attribution and exceptions; not all retained test/font notices are the library grant. |
| fontconfig | 2.17.1, manifest; `freedesktop-sdk/fontconfig/COPYING` | Permissive component copyright/permission notices | Retain the full notice, not just an inferred SPDX label. |
| FreeType | 2.14.3, manifest; `freedesktop-sdk/freetype/LICENSE.TXT` | FTL OR GPL-2.0-or-later; additional contributed-file terms | FTL requires documentation acknowledgement. The pinned runtime supplied only the overview; the rebuilt AppImage now adds exact `docs/FTL.TXT` and an acknowledgement. GPLv2 is the unselected alternative. Contributed-code terms remain under review below. |
| glibc / loader | 2.42, manifest; `freedesktop-sdk/glibc/LICENSES` | LGPL and per-component terms | Corresponding source, relinking/replaceability and bundled utility scope need review. |
| OpenSSL | 3.5.8, manifest; `freedesktop-sdk/openssl/LICENSE.txt` | Apache-2.0 plus retained component notices | Retain notices and review any additional source-level attribution requirements; no separate NOTICE found in this runtime subtree. |
| CUPS | 2.4.12, manifest; `freedesktop-sdk/cups/NOTICE` and `doc/help/license.html` | Apache-2.0 with CUPS exceptions and embedded-code attributions | Exact CUPS NOTICE included in root NOTICE; original also retained. Exceptions are CUPS-specific, not changes to the application Apache license. |
| e2fsprogs | 1.47.4, manifest; `freedesktop-sdk/e2fsprogs/NOTICE` | GPL-2.0 with library-specific LGPL/BSD/MIT terms | Preserve full upstream NOTICE; exact shipped libraries/tools and source obligations need clearance. |
| Adwaita icons | 50.0, manifest; `adwaita-icon-theme/COPYING*` | LGPL-3.0 OR CC-BY-SA-3.0-US, as stated upstream; attribution: GNOME Project | Attribution included in NOTICE; retain upstream terms and reconcile selected route/assets. |
| Cantarell / Noto Emoji / other runtime fonts | Cantarell 0.303.1; Noto Emoji 2.051, manifest | Inspected font notices include SIL OFL-1.1; other fonts retain their own notices | Preserve font copyright/license and reserved-name requirements; not project-owned artwork. Audit remaining font families separately. |
| Mako | manifest 1.4.1; installed metadata 1.4.1.dev0 | MIT, distribution metadata | Retain notices; recorded version discrepancy is not hidden. |
| Markdown / MarkupSafe / Jinja2 | 3.10.3 / 3.0.3 / 3.1.6 | BSD-3-Clause for first two; Jinja metadata says BSD, with its own full license retained | Preserve upstream copyright/disclaimers; exact Jinja grant is in its dist-info license. |
| attrs / setuptools | 26.1.0 / 80.10.2 in runtime | MIT, distribution metadata; setuptools vendored exceptions below | Runtime contains these ancillary packages even though app requires no PyPI service client; retain notices. |
| setuptools bundled validate-pyproject / fastjsonschema | Versions not established by bundled NOTICE | MPL-2.0 / BSD-3-Clause, `lib/python3.13/site-packages/setuptools/config/NOTICE` and `_validate_pyproject/NOTICE` | Preserve both full notices and covered-source obligations; bundled code is not all MIT. |
| packaging | 26.3, distribution metadata | Apache-2.0 OR BSD-2-Clause | Preserve supplied licenses; determine applicable attribution route in redistribution review. |
| AppImage type-2 runtime | commit `75849dce7cc37e4319b633df1f116ca895c71a12` | Runtime MIT plus musl/libfuse/squashfuse/zstd/zlib terms in `packaging/licenses/appimage-runtime.LICENSE` | Preserve full combined notice; verify static-link/source obligations for the exact launcher. |
| Build/CI tools | host setuptools 78.1.1; actionlint 1.7.12; Flatpak 1.16.6 | setuptools/actionlint MIT; Flatpak/OSTree/SquashFS/binutils have their own LGPL/GPL/component terms | These build tools are not copied by the builder as app dependencies. Independently bundled runtime tools keep their own obligations. |

Other retained runtime groups include media codecs, Rust/native dependencies,
Mesa/Vulkan components, dictionaries and additional fonts. Their notice locations
are indexed in the machine-readable inventory; exact SPDX mapping, payload scope,
patent/codec restrictions where applicable, and corresponding-source/attribution
verification remain **UNRESOLVED**, not implicitly Apache-2.0 or cleared.

## NOTICE decision

A project-specific root [NOTICE](../NOTICE) is included. This is an attribution
record, not an additional license. The app is not an Apache Software Foundation
project; ASF-internal policies are not treated as a requirement to add headers
to every file. Apache-2.0 section 4(d) requires preservation of supplied upstream
NOTICE attributions when applicable, rather than inventing a notice for every
dependency. See the [license text](https://www.apache.org/licenses/LICENSE-2.0.txt).

The runtime `share/licenses/` subtree contains two files named NOTICE: CUPS and
e2fsprogs. A whole-runtime filename scan also found two setuptools NOTICE files
under `lib/python3.13/site-packages/setuptools/config/` and its
`_validate_pyproject/` subdirectory, with MPL-2.0/BSD-3-Clause embedded-code
attributions. Both remain at their upstream paths and were verified byte-for-byte
in the final AppImage. CUPS's
2,375-byte notice is appended verbatim to the project NOTICE, including its
upstream exceptions; e2fsprogs's full notice remains in the runtime and is indexed
by path. GNOME Project artwork attribution is taken from the retained Adwaita
COPYING file. No author email, personal address, invented ownership or legal
entity detail was added to project-authored notices. Existing upstream texts
remain unmodified in the runtime; they are not sanitized or rewritten.

Both Flatpak and AppImage receive the project LICENSE and NOTICE. Flatpak's
GNOME runtime remains separately supplied. AppImage retains all upstream license
files and makes 1,453 absolute license links relative inside its copied runtime,
so notices resolve after relocation without reading host `/usr`. The build
rejects missing targets or absolute targets outside the runtime license tree.
Notice byte preservation and readable links are checked on the actual final
AppImage, not inferred from source alone.

## Remaining redistribution gates

**Application license selection: CLEARED — Apache-2.0.**
**Dependency redistribution clearance: BLOCKED / NOT VERIFIED.**

Before publication, complete binary-to-source mapping, exact dependency license
and attribution review, the remaining FreeType contributed-code review, LGPL/GPL source and
relinking/source-offer obligations, and the AppImage static launcher review.
Retaining notices and an Apache application LICENSE does not complete these
checks. Exact-runtime security advisories are a separate unresolved gate.
No dependency license was changed. No public distribution was authorized.

The Python wheel backend minimum is now setuptools 77 because PEP 639 SPDX
license strings and `project.license-files` require that support; see the
[setuptools documentation](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).
Canonical Flatpak/AppImage builds still do not install pip dependencies.

## Publication-clearance review (supersedes the gates above)

This is a technical redistribution review, not legal advice. Application source
license clearance is distinct from history/privacy and package clearance.

| Distribution | Decision | Boundary |
|---|---|---|
| Current source tree | **CLEARED** | Project-authored Python, CSS/themes, SVG, metadata, docs and fixtures; preserved upstream license texts retain their grants. Existing Git history is separately BLOCKED. |
| Flatpak application bundle | **CLEARED** | Only application source/resources and project LICENSE/NOTICE; no runtime libraries or Python packages embedded. GNOME Platform 50 is obtained separately. This does not approve republishing the runtime. |
| AppImage | **BLOCKED** | Bundled runtime, utilities, fonts, codecs and static launcher require the unresolved actions below. |

The authoritative component inventory for this phase is
[rc1-redistribution-inventory.json](validation/rc1-redistribution-inventory.json).
It indexes all 404 runtime build-manifest modules with exact primary source refs,
all 2,231 regular ELF payload paths, 21 Python distribution metadata records
(including setuptools vendoring), and all notice groups. The previous
[notice index](validation/rc1-license-inventory.json) remains an upstream notice
hash catalog, not a second clearance list. `common/` is a shared-text store,
not a dependency. Full file hashes, links, ELF NEEDED edges, all nested source
records and notices are reproducibly generated by `scripts/inventory-appimage.py`
into ignored local evidence. A manifest module may be build-only or pruned:
**unknown payload ownership is REVIEW REQUIRED, never evidence of shipping or
absence. A definitive component-to-source SBOM is still blocked.**

All runtime rows below are host-provided for native source use; separately
provided by Flatpak's runtime (**NOT REDISTRIBUTED** in the app bundle); and
bundled by AppImage where the stated payload was observed. Versions/source refs
are in the authoritative inventory and selected-component table above. License
copies and copyright notices must accompany bundled copies; named exceptions
and vendored terms survive the enclosing project's license. Status codes:
CLEARED, ATTRIBUTION REQUIRED, LICENSE TEXT REQUIRED, SOURCE OBLIGATION,
REVIEW REQUIRED, NOT REDISTRIBUTED. Multiple obligations can apply to one row.

| Included component / family | Actual payload evidence | License route / copies and attribution | Source / other obligation | Status |
|---|---|---|---|---|
| Python 3.13.15 and stdlib | `runtime/bin/python3*`, `lib/python3.13` | PSF plus stdlib subcomponents; retained Python notices | Verify subcomponents individually; no blanket PSF assumption | REVIEW REQUIRED |
| GTK4 4.22.5, libadwaita 1.9.4, GLib 2.88.3, Pango 1.57.1, PyGObject 3.56.3 | Shared libraries, GI typelibs, Python GI extension | LGPL, with source-level version/per-file exceptions; existing copies retained | Exact corresponding source, patches, build instructions; replacement/relinking route | SOURCE OBLIGATION |
| Cairo 1.18.4 / Pycairo 1.29.1 | Cairo library / Python extension | LGPL or MPL-1.1 alternatives; copies retained | Select and implement a route; do not impose both alternatives | SOURCE OBLIGATION |
| FreeType 2.14.3 | `libfreetype.so.6.20.6` | FTL selected; new exact `docs/FTL.TXT` and NOTICE acknowledgement | Main text gap fixed in rebuilt artifact; contributed-code terms still need reconciliation | REVIEW REQUIRED |
| HarfBuzz 11.4.5 / fontconfig 2.17.1 | Shared libraries | Old MIT / permissive copyright notices retained | Review per-file exceptions; no blanket source offer | REVIEW REQUIRED |
| glibc 2.42, GnuTLS, libgcrypt, libgpg-error, libffi and other LGPL libraries | Loader and shared libraries | Component-specific LGPL and exceptions; copies retained | Corresponding source and permitted replacement | SOURCE OBLIGATION |
| bash, coreutils, grep, sed, readline, gettext utilities, e2fsprogs/ext2fs | Executables, Python readline extension and shared libraries actually present | GPL family, plus per-library exceptions (e.g. e2fsprogs); NOTICE retained | Exact source including distribution patches/build scripts; choose applicable GPL delivery method | SOURCE OBLIGATION |
| GStreamer 1.26.11 and plug-ins / FFmpeg 7.1.3 | `gstreamer-1.0/*.so`, `libavcodec.so.61.19.101` and related libraries | LGPL/GPL configuration-dependent; upstream terms retained | Build flags and plug-in grants not proven by a COPYING filename; source and codec review | REVIEW REQUIRED; SOURCE OBLIGATION |
| OpenSSL 3.5.8 / CUPS 2.4.12 | `libssl.so.3`, CUPS libraries | Apache-2.0 and component exceptions; exact CUPS NOTICE preserved | Verify ancillary grants; no Apache source-offer requirement | REVIEW REQUIRED |
| NSS / NSPR / bundled validate-pyproject | Native libraries / setuptools Python code | MPL-family/per-file terms; validate-pyproject MPL-2.0 notice retained | Make covered source available and state how recipients obtain it; identify versions/patches | SOURCE OBLIGATION |
| Mesa/Vulkan, libdrm, image libraries (PNG/JPEG/WebP/JXL/TIFF), compression (zlib/zstd/bzip2/xz/Brotli) | Libraries and loaders in ELF inventory | Predominantly permissive but exact components/exceptions differ; existing copies retained | Resolve ownership and selected source grants; do not label whole family MIT | REVIEW REQUIRED |
| Adwaita icon theme 50.0 | `share/icons/Adwaita` | LGPL-3.0 OR CC-BY-SA-3.0-US; GNOME Project credit and upstream copies retained | Select route, preserve credit/link and adaptation/share-alike requirements if applicable | REVIEW REQUIRED |
| Adwaita/Cantarell/Noto/Liberation/DejaVu/FreeFont/TeX Gyre font families | `share/fonts` files | OFL, Bitstream/DejaVu, GPL with font exception, GUST and other per-font terms | Confirm each actual font's grant/reserved names; GPL font exception does not erase font-source duties | REVIEW REQUIRED |
| attrs, Mako, Markdown, MarkupSafe, Jinja2, packaging, setuptools | 9 top-level dist-info records | MIT/BSD/Apache alternatives as recorded; upstream texts retained | Mako manifest 1.4.1 vs installed 1.4.1.dev0 remains explicit | REVIEW REQUIRED |
| setuptools vendored packages (12 additional dist-info records) | `_vendor/*dist-info`, plus config notices | Includes autocommand 2.2.2 LGPLv3, importlib_metadata Apache-2.0, MIT and dual-license packages | LGPL source duty also applies to copied Python source; exact notices checked separately | SOURCE OBLIGATION; REVIEW REQUIRED |
| AppImage type-2 launcher, pinned commit in runtime lock | Executable prefix outside SquashFS | MIT launcher; static musl/libfuse/squashfuse/zstd/zlib named by upstream | Exact static dependency versions and full combined notices/relinkable build materials absent; hyperlinks alone do not satisfy copies | LICENSE TEXT REQUIRED; SOURCE OBLIGATION |
| Host build tools | setuptools 78.1.1, Flatpak 1.16.6, SquashFS, binutils, actionlint 1.7.12 | Build/test-only installations are not copied by these builders | No obligation merely from invoking a tool; independently bundled versions above are a separate case | NOT REDISTRIBUTED |
| Test tooling | Python unittest, Gio; CI PyYAML/Xvfb/dbus/metadata tools | Host/CI supplied; two project-authored validation helpers ship | No third-party test package is added to the app bundle | NOT REDISTRIBUTED |

### FreeType resolution and precise remaining limit

Upstream [FTL at the exact pinned commit](https://github.com/freetype/freetype/blob/0a0221a1347e2f1e07c395263540026e9a0aa7c7/docs/FTL.TXT)
is preserved byte-for-byte (SHA-256
`5a5ee54c5001bbad1cdc1a57cc3dd4c42199b2da09d39c7ee41fab002d02967f`).
AppImage packaging adds it beside the existing license overview at
`runtime/share/licenses/freedesktop-sdk/freetype/docs/FTL.TXT`; project NOTICE
acknowledges the FreeType Team. FTL binary distribution requires that
acknowledgement. Source redistribution additionally requires intact license and
copyright and documentation of modifications. The alternate GPL text is not
required by the selected FTL route. No unverified copyright year was invented.

The runtime manifest identifies the downstream
`patches/freetype/enable-cleartype-subpixel.patch`. We neither rebuild nor change
FreeType. Its retained overview is byte-identical to the exact upstream version.
That overview also names BDF/PCF/hash, gzip and HarfBuzz-derived file terms,
but those component texts are not all in its notice subtree. Therefore the
**main FTL text/acknowledgement gap is resolved by final package byte
verification; complete FreeType contributed-code clearance remains REVIEW
REQUIRED**. Flatpak's application does not ship FreeType or this supplement.

### Reciprocal-license obligations and linkage

The ELF inventory records dynamic dependencies for the bundled native payload;
AppRun invokes the bundled loader with a replaceable extracted runtime. That
mechanism helps replacement, but an executed modified-library/relink test and
complete corresponding source delivery have not been established. For
LGPL-2.1 section 6, choose a valid compliance option: suitable shared-library
replacement or relinkable application materials where applicable, library
source (including modifications), license/notice copies, and no prohibition on
reverse engineering to debug modifications. Merely being dynamically linked
does not waive library redistribution obligations. Static libfuse in the launcher
needs particular attention: source URLs alone do not establish a relinkable
build or the exact embedded version.

For GPL executables bundled as separate programs, Apache application code is
not automatically relicensed by aggregation. GPLv2 section 3 / GPLv3 section 6
still require compliant corresponding-source delivery for those programs,
including patches and build scripts. Online distribution can use a qualifying
source-download method; do not casually substitute an upstream homepage or an
unfulfilled written offer (which carries its own duration/recipient duties).
LGPLv3 additionally uses GPLv3 terms, with combined-work/relinking provisions.
For MPL-2.0 sections 3.1–3.3, covered source must be available under MPL and
recipients informed how to obtain it; separate larger-work files can retain
Apache-2.0. MPL-1.1 has its own text and requirements and is not silently treated
as MPL-2.0. Modified-source identification must follow each applicable grant.

These conclusions use the retained full GPL/LGPL copies in the inspected runtime,
[GNU LGPL-2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html),
[GNU GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html), and
[Mozilla MPL-2.0](https://www.mozilla.org/en-US/MPL/2.0/).
Retained source-tree notices can mention CDDL/EPL and many test-only components;
no authoritative mapping yet proves whether any such covered code is in the
shipped binaries. Those are REVIEW REQUIRED, not asserted absent or incompatible.
No source offer has been made and no compliance route is claimed implemented.

### NOTICE and ownership decision

Project NOTICE's CUPS body remains byte-identical to the runtime NOTICE. Its
inclusion in the app-only Flatpak is useful common documentation but not proof
that Flatpak embeds CUPS. Adwaita's upstream attribution names GNOME Project.
The FreeType acknowledgement now explicitly identifies the FreeType Team.
The e2fsprogs and both setuptools NOTICE files remain at their upstream paths.
No speculative owner, address or source-offer promise was added. The static
launcher lists external license URLs; contrary to any reading of earlier notes,
that file is **not a complete copy of all static-library license texts**.

Tracked SVG and CSS/theme palettes are original project material; Git history
shows their creation in this project and no contrary attribution evidence.
No raster screenshots, fonts, sound, external logos or executable binaries are
tracked in the source tree. Synthetic fixtures and path-free validation JSON are
project-generated. Screenshots and real diagnostic exports remain in ignored
local output. This source-provenance review is not an independent ownership
attestation for third-party runtime assets.
