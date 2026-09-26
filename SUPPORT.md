# Support

The [repository/homepage](https://github.com/Acelip-Development/acelip-scope) and
[GitHub Issues](https://github.com/Acelip-Development/acelip-scope/issues) are public.
Use GitHub Issues for normal support, bug reports and questions. There is no
response-time guarantee. [RC1 is publicly released](docs/RC1-PUBLICATION.md) as source + Flatpak only;
AppImage is withheld pending redistribution/advisory clearance.

Security reports use
[GitHub private vulnerability reporting](https://github.com/Acelip-Development/acelip-scope/security/advisories/new).
Do not post vulnerability details or secrets in public Issues. See
[SECURITY.md](SECURITY.md) for the confidential reporting process.

For ordinary troubleshooting, record version, package type, architecture and
backend from About/`--build-info`, the scan mode, expected behavior, observed
coverage state and reproduction steps. Include only a reviewed sanitized report
or narrowly cropped non-sensitive screenshot. Never share credentials, raw
journals or personal network inventories. Security issues follow [SECURITY.md](SECURITY.md).

A missing diagnostic tool, permission-denied SMART read or Flatpak sandbox limit
is often expected coverage, not a system failure. Acelip Scope does not elevate to work
around these limits. Core diagnostics run offline; AI clients are external and
optional. A userspace/container result does not certify hardware or desktop
services. See the [compatibility matrix](docs/LINUX-COMPATIBILITY.md) and current
[release checklist](docs/RELEASE-CHECKLIST.md) before assuming support.
