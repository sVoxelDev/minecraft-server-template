# Minecraft server template

Run a reproducible Java Edition server with Docker Compose. The default is stable Paper 26.2 build 129 on Java 25. Minecraft's current release, 26.3, is available as standalone Vanilla. Exact image digests and software versions live in [versions.env](versions.env).

## Start a server

You need Python 3.11+, Docker Engine 28+, the `docker compose` plugin v2 or v5, and at least 4 GiB available memory. Linux amd64 and arm64 images are pinned. Setup uses your host UID and GID for Minecraft and backups; use an ordinary user with Docker access. The optional database and web images use their publisher's initialization defaults.

Read the [Minecraft EULA](https://aka.ms/MinecraftEULA). The flag below records your explicit acceptance.

```sh
git clone https://github.com/sVoxelDev/minecraft-server-template.git
cd minecraft-server-template
./scripts/minecraft setup --accept-eula --start
```

Setup generates random protected secrets, creates local data directories, validates Docker and Compose, starts the selected services, and waits up to ten minutes for healthy services and working RCON. Connect at your host's TCP port 25565. The gameplay port binds publicly; host firewall configuration stays your responsibility. Use `--bind 127.0.0.1` for local development.

Choose options at first setup:

```sh
./scripts/minecraft setup --accept-eula --distribution vanilla --bind 127.0.0.1 --start
./scripts/minecraft setup --accept-eula --network --profile backup --start
./scripts/minecraft setup --accept-eula --profile database --profile web --start
```

Run each example in its own checkout. Vanilla does not support Paper plugins or Velocity modern forwarding. `--network` selects a Paper backend plus online authenticated Velocity and publishes only Velocity. Optional profiles are `backup`, `database`, and `web`; repeat `--profile` to combine them. Setup with identical options is idempotent. Different options fail rather than silently reconfigure a world.

The CLI works from any current directory and supports checkout paths with spaces. `./scripts/minecraft --help` and `setup --help` list options. Use the full path when calling it outside the checkout.

## Operate

```sh
./scripts/minecraft start
./scripts/minecraft status
./scripts/minecraft doctor
./scripts/minecraft command list
./scripts/minecraft command 'save-all flush'
./scripts/minecraft compose logs --tail 100 server
./scripts/minecraft backup
./scripts/minecraft snapshots
./scripts/minecraft restore /absolute/empty/recovery-directory
./scripts/minecraft stop
```

`status` emits Compose JSON; `doctor` emits redacted runtime and pin identity. `command` runs internal authenticated RCON without a published admin port. `stop` removes this project's containers and network, preserving bind-mounted data and secrets. Backup can run manually even without the scheduled profile. Restore writes a separate directory and refuses active data or nonempty destinations.

Place approved Paper jars and plugin configuration under `plugins/server/`, Velocity jars under `plugins/proxy/`, and server configuration under `configs/server/`. Restart to copy them into persistent data. Remove a plugin from both the source and `data/server/plugins/` when uninstalling it. Vanilla ignores plugin jars. The template makes no claim about arbitrary plugin compatibility. [Operations, backup and upgrades](docs/operations.md) explains the data layout and optional integrations.

## Agents and validation

Use the [START prompt](START.md) for a coding agent. Its discoverable [setup skill](.agents/skills/minecraft-server-setup/SKILL.md) requires explicit EULA consent and keeps host installation, firewall and DNS changes outside setup.

```sh
./scripts/validate static
./scripts/validate local
./scripts/validate fullDocker --output /tmp/minecraft-proof
./scripts/check-versions
```

Static and local modes exercise the CLI and resolved Compose boundaries without starting containers. Full Docker mode requires native Linux Docker networking and GNU `timeout`. It accepts the EULA for disposable tests only, runs unique projects on ephemeral loopback ports, checks live protocol and RCON, recreates containers, and boots a restored world. It removes only its own resources and exports redacted command logs, assertions and versions. Read [the validation report](docs/validation.md) for actual results and limits. CI runs the local gate on every change and the full Docker gate on pull requests or explicit dispatch. Archive copies can validate without a Git index; the fallback excludes generated data, secrets and legacy runtime paths.

Existing 1.17 deployments must follow [the migration guide](docs/migration.md). Setup never upgrades production data. [Current standards](docs/current-standards.md) records the cited version and security decisions.

## Troubleshooting

If startup fails, use `doctor`, `status`, and `compose logs --tail 200`. Docker must already be reachable. A failed pull or download is a failure, not a ready server. Give the JVM sufficient heap plus container overhead and leave disk room for world generation and backups. A port conflict requires another explicit setup port in a fresh checkout or deliberate reconfiguration.

Secret files must be nonempty, mode 0600, and readable by the configured Minecraft UID. Restore credentials from secure custody if lost; replacing them can make backups or the database inaccessible. A network backend must retain its matching forwarding secret and both modern forwarding settings. Never publish its port to diagnose login issues. Plugin crashes require checking that plugin's support for the exact Minecraft release.
