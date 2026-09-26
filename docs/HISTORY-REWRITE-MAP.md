# Approved RC1 history rewrite map

**History rewrite: COMPLETE. Publication-history privacy: PASS.**
Acelip Scope 1.0.0-rc1. Explicit user approval: 2026-09-26.
Safety reference recorded at **2026-09-26T18:42:14Z**.

| State | Commit/reference |
|---|---|
| Pre-rewrite HEAD | `c9b7e8072bb35ee84653d21dda1072c65cdbcd46` |
| Immediate post-rewrite HEAD / new artifact source | `6c4c33fcbf435879e07f086ba4a92130b8b4d338` |
| Current branch | `codex/rc1-publication-clearance` |
| Retained safety branch | `backup/pre-publication-history-rewrite` → pre-rewrite HEAD |
| Pre-rewrite Book checkpoint | `179eb59f-ba05-46bc-ac11-a2d350dd1a5c` (readback verified) |
| Final documentation HEAD / completion checkpoint | Recorded after this report's commit in the verified Book checkpoint and task handoff |

The post-rewrite SHA above is the tip immediately after the atomic ref update,
not the subsequent documentation commit. Rebuilt artifacts name that clean tip.
The checked-out tree before/after the rewrite has the **same** tree object:
`dd831166e7196ccc427e7a3244f6777fb113b069`.

## Scope and exact changes

The authority is the nine findings in the pre-rewrite publication report and
[its original audit evidence](validation/rc1-history-audit.json). No new finding
was inferred from generic LUCY, username or network search terms. Exact original
lines were recovered from the recorded blobs and checked against the report's
line numbers and every listed containing commit. The sensitive strings are
retained only in ignored local recovery evidence, not copied into this report.

**Nine distinct blobs**, three paths, 28 affected original commits, and 53 file
instances across those commits changed. Because parent IDs propagate, 42 of 43
commits receive new IDs; the original root remains unchanged. No commit is
squashed, dropped or reordered, and no file is deleted.

| Context | Approved replacement |
|---|---|
| Seven historical README variants | Replace only the local `cd` argument with `/path/to/LUCY-Diagnose` |
| One historical validation document | Replace only the checkout literal with `<local-checkout>` |
| One historical package smoke helper | Replace the machine-path origin expression with `'packaged'`; preserve its existing relative module-containment assertion verbatim |

The helper already asserts that the imported module lives beside the packaged
script. Removing its redundant machine-specific origin expression preserves that
assertion; no current helper or application source changed. Historical LUCY
Diagnose product naming and all unrelated content remain unchanged.

| Historical path | Original line | Old blob | New blob |
|---|---:|---|---|
| `README.md` | 19 | `a0ecc6bc571784a9ebcfab31505a46b8b755a4d2` | `e25ed1039e1e2ccd7cbdc1b51f5fd152273d7c49` |
| `docs/V1.2-VALIDATION.md` | 3 | `9fe1c77d389da27ba62d93f11f5d92b067213099` | `68f92219de1ea5f4e9f5ea256b20306d9734ddac` |
| `README.md` | 22 | `17baaef8754c7969c9c7861fa8cc1ab164938619` | `f5682d6047a46576853ae647c077945ed2b789d2` |
| `README.md` | 23 | `393c3f4032589e5a3e2f13324df7c8d52272a829` | `733ffad17cae2585d1ca702652676c4d1591dab2` |
| `scripts/validation/package-smoke.py` | 42 | `e999d7fb88f0d9ce6f9a4e17d138dc602cb5d4b6` | `d9d96c318a9ee59e375de95b56e40994ac69e30d` |
| `README.md` | 13 | `47e78eea7742e73e4514a1fb18f2543ea543f96c` | `728731f709d8885ec9a40bd687d7231f251b923f` |
| `README.md` | 13 | `6d8aa8e5afa65ac7768d306339d3f26ee4274f96` | `91392cb3bd72c503adfe320411549001df24f0d2` |
| `README.md` | 13 | `ca225e14b9cd1762c4dacc636335d87e5ee26e22` | `814ffd86932d2753f5f784e558d2df0d11da4f92` |
| `README.md` | 13 | `46a8025a36e7ea85a3e871d26fcc62ef545938ba` | `b002531023f601dbcdf5278ea083a8d2242d376b` |

## Publication refs and old-to-new mappings

Exactly these six branches were updated in one compare-and-swap transaction:

| Branch | Old tip | New tip immediately after rewrite |
|---|---|---|
| `main` | `a1f5c91fbd2c1d1a979b75f1542e984fd4ab4b9d` | `aa7ca45bd72b7808dfaf00c6ce160be279db7b20` |
| `codex/v1.4-linux-validation` | `ac51ab16d777060209cbe3236e2bb747aa88aab1` | `de5ee66c95be15ebb947b0cfc5fde5a58796bd4e` |
| `codex/v1.5-packaging` | `b085a9f42d7e5c6f87777d75fa2e0a65140fd562` | `fd9922e23f235ea0f764d5e4656be2dea173d458` |
| `codex/v1.6-public-release` | `ab1c24c07b5b3a09c957ad5934d3befa147227fc` | `1ae69ef8b105c6d40f2581649201f6bb19782c09` |
| `codex/rc1-release-prep` | `24b96ce9fd670276f870294a6199f220bc843fef` | `51088c058d1746f65da798d5a8b9a06adcebbfdb` |
| `codex/rc1-publication-clearance` | `c9b7e8072bb35ee84653d21dda1072c65cdbcd46` | `6c4c33fcbf435879e07f086ba4a92130b8b4d338` |

