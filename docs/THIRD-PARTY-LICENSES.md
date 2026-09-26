# Third-party licenses

The authoritative per-artifact index is generated from the actual AppImage:
`dist/THIRD-PARTY-LICENSES.md`. A copy travels inside the AppImage at
`usr/share/licenses/acelip-scope/compliance/THIRD-PARTY-LICENSES.md`.
It identifies components, versions where established, upstreams, full-text
locations and explicit unresolved entries. The companion component JSON and
CycloneDX SBOM include all payload files and their hashes.

Acelip Scope's [LICENSE](../LICENSE) and [NOTICE](../NOTICE) apply to its own
material and preserve third-party attributions; they do not relicense upstream
code or assets. Runtime and launcher library entries concern AppImage; Flatpak
supplies the runtime separately. Exact supplemental texts and source hashes are
in `packaging/compliance/license-assets.json` and `source-archives.json`.

See [APPIMAGE-THIRD-PARTY.md](APPIMAGE-THIRD-PARTY.md) for the reviewed obligations,
FreeType/launcher evidence and remaining source/relinking blockers. Neither a
valid SBOM nor the presence of a COPYING file constitutes redistribution
clearance. **AppImage redistribution remains BLOCKED.**
