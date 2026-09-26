# AppImage size audit

V1.5 measured **358,291,960 bytes** (about 358 MB decimal). Its pinned GNOME
Platform copy contains **1,089,426,777 bytes** of regular-file payload before
SquashFS compression. The input inventory is in
[validation/v1.6-runtime-size.json](validation/v1.6-runtime-size.json).

| Major input group | Uncompressed bytes |
|---|---:|
| Native libraries (`lib/x86_64-linux-gnu`) | 661,643,459 |
| Python 3.13 and modules | 70,570,311 |
| Locale archive | 58,384,366 |
| Fonts | 51,738,056 |
| Thesaurus data | 21,597,799 |
| Internationalization data | 15,748,889 |
| Glycin image loaders | 14,066,168 |
| Icons | 13,404,406 |
| License notices | 9,528,924 |

Two WebKit engines contributed about 204 MB and their JavaScriptCore libraries
about 69 MB uncompressed. LUCY uses neither a webview nor JavaScript. A read-only
ELF dependency audit found their consumers only in the WebKit helper families
and Yelp help viewer; LUCY does not use Yelp either.

V1.6's explicit prune manifest removes those libraries, typelibs and consumers
from the staged AppImage copy only. It never edits the installed GNOME runtime.
Every remaining ELF binary is checked for dependencies on removed library names;
a missed consumer stops the build. GTK/libadwaita, Python/GI/Cairo, fonts, icon
resources, text/image support and all runtime license notices are retained.
No new dependence on random host libraries was introduced to reduce size.

The first v1.6 candidate measured **261,536,248 bytes**, a reduction of
**96,755,712 bytes (27.0%)**. Final artifact size, smoke results and exact checksum
are recorded in [V1.6-VALIDATION.md](V1.6-VALIDATION.md), because later source and
notice changes can shift the last few kilobytes.

Further pruning is deliberately deferred: generic GTK/Gio modules, translations,
fonts, image codecs and their transitive dependencies can be selected dynamically.
Keeping that compatibility margin is preferable to a smaller unvalidated image.
The package still uses the host compositor and normal host font configuration;
it bundles its own interpreter, loader and GUI libraries. See PACKAGING.md.
