# Validation in progress

The disposable Docker validator is being completed on 2026-10-01. Stable Paper 26.2 build 129, Vanilla 26.3, persistence, encrypted backup and booting a restored world, MariaDB authentication/persistence and static NGINX serving have passed on Linux ARM64. Velocity startup defects found by runtime checks were fixed; forwarding login and failure-path backup proof remain in progress.

Run `scripts/validate local` and `scripts/validate fullDocker --output /tmp/minecraft-proof`. Network-only diagnosis is available with `--scenario network`. The final committed report will include timestamps, commands, exact identities and limitations. This interim report does not claim review readiness.
