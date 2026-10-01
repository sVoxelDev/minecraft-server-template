# Start prompt

Paste this into your coding agent from a fresh checkout:

> Use the repo-local minecraft-server-setup skill to set up and start this template. I explicitly accept the Minecraft EULA at https://aka.ms/MinecraftEULA for this server. Use default stable Paper, enable scheduled backups, and bind gameplay to 127.0.0.1 for local use. Make autonomous routine decisions within this checkout. Docker and Python must already be installed; report a prerequisite blocker instead of installing host packages or changing firewall/DNS. Finish by querying live Minecraft status, running authenticated RCON, and reporting exact versions, health, data paths, and the backup schedule without revealing secrets.

For a public server, explicitly request the desired bind address and handle host networking separately. For current Vanilla, request `--distribution vanilla` and omit proxy/plugin requirements. For a network, request Velocity and Paper. EULA acceptance in this example does not authorize unrelated future installations or existing-world upgrades.
