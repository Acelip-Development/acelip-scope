# Licensing notes

This is an informational inventory, not legal advice or a complete legal
clearance. **PUBLIC RELEASE BLOCKER: Application license not selected.** There
is deliberately no root LICENSE file. Neither a public repository nor a
`LicenseRef-proprietary` metadata placeholder selects or grants an application
license. The owner must approve licensing before public distribution.

## Project assets

The application Python/CSS, original theme palettes and simple SVG packaging
icon are project-authored assets in Git. No external raster art, downloaded logo,
AI-generated visual asset, sample music or sound recording was added in this
phase. Ownership/contribution provenance and the chosen grant still need owner
review. The new AppStream metadata declares CC0-1.0 for that metadata alone.
Normal UI icons come from the runtime/desktop Adwaita icon theme; their upstream
notices remain with the runtime. No font is claimed as project-owned.

## Main runtime/build components

| Component | Role | Known upstream license / evidence |
|---|---|---|
| Python / standard library | Core/runtime | PSF license and component notices in the pinned runtime's licenses; not a blanket license for all dependencies |
| GTK4 | GUI | LGPL-2.1-or-later, [official GTK overview](https://docs.gtk.org/gtk4/) |
| libadwaita | GUI widgets/appearance | LGPL-2.1-or-later, [official API documentation](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/) |
| PyGObject | Python GI bindings | LGPL-2.1-or-later, [official project documentation](https://pygobject.gnome.org/) |
| Pycairo | Graph rendering bindings | LGPL-2.1-only OR MPL-1.1, [official documentation](https://pycairo.readthedocs.io/en/latest/) |
| GLib/Gio, Cairo, Pango, HarfBuzz, fontconfig, FreeType | Transitive native GUI/text/IO libraries | Component-specific LGPL/MIT/BSD/MPL/FreeType notices; use the retained per-component files, not an inferred single license |
| glibc, bundled loader | AppImage native runtime | GNU LGPL/component terms; source/replaceability obligations require review |
| Adwaita icons, Noto/Cantarell/other fonts | Runtime icons/text fallback | Component-specific font/icon licenses retained under `runtime/share/licenses/`; fonts and notices are not pruned |
| AppImage type-2 runtime | Executable mount/extract launcher | MIT for runtime code; statically linked musl, libfuse, squashfuse, zstd and zlib have their own notices/terms, explicitly listed in the [pinned upstream LICENSE](https://github.com/AppImage/type2-runtime/blob/75849dce7cc37e4319b633df1f116ca895c71a12/LICENSE) |
| Flatpak/OSTree, SquashFS tools, binutils/readelf | Build-only tools | Upstream LGPL/GPL/component terms; tools are not copied into the application payload by the builder |
| setuptools | Optional source wheel build backend | Upstream MIT; canonical Flatpak/AppImage staging does not require pip installation |
| actionlint | Development/CI only | Upstream MIT; checksum-pinned download into ignored tooling directory |

`packaging/licenses/appimage-runtime.LICENSE` is the actual pinned runtime notice,
not a LUCY license. It is included in the AppImage. The AppImage keeps **all**
upstream GNOME runtime `share/licenses/` files (about 9.5 MB uncompressed) and the
runtime manifest; removed WebKit/JavaScriptCore/Yelp notices are also retained.
Flatpak applications use the separately supplied GNOME Platform with its own
notices. This inventory does not imply the entire platform is LGPL-only: the
runtime contains additional utilities/libraries with diverse licenses, including
copyleft components.

## Distribution gates

Before publishing, choose the application license, confirm ownership and public
publisher identity, and review the exact shipped dependency inventory. Retaining
license files alone is not proof that all corresponding-source, relinking,
static-linking or source-offer obligations are satisfied. Establish a compliant
source/notice distribution process for the exact runtime commit and AppImage
launcher, including its statically linked libraries. Review upstream security
advisories as a separate task; version pinning is not vulnerability clearance.

No dependency license has been changed or replaced, and no public-distribution
approval is implied by a passing build. [DEPENDENCIES.md](DEPENDENCIES.md) lists
required, optional, development-only and packaging-only dependencies.
