# Linux execution evidence

These are opt-in validation tools, never application startup hooks. Run them
only in environments you intend to inspect. They do not install host packages.

```sh
python3 scripts/validation/validate-linux.py --environment host --output var/v14-ubuntu
python3 scripts/validation/pull-userspace.py registry-1.docker.io library/fedora 44 var/v14-environments/fedora
python3 scripts/validation/run-userspace.py --root var/v14-environments/fedora/rootfs --output var/v14-fedora --setup -- dnf -y install python3
python3 scripts/validation/run-userspace.py --root var/v14-environments/fedora/rootfs --output var/v14-fedora -- python3 scripts/validation/validate-linux.py --environment container --output var
```

Use the saved architecture-specific manifest digest instead of the tag to
repeat an image selection. Python with `tarfile.data_filter` and host Bubblewrap
are required. Fetch verifies SHA-256 manifests/layers, refuses whiteouts and
special files, and rewrites absolute symlinks within the image. Extraction does
not preserve ownership, directory modes, privileged bits or capabilities;
package verification can therefore find extraction artifacts. This is not a
replacement for an OCI runtime. Setup uses root only in an unprivileged user
namespace and can encounter unmapped ownership/capability failures. Record
those failures; do not call a partially installed image a healthy workstation.

Normal runs mount the image and source read-only, use private process/network
namespaces and empty sysfs, and expose no host home, session bus, block devices
or GPU. Only the chosen output directory is writable. Setup explicitly permits
image writes and network to obtain test dependencies. All generated evidence,
images, setup logs and screenshots belong in ignored `var/`.

`--wayland` exposes the current compositor socket only. A guest GTK client
rendering on the host compositor is **not another desktop session**, and cannot
validate Fedora Workstation, KDE, portal/audio services or hardware. Do not set
fake desktop identities to claim desktop validation.

`validate-linux.py` executes every scan, normalized package/service/sensor
queries, two live samples, cancellation/deadline checks, and writes sanitized
Markdown/JSON exports plus `evidence.json`. Its execution PASS means no collector
crashed, not that every feature is supported or the machine is healthy. Review
per-check severity and coverage. Raw local artifacts still need review before
sharing; commit only a compact identity-free evidence summary.

Additional acceptance commands:

```sh
python3 scripts/validation/validate-gui.py --label ubuntu-gnome
python3 scripts/visual-check.py
python3 scripts/validation/run-userspace.py --root var/v14-environments/arch/rootfs --output var/v14-missing-tools -- /usr/bin/python3 scripts/validation/validate-linux.py --environment container --missing-tools --output var
```

GUI acceptance uses actual scan controls, checks pause/resume and every theme's
saved preference, exercises privacy/AI consent, saves both preview formats to QA
paths, and captures only the app widget tree. The native interactive file chooser
is not automated. The separate visual check renders all 13 themes using clearly
labeled sample data. `--missing-tools` is an explicitly injected empty PATH, not
a claim about the unmodified image. Existing native package positive/negative
controls run in normal CLI acceptance; all run results retain coverage limits.
