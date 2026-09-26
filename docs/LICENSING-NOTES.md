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
| FreeType | 2.14.3, manifest; `freedesktop-sdk/freetype/LICENSE.TXT` | FTL OR GPL-2.0-or-later; additional contributed-file terms | FTL requires documentation acknowledgement. Runtime retains the license overview but the referenced `docs/FTL.TXT` and `docs/GPLv2.TXT` are absent from this notice subtree; obtain/reconcile complete selected-route terms before publication. No clearance claimed. |
| glibc / loader | 2.42, manifest; `freedesktop-sdk/glibc/LICENSES` | LGPL and per-component terms | Corresponding source, relinking/replaceability and bundled utility scope need review. |
| OpenSSL | 3.5.8, manifest; `freedesktop-sdk/openssl/LICENSE.txt` | Apache-2.0 plus retained component notices | Retain notices and review any additional source-level attribution requirements; no separate NOTICE found in this runtime subtree. |
| CUPS | 2.4.12, manifest; `freedesktop-sdk/cups/NOTICE` and `doc/help/license.html` | Apache-2.0 with CUPS exceptions and embedded-code attributions | Exact CUPS NOTICE included in root NOTICE; original also retained. Exceptions are CUPS-specific, not changes to the application Apache license. |
| e2fsprogs | 1.47.4, manifest; `freedesktop-sdk/e2fsprogs/NOTICE` | GPL-2.0 with library-specific LGPL/BSD/MIT terms | Preserve full upstream NOTICE; exact shipped libraries/tools and source obligations need clearance. |
| Adwaita icons | 50.0, manifest; `adwaita-icon-theme/COPYING*` | LGPL-3.0 OR CC-BY-SA-3.0-US, as stated upstream; attribution: GNOME Project | Attribution included in NOTICE; retain upstream terms and reconcile selected route/assets. |
| Cantarell / Noto Emoji / other runtime fonts | Cantarell 0.303.1; Noto Emoji 2.051, manifest | Inspected font notices include SIL OFL-1.1; other fonts retain their own notices | Preserve font copyright/license and reserved-name requirements; not project-owned artwork. Audit remaining font families separately. |
| Mako | manifest 1.4.1; installed metadata 1.4.1.dev0 | MIT, distribution metadata | Retain notices; recorded version discrepancy is not hidden. |
| Markdown / MarkupSafe / Jinja2 | 3.10.3 / 3.0.3 / 3.1.6 | BSD-3-Clause for first two; Jinja metadata says BSD, with its own full license retained | Preserve upstream copyright/disclaimers; exact Jinja grant is in its dist-info license. |
| attrs / setuptools | 26.1.0 / 80.10.2 in runtime | MIT, distribution metadata | Runtime contains these ancillary packages even though app requires no PyPI service client; retain notices. |
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

The runtime contains two files actually named NOTICE: CUPS and e2fsprogs. CUPS's
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
and attribution review, the FreeType missing-text question, LGPL/GPL source and
relinking/source-offer obligations, and the AppImage static launcher review.
Retaining notices and an Apache application LICENSE does not complete these
checks. Exact-runtime security advisories are a separate unresolved gate.
No dependency license was changed. No public distribution was authorized.

The Python wheel backend minimum is now setuptools 77 because PEP 639 SPDX
license strings and `project.license-files` require that support; see the
[setuptools documentation](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).
Canonical Flatpak/AppImage builds still do not install pip dependencies.
