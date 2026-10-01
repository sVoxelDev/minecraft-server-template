# Independent standards review

Reviewed 2026-10-01 UTC in `/tmp/minecraft-modernize`. Fixed point `b65b463a674ca0caf9fcf76eca5c07a60b1ab9cd`; reviewed commits through `bde5ede0f4140cfede9835ddd1b1b5745688d05f`, using `git diff b65b463...HEAD`, plus final working source and runtime evidence. The builder concurrently changed migration ignores and documentation; those edits were observed, not made by this reviewer. No code, other ticket, map or GitHub mutation occurred.

Resolution: request changes. Three P1 operational defects and three P2 operational/validation defects are verified. A separate P2 maintenance gap is also verified. Closure means this independent review is complete, not that the implementation passes.

## Verified findings

### P1: inherited project identity can target unrelated resources

`scripts/minecraft:42-46`; destructive caller `scripts/validate:208`.

Fresh setup writes a random `COMPOSE_PROJECT_NAME`, but every Docker call inherits the shell environment. Docker gives an inherited project name precedence over the env-file value. Public repro: initialize an isolated checkout, set `COMPOSE_PROJECT_NAME=unrelated-production-review-proof`, then run `compose config --format json`. The effective name becomes `unrelated-production-review-proof`; `doctor` exits zero. Evidence: `review-standards-boundaries.json`.

Consequently, `stop` and validator `down --volumes --remove-orphans` can remove containers or volumes belonging to that existing project. I proved name selection without deleting unrelated resources. The validator's later ownership checks use the generated name, making them inspect a different project. Ambient image variables can likewise override file pins while `doctor` reports the file values.

Minimal fix: make generated deployment identity authoritative with a validated explicit project argument; isolate child Compose interpolation from conflicting inherited deployment/pin variables. Verify actual effective identity before any cleanup. This violates the user's restriction on destructive actions and the documented isolated-project contract.

### P1: a failed Restic backup returns success

`scripts/minecraft:245-250`, with capture behavior at `scripts/minecraft:20-22`.

Public runtime repro: start disposable Paper, complete one backup, then set the isolated backup service's `RESTIC_LIMIT_UPLOAD` to `invalid` and call `scripts/minecraft backup`. Restic rejects the flag, the pinned sidecar logs `ERROR Backup failed with exit code 1`, and the CLI exits zero with empty stdout. All sidecar logs go to stderr, while the CLI checks only captured stdout. The sidecar intentionally continues and itself returns zero after this failure.

Evidence: `review-standards-backup-repro.json`. Saving resumes correctly, so the defect is false success and lost recovery coverage, not save resumption. Minimal fix: inspect merged stdout/stderr for sidecar failure, or arrange a trustworthy one-shot exit status; test a failure inside Restic, not only `PRE_BACKUP_SCRIPT`. This violates truthful public-command validation and recovery behavior.

### P1: concurrent backups re-enable saving before the lock

`compose.yaml:101`, `docs/operations.md:9`, and the pinned backup image's `backup-loop.sh` loop before `flock 4`.

The sidecar performs its RCON readiness check with `save-on` before acquiring `/backups/.mc-backup-lock`. Public runtime repro: run a backup with `PRE_BACKUP_SCRIPT=sleep 15`; after its successful save-off/flush/sync, start a second ordinary backup. The second job successfully sends save-on while the first still holds the lock. An RCON probe returns `Saving is already turned on` while the first remains active.

Evidence: `review-standards-concurrent-backup.json`. During a longer actual snapshot this permits world saves while files are being read, defeating coordinated consistency. Minimal fix: use a non-mutating readiness command such as `list`, or acquire the shared lock before any save-state command. Adopt a fixed pinned sidecar or a small maintained entrypoint fix. Add a two-job public test. This is a verified dependency integration defect, not a Fowler abstraction recommendation.

### P2: host networking bypasses privacy checks

`scripts/minecraft:150-157`.

After isolated network setup, set `.state/compose.yaml` to `{"services":{"server":{"network_mode":"host"}}}`. Resolved config has host networking and no `ports`; `doctor` returns `configuration: valid`. Evidence: `review-standards-boundaries.json`.

