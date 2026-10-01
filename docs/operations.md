# Operations

## Files and access

`.state/` holds the generated project identity, deployment options, Velocity config and five secrets. `data/server/` holds the world, runtime settings and installed plugins; `data/proxy/` holds Velocity downloads and plugin data. The project-scoped `database` Docker volume holds MariaDB data. `backups/` holds the encrypted restic repository. These paths, plugin inputs, and user configuration are ignored by Git. Keep their permissions and an encrypted recovery copy under your control. Compose secrets are protected local files, not an encrypted vault.

Standalone authenticates through Mojang. Network mode authenticates through Velocity with modern forwarding; the backend has offline authentication only because its port is unpublished and its forwarding secret authenticates the proxy. RCON, SQL, query, debug and admin ports are unpublished. Other containers on the same Docker network are still inside the trust boundary. Isolate untrusted workloads and control Docker daemon access.

## Backups and restore

The `backup` profile runs the same job as `scripts/minecraft backup`, after server health, then every six hours. It uses RCON `save-off`, `save-all flush`, and `save-on`, including an exit trap to resume saving on failure. Concurrent jobs share a backup-directory lock. Restic encrypts the server directory, including jars and plugin data. Retention keeps seven daily, four weekly and six monthly snapshots. Inspect `compose logs backup`; a running sidecar alone does not prove successful backups.

The server directory backup excludes cache, logs and temporary files. It does not back up MariaDB, proxy data, source configuration, or `.state/`. Keep encrypted copies of those separately, especially the restic password. For SQL plugins, use a separate authenticated `mariadb-dump --single-transaction` workflow and restore rehearsal. Copying the live database directory is not a SQL backup. Plugin writes outside Minecraft save coordination need plugin-specific handling.

Move or replicate the encrypted repository off-host. Local backups do not protect against host loss. Keep the restic password separately from the repository. Inspect snapshots and check integrity:

```sh
./scripts/minecraft snapshots
./scripts/minecraft compose run --rm --no-deps --entrypoint restic backup check
./scripts/minecraft restore /absolute/empty/recovery-directory --snapshot latest
```

Restore creates `recovery-directory/data/`. Rehearse booting that data in a separate checkout and isolated project before considering production replacement. Stop the destination server before deliberate data replacement. Never restore directly over a running world. The automated full Docker validator performs this rehearsal with a persistent scoreboard value.

## Plugins, mapping and web

`plugins/server/` and `plugins/proxy/` are read-only source inputs copied into their persistent plugin directories at startup. `configs/server/` copies server configs. In network mode it also contains the generated Paper forwarding secret; it is ignored and mode 0600. Keep that file's forwarding settings consistent with `.state/velocity.toml` and `.state/secrets/forwarding`.

Install current Plan or mapping plugins only after checking publisher support for the selected Paper release. Their old bundled configs and web assets were removed. Configure Plan's current authentication and database independently; reach its admin interface over an SSH tunnel or authenticated reverse proxy. A mapping plugin can serve its own current web interface internally, or write static output under `web/` for the optional NGINX profile. The profile exposes only `127.0.0.1:8080`; `--web-port` selects another loopback port. It also serves downloads placed there. Put a maintained authenticated HTTPS proxy in front if you choose public access. The template neither configures public DNS/ACME nor mounts the Docker socket.

With the database profile enabled, plugins use host `database`, port 3306, database and username `minecraft`, and the protected `.state/secrets/database` credential. There is no public SQL or phpMyAdmin port. The database credential is initialized once by MariaDB; changing a secret file alone does not change an existing database account.

## Updates and deliberate reconfiguration

Review [versions.env](../versions.env), run `scripts/check-versions`, back up, and rehearse restoration before software changes. Image and jar versions are separate pins. Renovate proposes image tag/digest updates; software versions require checking official release channels. The version verification workflow exports the official identity evidence. Repeat full validation after any pin change. Paper and Vanilla worlds may differ; do not change distribution on an existing production world without a compatibility rehearsal.

Setup never rewrites an existing deployment with new options. For an intentional port, MOTD, memory or profile change, stop the project, make a protected copy of `.state/`, edit `.state/settings.env` and the matching values in `.state/settings.json`, then run `doctor` and `start`. Standalone's published port lives in `.state/compose.yaml`; network's port comes from `GAME_PORT`. Keep those in sync. Use Compose overrides for advanced local requirements. `doctor` rejects contradictory authentication, published backend/admin ports and inconsistent generated forwarding settings. Keep the generated forwarding YAML indentation when editing it. Review resolved configuration locally; `compose config` can contain sensitive interpolated values and should not be published.

Switching an existing deployment between standalone and proxy mode requires matching Paper, Spigot and Velocity configs as well as port changes. Rehearse it in a new checkout instead of editing production in place. Setup does not automate topology or world migrations.