The [verification record](validation/rc1-history-rewrite.json) contains the complete
**43-entry old-to-new commit map**, including the unchanged root, every milestone
and all nine blob mappings. An unchanged map entry is intentional.

No tags or remote refs existed. No tag, remote, push or release was created.
The backup branch is retained at the exact original HEAD. `refs/codex/*` contains
private application tree snapshots; these refs were not manually rewritten.
Neither those private refs nor backup refs belong to the publication ref set.
Local reflogs and old objects were preserved; no garbage collection, aggressive
pruning, reflog expiration, reset or safety-reference deletion was performed.

**Do not publish the backup/private refs or use a mirror/all-branches push.**
A future separately authorized publication must select reviewed publication refs.
An unscoped `--all` audit still sees the deliberately retained old private
history; that is expected and is not a claim that all local objects were erased.

## Method and preservation proof

`git filter-repo` was not installed. No package was installed and `filter-branch`
was not used. For this small exact-blob scope, native Git plumbing provides
byte-level control:

1. Validate the clean pre-HEAD, safety ref, exact nine blob IDs, source paths,
   line contents, occurrence counts and containing-commit sets.
2. Write only the approved replacement blobs. Recursively reconstruct tree
   objects with the same modes/names/order, substituting only those blob/path
   pairs. Build commits in parent-first order by replacing only `tree` and
   `parent` headers in raw commit bytes; reject signed/mergetag cases rather
   than silently invalidating signatures. No such signatures were present.
3. For **every one of 43 commits**, compare complete path sets, modes and blob
   IDs; require that all deltas exactly match the nine approved replacements.
   Compare raw messages and all non-tree/non-parent headers byte-for-byte,
   and compare mapped parent lists in their original order.
4. Verify identical current tree IDs. Run both existing history scanners on
   candidate publication tips before changing refs. The candidate tip was
   temporarily dangling, as expected; integrity checking found no corruption.
5. Atomically update exactly the six refs with their expected old IDs, also
   verifying the backup ref in that transaction. Re-run audits and integrity
   checks after the update. No checkout/reset was needed because the tip tree
   stayed identical.

Ignored local evidence is under `var/history-rewrite/`: exact private redaction
plan, sanitized full mapping, procedure, candidate/post-rewrite/final audits,
atomic-ref transaction, test/build/GTK logs and package comparisons. Procedure
and audit-wrapper SHA-256s are recorded in the committed verification JSON.
These tools changed scope only, not scanner patterns or exclusions.

## Audit, integrity and tests

**HISTORY PRIVACY AUDIT: PASS** for all history reachable from the six publication
refs. Immediately after rewrite: 43 commits, 226 trees, 470 blobs; zero remaining
approved path literals and zero findings from both existing `audit-history.py`
and `audit-public.py` logic. Full historical path associations include renamed
and deleted files. Raw commit data and all blobs are scanned. The final
additional documentation commit is audited again before checkpoint completion.

Secret review: no real credentials found. Before/after provider, auth, assignment,
private-key-marker, MAC and synthetic-host matches are unchanged and retain their
reviewed fixture/tool meanings. AWS/SSH/JWT/database-userinfo/private-username
patterns remain empty. Public upstream license contacts and the approved
GitHub noreply metadata remain acceptable. Dedicated gitleaks/trufflehog/
detect-secrets remain unavailable; no unavailable scanner is claimed executed.

Author/committer names, email addresses, dates/timezones, messages and other raw
metadata are **byte-identical across all mapped commits**. Existing public
pseudonymous identity remains as documented in PUBLICATION-CLEARANCE.md.

`git fsck --full --strict`: **PASS**, exit 0, no errors after refs moved.
The retained safety ref resolves to the original HEAD; current source remains
reachable and readable. Current-tree privacy: **PASS**, zero findings. Full
before/after suites: **315 regression + 4 Gio**, all passing. No test or feature
was added. The final documentation tree differs only in the files required to
record this rewrite and current validation; application/build/test source remains
identical to the pre-rewrite tree.

For future re-audits, use the explicit six refs above as `git rev-list` / `git log`
roots. The local `audit-publication.py` wrapper substitutes those roots for
`--all` in the existing scanners and records both included/excluded ref sets.
Do not weaken scanner rules or interpret the intentionally retained backup as
publication history.

## Package provenance and remaining gates

Both formats were built twice from clean post-rewrite HEAD. The current
[execution record](validation/rc1-history-rewrite.json) and
[publication report](PUBLICATION-CLEARANCE.md) contain updated hashes and real
packaged GTK acceptance outcomes. Only the packaged `_build.json` changed from
the previous pair: it records the new source commit and that commit's preserved
epoch. All other package payload bytes, notice copies, links and Flatpak sandbox
metadata are identical. Container bytes/timestamps consequently changed.
Old artifacts and checksum claims remain preserved as historical evidence.

Source licensing **CLEARED**; Flatpak application redistribution **CLEARED**;
AppImage redistribution **BLOCKED**. This rewrite does not resolve AppImage
source/relinking/notice obligations or runtime advisories. Remote creation,
homepage/support reachability, private vulnerability reporting, remote CI and
publication authorization remain blocked. The Book remains development backup
only; the final checkpoint is recorded/read back after the documentation commit.