Host networking exposes the server's listening gameplay/RCON sockets without published-port entries. An optional database using host networking similarly bypasses its check. Modern forwarding still protects gameplay login; this finding does not claim an account-authentication bypass. Minimal fix: reject host networking for protected services and inspect effective network configuration. This violates the backend/admin privacy contract.

### P2: the cleanup gate never asserts unrelated resources survived

`scripts/validate:210-221`.

The validator writes an inventory diff but computes its pass condition solely from its own remaining resources. `/tmp/minecraft-modernize-runtime-final/summary.json` says passed true while that run's `inventory-diff.json` lists removed unrelated ID `2dc5d814e349`. The later verified run has no removals, but the code still omits this assertion. Copies of the contradictory summary and inventory are retained as `review-standards-inventory-run-summary.json` and `review-standards-inventory-diff.json`. I do not attribute that removal to the validator; another actor may have removed it. The report cannot certify preservation either way.

Minimal fix: assert preservation of a stable test sentinel outside the cleanup project, or explicitly fail and explain unresolved inventory removals before claiming preservation. Retain owned-resource checks. This is a concrete validation gap, independent of the inherited-project defect.

### P2: accepted MOTD quoting produces unusable setup

`scripts/minecraft:107`.

Pass a MOTD containing one backslash immediately followed by an apostrophe. Setup succeeds and writes settings, but the next `compose config` exits one because dotenv parsing treats the escaped quote incorrectly. A source-independent repro constructs the argument as `"backslash " + chr(92) + "' quote"`. Evidence: `review-standards-boundaries.py` and `.json`. The resulting error is `unexpected character "'" in variable name "quote'"`.

Minimal fix: serialize dotenv values with correct backslash/quote handling, and verify that public setup preserves this value through actual startup. No shell injection was observed. Dollar escaping in serialized Compose output was investigated and excluded as an unproven runtime defect.

## Verified maintenance gap

P2, `.github/workflows/validate.yml:18,20,30,32` and `.github/workflows/versions.yml:15,17`: workflow actions remain pinned to checkout v4.2.2 and upload-artifact v4.6.2. Official GitHub release APIs identify v7.0.1 for both. Evidence: `review-standards-actions.json`, with source URLs. Minimal fix: review the publishers' migration requirements, pin supported current release commits and run both workflows. This is a full-modernization gap, not a claim that an old major alone is a security vulnerability or a documented coding-style violation.

## Checks and limits

`./scripts/validate local` passed independently. `./scripts/check-versions` passed independently, validating software metadata and fixed image index/platform digests. Artifacts are `review-standards-local/` and `review-standards-version-check.json`. The image pins freeze exact digest identities rather than floating tags. Existing runtime evidence in `/tmp/minecraft-modernize-runtime-verified/` proves ARM64 Paper/Vanilla startup, persistence, restored scoreboard contents, MariaDB authentication/persistence, static web serving, real forwarded backend join, direct-backend/wrong-secret denial, and restored production authentication. Online login proof challenges the authentication request; the successful forwarded login uses disposable offline account mode. ARM64 runtime evidence does not prove amd64 execution. The final reviewed commit adds effective standalone/Vanilla authentication and Vanilla/Velocity runtime checksum assertions; these were inspected in source, but their newer full-run results were not claimed by this review.

Two independent disposable Paper deployments reproduced backup failure and concurrency. Their unique projects were torn down successfully, including owned resources; no pruning or host changes occurred. Logs were redacted before publication. Restore guards were inspected for empty destinations, snapshot argument validation and canonical destination handling; no additional verified restore defect is asserted. The legacy-ignore regression visible in the earlier commit is being corrected in the builder's working tree and is not an open finding here.

Standards sources were the user instructions, `AGENTS.md`, the setup skill and operational contracts. Python/Bash are suitable; no app-stack preference was imposed. No new inline code comments, npm/yarn usage, or worthwhile simplicity/type-safety violation was found. Fowler's full baseline was considered: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man and Refused Bequest. These remain heuristics; none justified an additional finding or mandatory abstraction.
