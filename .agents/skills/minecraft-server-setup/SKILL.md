---
name: minecraft-server-setup
description: Set up and verify this repository's Minecraft Docker deployment, or diagnose its startup prerequisites. Use for fresh server startup; route existing worlds to the migration guide.
---

# Minecraft server setup

Read the root README for commands and distribution choices. Use the repository's `scripts/minecraft` entrypoint from its absolute path; it resolves paths independently of the current directory.

Check for `.state/settings.json`, legacy deployment paths, or existing world data first. Existing deployments need [the migration guide](../../../docs/migration.md) and a backup/restore rehearsal. Preserve their data and credentials.

Python 3.11+, Docker Engine 28+, Compose plugin v2 or v5, sufficient memory and disk, and Docker access must already exist. Inspect prerequisites; report the missing prerequisite if unavailable. Host package installation, firewall/DNS changes, and unrelated Docker resources are outside this setup skill.

Obtain explicit EULA acceptance from the user's request before passing `--accept-eula`. Acceptance for an isolated validation run applies only to its disposable test servers. An absent response is not consent. [START.md](../../../START.md) supplies a reusable request with explicit acceptance.

For fresh setup, choose the user's distribution and topology, then run `setup --accept-eula --start` with their options. Default stable Paper differs from the latest Minecraft release; current Vanilla is an explicit distribution choice. Velocity requires Paper and modern forwarding. Select optional profiles only when wanted. Reuse identical setup options on repeat runs; investigate conflicting options rather than deleting `.state/`.

Completion requires `doctor`, healthy `status`, an actual `scripts/status` protocol response at the selected gameplay address, and working `command list`. If scheduled backups were requested, inspect backup logs for a completed snapshot and the next interval. Use the backup/restore procedure in [operations.md](../../../docs/operations.md) when the user requests recovery verification. Keep generated secrets out of transcripts and source control.

Report the exact software/image identities, address, service health, selected profiles, persistent data and credential paths, and any failed check. A Compose configuration or a running process alone is not completion. For template development, `scripts/validate fullDocker` implements the isolated runtime contract and exports reviewable evidence; it never validates a user's arbitrary plugins.
