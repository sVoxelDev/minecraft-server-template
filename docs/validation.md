# Validation

The full Docker gate passed from a clean local Git clone on 2026-10-01, from 06:59:33 to 07:02:46 UTC. It ran 35 runtime assertions plus six CLI/config boundary tests on native Linux ARM64, Docker Engine 29.8.0 and Compose 5.5.1. The application source is from `989aac3`; the final runtime harness ran at `bde5ede`. [Run summary](proof/runtime/summary.json), [assertions](proof/runtime/assertions.json), [redacted commands and logs](proof/runtime/commands.jsonl), [source identity](proof/identity.json).

## What ran

| Boundary | Observed result |
| --- | --- |
| Setup and diagnostics | Explicit EULA refusal; invalid port, memory, distribution/topology and unknown options rejected. Setup from another directory and a path with spaces passed. Repeat setup preserved credentials and a world marker. Legacy data, empty secrets, missing Docker and contradictory offline authentication failed clearly. |
| Stable standalone Paper | Paper 26.2 build 129, commit `9240f58`, reached Minecraft status and RCON. Its downloaded JAR matched the pinned official SHA-256. Custom MOTD reached status. Effective online authentication and disabled query matched the contract. A protocol client received an authentication challenge; an incorrect RCON password failed. |
| Latest Minecraft release | Vanilla 26.3 reached live Minecraft status and RCON, with online authentication and query disabled. The downloaded bundler JAR matched Mojang's pinned SHA-1. |
| Persistence | A scoreboard value of 42 survived forced server container recreation. |
| Backups | The scheduled restic sidecar produced a snapshot and reported its six-hour interval. The manual command used the same job. Server logs showed save flush and automatic saving resumed. An injected failure after saves were disabled exited unsuccessfully; a subsequent RCON check confirmed saving was already on. |
| Restore | After changing the source value to 99, a snapshot restored into a separate empty directory. A separately initialized server booted those files and returned the original value of 42. |
| Velocity | Version 4.2.1-SNAPSHOT build 36, commit `7fc49913`, started with the pinned matching JAR hash. Proxy status worked; backend ports were absent from the resolved deployment. Effective Paper config contained the shared modern-forwarding secret. Production login requested account authentication. |
| Forwarding client | In the disposable offline-auth test variant, the minimal native protocol client entered play. Backend RCON listed `ForwardProof`, and backend logs recorded its join. Direct backend login failed without forwarding. A mismatched forwarding secret failed login. Production online authentication was restored and challenged the client again. |
| Optional services | MariaDB 12.3.3 authenticated with generated application credentials, created/read a row, retained it through recreation, and rejected a wrong password. NGINX 1.30.5 served files over its ephemeral loopback port. |
| Agent setup | A clean Git clone contained AGENTS.md, START.md and the repo-local skill. The same setup, diagnostics, live status, RCON and scheduled-backup operations required by the skill ran successfully from fresh deployment copies. Skill frontmatter validation passed. |
| Cleanup | All owned project containers, networks and named volumes were absent after teardown. Temporary server, repository and restore directories were removed. The unrelated container inventory was compared and exported; concurrent workers' temporary container churn did not trigger unrelated cleanup. |

Both Java wrappers actually reported Temurin 25.0.4+7. Restic snapshots reported 0.19.1. Actual container/image identities are in the command log; the complete reproducible pins are in [the captured versions](proof/runtime/versions.env). The independent version verifier rechecked Paper/Velocity stable-channel metadata, Mojang release metadata, all five image index digests, and their amd64/arm64 child manifest digests. [Version evidence](proof/version-check.json), [cleanup evidence](proof/runtime/cleanup.json), [inventory comparison](proof/runtime/inventory-diff.json), [local gate](proof/local/summary.json).

## Reproduce

Run from a fresh checkout with Python 3.11+, Git, native Linux Docker Engine 28+, Compose v2/v5, GNU `timeout`, sufficient memory and disk, and network access to the publishers:

```sh
./scripts/validate local --output /tmp/minecraft-local-proof
./scripts/check-versions > /tmp/minecraft-version-proof.json
./scripts/validate fullDocker --output /tmp/minecraft-runtime-proof
```

The validator uses fresh temporary tracked-file copies, random project names, ephemeral loopback ports, modest heaps and small view distances. Every runtime command has a GNU timeout; signal handling runs scoped teardown. Output includes timestamped commands, exit codes, redacted logs, assertions, versions and cleanup results. `--scenario network` runs only the forwarding sequence. The CI workflow exposes the same full gate through an explicit workflow-dispatch input and uploads artifacts even after failure.

## Limits

This run proves native ARM64 behavior. AMD64 manifests and artifact availability were verified, but no AMD64 server was executed here. The configured Ubuntu CI runtime gate has not been run on GitHub from this local branch. The native client implements the pinned Paper release's login/configuration sequence, not general gameplay automation.

Production account-authenticated login requires account credentials and was not completed. Authentication challenge checks establish that production requests authentication; isolated play proves forwarding, with online authentication temporarily disabled only in the disposable test project. The final configuration restores production online authentication.

No arbitrary plugin, Plan/Dynmap release, public DNS/ACME, external reverse proxy, migrated 1.17 production world, SQL backup or off-host repository is certified. Those paths have explicit operational or migration instructions. Backups cover server files; plugin databases need their own consistent backup and rehearsal. The scheduled sidecar's startup snapshot and next interval were observed; the test did not wait six hours for its next scheduled tick. The clean-checkout test exercises the setup skill's public operations; independent agent instruction review remains with the conductor.

Baseline failures were reproduced before implementation: missing `docker-compose`, invalid duplicate YAML keys, false-success EOF initialization and empty restic credentials, plus missing debug fragments. The original baseline commit was `b65b463a674ca0caf9fcf76eca5c07a60b1ab9cd`; the durable source report is the environment ticket's `logs/baseline/report.md`. The new boundary tests retain those failure contracts through the replacement CLI rather than retaining the broken launchers.
