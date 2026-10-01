# One-prompt independent setup review

Publication note: this source-blind execution used archive `5cd63b7`, not the final `1b6a5ee` validation harness. Its genuine shipped-skill/START setup proof is distinct from the later independent full/cold review. Selected evidence is redacted; no fixture, generated state, secret value or unrelated host inventory is published.

Result: passed the requested disposable-server workflow. No setup-material or workflow finding reproduced. Review complete; no code changes or downstream dispatch.

The clean fixture `/tmp/minecraft-one-prompt-0ampoe4d` archived candidate `5cd63b7688058295198ac32a7f46062bf5d8c873`. Inputs read were the local setup skill, START.md, README.md, routed operations.md, and public CLI help. No implementation, tests, diffs, other reviews or builder proof were read. Explicit disposable EULA consent came from the supplied prompt. Native Codex executed the review, with GNU timeout bounding setup to 420 seconds and subsequent operator commands to 60 seconds. The review completed within its ten-minute cap.

## Setup and readiness

The host had Python 3.12.3, Docker Engine 29.8.0, Compose 5.5.1, arm64, about 50 GiB available memory and 29 GiB free disk. The fixture had no existing deployment state or world data. A socket bind selected free port 35673 before setup.

Command, also retained in [setup-command.txt](setup-command.txt):

```sh
timeout --signal=TERM --kill-after=15s 420s /tmp/minecraft-one-prompt-0ampoe4d/scripts/minecraft setup --accept-eula --distribution paper --memory 2G --bind 127.0.0.1 --port 35673 --profile backup --start --wait 360
```

Setup exited 0. Doctor reported valid configuration. Server status and Docker health were healthy. The backup sidecar was running and has no Docker healthcheck; its completed snapshot and six-hour sleep prove operational readiness. Only the backup optional profile was enabled. Docker published only `127.0.0.1:35673 -> 25565/tcp`; no RCON port was published.

Live `scripts/status --host 127.0.0.1 --port 35673` returned Paper 26.2, protocol 776, secure chat enabled, and 0/20 players. Authenticated `scripts/minecraft command list` returned `There are 0 of a max of 20 players online` and exited 0. These were direct checks, not setup-banner inference. See [protocol.log](protocol.log), [rcon.log](rcon.log), [status.log](status.log), [doctor.log](doctor.log) and [runtime.json](runtime.json).

## Runtime identities and heap

Server logs identify Paper `26.2-129-ver/26.2@9240f58`, API `26.2.build.129-stable`, and initial/max heap 2G. Container inspection confirms MEMORY=2G. Java reports Temurin `25.0.4+7-LTS`. The server reference and actual image ID are `itzg/minecraft-server:2026.9.2-java25@sha256:de5d1b1a83eba576f6c8a688fac2a3523ce457724cdebc8ea48d7818b74cdf6e` and `sha256:de5d1b1a83eba576f6c8a688fac2a3523ce457724cdebc8ea48d7818b74cdf6e`.

The backup base pin is `itzg/mc-backup:2026.9.3@sha256:3ff6a1e8fa15ca4e4440b118676cf58c611a4079d4da8fe792b04a9a13619f16`. Its running derived image is `minecraft-template-backup:3ff6a1e8fa15ca4e-1c6ea31fbca3`, actual image ID `sha256:651da33a96d3c7e07d82271e6a2170a68c94a19c7b6b22b414087edfae3dc5bd`. Snapshots report restic 0.19.1. See [server-logs.log](server-logs.log), [java-version.log](java-version.log) and [runtime.json](runtime.json).

Two extra diagnostic commands had limited results. RCON `version` returned its asynchronous checking message; exact Paper identity comes from runtime server logs. `docker top ... -eo args` failed because Docker requires a PID field. No JVM flag listing was obtained; heap evidence is the startup log and container configuration. Neither diagnostic blocked a requested success check. The failed command is retained in [heap-process.log](heap-process.log).

## Backup proof

The scheduled sidecar saved snapshot `bca2308a` at 2026-10-01 07:35:39 UTC, enabled saving again and logged `sleeping 6h...`. Its next interval was six hours, approximately 13:35:40 UTC. The operator docs specify retention of seven daily, four weekly and six monthly snapshots.

Manual `scripts/minecraft backup` exited 0 and saved `b68ac97f` at 07:36:39 UTC. Logs show authenticated readiness, save-off, save-all flush, 182 files processed, snapshot saved and save-on. `scripts/minecraft snapshots` independently listed both snapshot records. The full manual ID is `b68ac97fdbde214c3271f6b0213ca6ae818141590bf3f625ec6bdcadc7928533`. See [scheduled-backup.log](scheduled-backup.log), [manual-backup.log](manual-backup.log) and [snapshots.log](snapshots.log). Restore was not requested and was not tested.

## Data, secrets and cleanup

Runtime data used fixture-local `data/server`; the encrypted restic repository used `backups/repository`. Generated settings and five credentials used `.state/` and `.state/secrets/`. Every credential file was nonempty and mode 0600. Only paths and permissions were retained in [credential-paths.json](credential-paths.json).

`scripts/minecraft stop` exited 0 and removed the two project containers plus `minecraft-c56fd5f6_default`. Project-filtered Docker queries confirm zero containers, networks and volumes. The one-off backup/snapshot containers removed themselves. Port 35673 refused connections after cleanup. Runtime mounts were bind mounts, with no project named volumes. See [cleanup.log](cleanup.log) and [cleanup-verification.json](cleanup-verification.json).

After checking retained artifacts against all generated secret values, this review removed its fixture's generated `.state`, `data` and `backups` directories. Only redacted evidence and the supplied clean fixture material remain. No host software, firewall, DNS, production data, Docker pruning or unrelated Docker resource mutation occurred. Publication omits unrelated host inventories and isolation comparisons. The retained cleanup verification records only the owned project and gameplay port. Concurrent lanes could independently change other resources. Container images were retained and were not pruned.
