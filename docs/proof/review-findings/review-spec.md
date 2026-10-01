# Spec review

Request changes. Reviewed base `b65b463a674ca0caf9fcf76eca5c07a60b1ab9cd` through `bde5ede`, plus final working docs/source/proof on 2026-10-01 UTC. Spec source is `prompts/implementation.txt` and Michael's adopted version policy. This ticket is complete even though findings remain.

## Findings

1. P1, `scripts/minecraft:42`, `scripts/validate:218`. Requirement: "random project names" and "no unrelated prune". Inherited `COMPOSE_PROJECT_NAME` overrides the generated identity. Repro: setup an isolated checkout; invoke `compose config --format json` with `COMPOSE_PROJECT_NAME=review-spec-unrelated-probe`. Effective name changes and doctor succeeds. Cleanup can consequently target another project, including its volumes. Inherited `SERVER_IMAGE` also overrides the pin while doctor reports the original pin. Evidence: `review-spec-boundaries.json`. Make generated identity and effective pins authoritative before launch/cleanup.

2. P1, `scripts/minecraft:245`. Requirement: "Tests at user-authorized public boundaries" including "backups/restore". Inject `RESTIC_LIMIT_UPLOAD=invalid` into an isolated backup service and run `backup`. Restic reports `Backup failed with exit code 1`, but the CLI returns zero. It checks captured stdout while the failure is on stderr, and the sidecar returns zero. The validator's pre-hook failure does not test this path. Evidence: `review-spec-runtime.json`. Propagate actual snapshot failure.

3. P1, `compose.yaml:backup`, `docs/operations.md:9`. Requirement: "scheduled consistent backups". Start backup with `PRE_BACKUP_SCRIPT=sleep 12`, wait for save-off/flush/sync, then start ordinary backup. Its readiness sends save-on before acquiring the lock. RCON confirms saving already enabled while the first job remains active. Evidence: `review-spec-runtime.json`. Lock before save-state mutation or use non-mutating readiness.

4. P2, `scripts/minecraft:125`. Requirement: "idempotent setup and config"; documented MOTD configuration. `setup --accept-eula --network --motd 'Spec custom lobby'` succeeds, but generates proxy MOTD `Minecraft Velocity network`. Clients see the proxy's fixed value. Evidence: `review-spec-boundaries.json`. Apply the requested MOTD to Velocity with valid TOML encoding.

5. P2, `scripts/validate:101`, `:104`, `:105`, `:154`, `:170`. Requirement: "version updates verifiable". The gate hardcodes Paper 26.2/build129, Vanilla 26.3 and Velocity's current jar filename rather than deriving them from `versions.env`. Updating valid pins makes the prescribed gate check old identities or nonexistent files. Read expectations from pins and explicitly handle client protocol changes.

## Verification and limits

Independent `validate local` passed. Independent disposable Paper startup, server/plugin config copying after recreation, successful snapshot, Restic failure and concurrent backups were exercised. All owned containers, networks and volumes were verified absent. Reproduction script and redacted runtime events are `review-spec-runtime.py` and `review-spec-runtime.json`.

Read actual `docs/proof/runtime/commands.jsonl`, assertions, cleanup and identities. They substantiate ARM64 Paper 26.2, Vanilla 26.3, Java 25, authenticated RCON, persistence, separately booted restored scoreboard, MariaDB persistence/authentication, web serving, real forwarded backend join, direct-backend and wrong-secret denial. Paid-account login and AMD64 execution remain explicitly unproved. Inventory churn is exported; no unrelated deletion is attributed to the validator.

Final docs now include the proof, migration replacements and limits. Legacy migration keeps production untouched and warns about irreversible upgrades. The discoverable skill and START prompt have explicit EULA consent, prerequisites, live completion checks and host boundaries. Public setup operations ran from fresh copies; an autonomous agent executing START itself was not demonstrated. No arbitrary plugin compatibility is claimed. No unnecessary scope found. No code, main, other ticket, map or GitHub changes were made.
