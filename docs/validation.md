# Validation

The final review-fix full Docker gate passed 45 runtime assertions and nine CLI/config cases on both native ARM64 and native GitHub AMD64. Final application/harness source is `1b6a5ee`; subsequent commits add evidence/documentation only. ARM64 used an unindexed Git archive, Docker 29.8.0/Compose 5.5.1, from 07:42:13 through 07:45:54 UTC on 2026-10-01. [ARM64 summary](proof/review-fixes/runtime-arm64-final/summary.json), [assertions](proof/review-fixes/runtime-arm64-final/assertions.json), [redacted commands](proof/review-fixes/runtime-arm64-final/commands.jsonl).

[GitHub AMD64 run](https://github.com/sVoxelDev/minecraft-server-template/actions/runs/36831801041) passed the same full gate from a fresh Ubuntu checkout with cold image pulls, Docker 28.0.4 and Compose 2.38.2, from 07:41:44 through 07:46:02 UTC on 2026-10-01. [AMD64 summary](proof/review-fixes/runtime-amd64/summary.json), [assertions](proof/review-fixes/runtime-amd64/assertions.json), [runtime commands/identities](proof/review-fixes/runtime-amd64/commands.jsonl), [CI result](proof/review-fixes/ci-amd64-run.json), [source hashes](proof/review-fixes/identity.json), [local gate](proof/review-fixes/local/summary.json), [version verification](proof/review-fixes/version-check.json), [setup skill validation](proof/review-fixes/skill-validation.json).

The original 35-assertion proof remains in [historical runtime evidence](proof/runtime/summary.json); independent findings subsequently exposed defects in that earlier tree. The final run preserves all 35 earlier runtime assertions and adds ten meaningful assertions for actual Restic failure/save recovery, overlapping jobs, literal Velocity MOTD and stable cleanup sentinel. Three new focused CLI cases supplement the original six. Both final runs include protected archive-copy exclusions and the tiny derived-image build context.


## What ran

| Boundary | Observed result |
| --- | --- |
| Setup and diagnostics | Explicit EULA refusal; invalid port, memory, distribution/topology and unknown options rejected. Setup from another directory and a path with spaces passed. Repeat setup preserved credentials and a world marker. Legacy data, empty secrets, missing Docker and contradictory offline authentication failed clearly. Every inherited managed setting/pin was contaminated; the generated project and pins remained effective. Image substitution, host/container networking, foreign/external/non-bridge networks were rejected without creating resources. |
| Stable standalone Paper | Paper 26.2 build 129, commit `9240f58`, reached Minecraft status and RCON. Its downloaded JAR matched the pinned official SHA-256. Literal unicode, dollars, backslash/apostrophe and doubled-backslash MOTD reached actual status unchanged. Effective online authentication and disabled query matched the contract. A protocol client received an authentication challenge; an incorrect RCON password failed. |
| Latest Minecraft release | Vanilla 26.3 reached live Minecraft status and RCON, with online authentication and query disabled. The downloaded bundler JAR matched Mojang's pinned SHA-1. |
| Persistence | A scoreboard value of 42 survived forced server container recreation. |
| Backups | The scheduled restic sidecar produced a snapshot and reported its six-hour interval. The manual command used the same job. Server logs showed save flush and automatic saving resumed. Both a failed pre-hook and an actual inner Restic failure from invalid `RESTIC_LIMIT_UPLOAD` returned nonzero; the latter included useful stderr, and saves resumed. Two overlapping jobs completed successfully. While the first held the lock after flushing, the second completed non-mutating readiness and saving remained disabled; saving resumed after both completed. |
| Restore | After changing the source value to 99, a snapshot restored into a separate empty directory. A separately initialized server booted those files and returned the original value of 42. |
| Velocity | Version 4.2.1-SNAPSHOT build 36, commit `7fc49913`, started with the pinned matching JAR hash. Proxy status rendered the same literal MOTD; backend ports were absent from the resolved deployment. Effective Paper config contained the shared modern-forwarding secret. Production login requested account authentication. |
| Forwarding client | In the disposable offline-auth test variant, the minimal native protocol client entered play. Backend RCON listed `ForwardProof`, and backend logs recorded its join. Direct backend login failed without forwarding. A mismatched forwarding secret failed login. Production online authentication was restored and challenged the client again. |
| Optional services | MariaDB 12.3.3 authenticated with generated application credentials, created/read a row, retained it through recreation, and rejected a wrong password. NGINX 1.30.5 served files over its ephemeral loopback port. |
| Agent setup | A clean Git clone contained AGENTS.md, START.md and the repo-local skill. The same setup, diagnostics, live status, RCON and scheduled-backup operations required by the skill ran successfully from fresh deployment copies. Skill frontmatter validation passed. |
| Cleanup | All owned project containers, networks and named volumes were absent after teardown. Temporary server, repository and restore directories were removed. A stable container with a separate project label survived contaminated `COMPOSE_PROJECT_NAME` stop/down cleanup and was then explicitly removed. The unrelated container inventory was compared and exported; concurrent workers' temporary container churn did not trigger unrelated cleanup. |

Both Java wrappers actually reported Temurin 25.0.4+7. Restic snapshots reported 0.19.1. Actual container/image identities are in the command log; the complete reproducible pins are in [the captured versions](proof/review-fixes/runtime-arm64-final/versions.env). The independent version verifier rechecked Paper/Velocity stable-channel metadata, Mojang release metadata, all five image index digests, and their amd64/arm64 child manifest digests. [Version evidence](proof/review-fixes/version-check.json), [cleanup evidence](proof/review-fixes/runtime-arm64-final/cleanup.json), [inventory comparison](proof/review-fixes/runtime-arm64-final/inventory-diff.json), [local gate](proof/review-fixes/local/summary.json).

## Reproduce

Run from a fresh checkout with Python 3.11+, Git, native Linux Docker Engine 28+, Compose v2/v5, GNU `timeout`, sufficient memory and disk, and network access to the publishers:

```sh
./scripts/validate local --output /tmp/minecraft-local-proof
./scripts/check-versions > /tmp/minecraft-version-proof.json
./scripts/validate fullDocker --output /tmp/minecraft-runtime-proof
```

The validator uses fresh temporary source copies, with a safe archive fallback excluding generated/legacy data and secrets, random project names, ephemeral loopback ports, modest heaps and small view distances. Every runtime command has a GNU timeout; signal handling runs scoped teardown. Output includes timestamped commands, exit codes, redacted logs, assertions, versions and cleanup results. `--scenario network` runs only the forwarding sequence. The CI workflow runs the same full gate on pull requests and exposes an explicit workflow-dispatch input and uploads artifacts even after failure.

## Limits

Both native ARM64 and GitHub AMD64 executed the real servers and integrations. The committed CI proof identifies the exact tested source; final documentation commits retain those source hashes. The native client explicitly supports Paper protocol 776 for 26.2 and refuses a future unsupported protocol with a clear error before connecting. Runtime version/build/jar/hash expectations derive from `versions.env`; updating a Paper protocol requires updating this small client mapping.

Production account-authenticated login requires account credentials and was not completed. Authentication challenge checks establish that production requests authentication; isolated play proves forwarding, with online authentication temporarily disabled only in the disposable test project. The final configuration restores production online authentication.

No arbitrary plugin, Plan/Dynmap release, public DNS/ACME, external reverse proxy, migrated 1.17 production world, SQL backup or off-host repository is certified. Those paths have explicit operational or migration instructions. Backups cover server files; plugin databases need their own consistent backup and rehearsal. The scheduled sidecar's startup snapshot and next interval were observed; the test did not wait six hours for its next scheduled tick. The clean-checkout test exercises the setup skill's public operations; independent agent instruction review remains with the conductor.

Baseline failures were reproduced before implementation: missing `docker-compose`, invalid duplicate YAML keys, false-success EOF initialization and empty restic credentials, plus missing debug fragments. The original baseline commit was `b65b463a674ca0caf9fcf76eca5c07a60b1ab9cd`; the durable source report is the environment ticket's `logs/baseline/report.md`. The new boundary tests retain those failure contracts through the replacement CLI rather than retaining the broken launchers.

## Review history

The independent [standards](proof/review-findings/review-standards.md) and [spec](proof/review-findings/review-spec.md) reports found defects in the earlier successful tree. Their original Restic stderr and unsafe concurrency evidence remains committed. [Focused local red evidence](proof/review-findings/local-red/commands.jsonl) reproduced inherited project/image redirection, host networking and malformed dotenv MOTD. Failed follow-up probes remain under `proof/review-findings/runtime-3/` and `runtime-4/`: the first incorrectly expected player-list output from the wrapper; the second caught Velocity consuming doubled backslashes. Neither failed result is presented as passing proof. [Baseline report](proof/review-findings/baseline-report.md) preserves the old 1.17/Waterfall failures.

| Review finding | Final public proof |
| --- | --- |
| Inherited project/settings/images | CLI case `test_ambient_environment_cannot_redirect_project_or_pins` poisons every generated setting and pin, verifies exact project/version, and rejects explicit image substitution. All runtime CLI stop/down operations inherit the sentinel project and wrong managed pins. |
| Restic stderr false success | `inner Restic failure returns nonzero with useful output` and `inner Restic failure resumes saves`. |
| Pre-lock save-on overlap | `second backup completed nonmutating readiness while first locked`, `overlap cannot enable saving while first holds lock`, both successful jobs and final save-on evidence in overlap logs. |
| Network bypass | CLI case `test_doctor_rejects_network_bypasses` checks host/container modes, foreign/external bridge names and macvlan without launching them. |
| MOTD literals | Valid TOML/config CLI case and exact Paper/Velocity live protocol MOTD assertions with unicode, dollars, backslash/apostrophe and doubled backslashes. |
| Unrelated cleanup | Stable sentinel survives contaminated cleanup, then is removed; exact project labels show zero owned containers/networks/volumes. Inventory churn is informational. |
| Current actions / AMD64 | Official action release identities are in `proof/actions.json`; GitHub PR jobs run the public local/version/full gates and upload proof even on failure. |
| Updated pins / future protocol | Runtime jar/build/hash assertions use `versions.env`; [unsupported future client proof](proof/review-fixes/unsupported-protocol.json) fails before connecting. |
| Archive validation | Both successful ARM64 full runs used `git archive` source without an index. Fallback excludes protected generated/legacy paths. |

The first GitHub AMD64 run passed all server/integration assertions but failed cleanup because cold-image `docker create` pull progress was merged into the captured sentinel ID. [Failure proof](proof/review-findings/ci-amd64-cold-image-failure/summary.json) remains committed. The harness now uses its unique owned sentinel name and independently inspects its exact 64-character hexadecimal ID; pull output cannot become a Docker resource identifier. The subsequent green AMD64 run proved sentinel survival, explicit removal and complete owned-project cleanup.
