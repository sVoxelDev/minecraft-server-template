import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


def copy_template(destination):
    result = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True, capture_output=True)
    if result.returncode == 0:
        files = set(result.stdout.splitlines())
    else:
        excluded = {'.git', '.state', 'data', 'backups', 'validation-output', '__pycache__', 'node_modules',
                    'servers', 'minimal', 'worlds', 'database', 'rcon', 'backup', 'schematics', 'downloads', 'files'}
        files = {str(path.relative_to(ROOT)) for path in ROOT.rglob('*') if path.is_file() and
                 not excluded.intersection(path.relative_to(ROOT).parts) and not path.name.endswith(('.secrets.env', '.jar')) and
                 path.name not in {'.env', 'secrets.env', 'ports.env'}}
    for name in files:
        source = ROOT / name
        if source.is_file() and not name.startswith(('validation-output/', 'docs/proof/', 'configs/server/', 'plugins/server/', 'plugins/proxy/', 'web/')):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)



class SetupBoundary(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='minecraft cli with spaces ')
        self.root = Path(self.temporary.name)
        copy_template(self.root)
        self.cli = self.root / 'scripts/minecraft'

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, *args):
        return subprocess.run([str(self.cli), *args], cwd='/tmp', stdin=subprocess.DEVNULL,
                              text=True, capture_output=True, timeout=30)

    def test_requires_consent_and_rejects_invalid_options_without_writes(self):
        for args in [[], ['--accept-eula', '--port', '0'], ['--accept-eula', '--memory', '512M'],
                     ['--accept-eula', '--distribution', 'vanilla', '--network'], ['--accept-eula', '--unknown']]:
            result = self.invoke('setup', *args)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertFalse((self.root / '.state').exists())

    def test_idempotent_setup_preserves_secrets_world_and_denies_silent_reconfiguration(self):
        self.assertEqual(self.invoke('setup', '--accept-eula').returncode, 0)
        secret = self.root / '.state/secrets/rcon'
        before = secret.read_bytes()
        marker = self.root / 'data/server/world/marker'
        marker.parent.mkdir()
        marker.write_text('existing world')
        result = self.invoke('setup', '--accept-eula')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['setup'], 'unchanged')
        self.assertEqual(secret.read_bytes(), before)
        self.assertEqual(marker.read_text(), 'existing world')
        self.assertEqual(secret.stat().st_mode & 0o777, 0o600)
        result = self.invoke('setup', '--accept-eula', '--network')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(before.decode().strip(), result.stdout + result.stderr)
        secret.write_text('')
        self.assertNotEqual(self.invoke('setup', '--accept-eula').returncode, 0)

    def test_doctor_reports_unavailable_docker_without_exposing_credentials(self):
        self.assertEqual(self.invoke('setup', '--accept-eula').returncode, 0)
        binary = self.root / 'without docker'
        binary.mkdir()
        (binary / 'python3').symlink_to(shutil.which('python3'))
        result = subprocess.run([str(self.cli), 'doctor'], env={'PATH': str(binary)}, cwd='/tmp',
                                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('docker', result.stderr)
        self.assertNotIn((self.root / '.state/secrets/rcon').read_text().strip(), result.stdout + result.stderr)

    def test_doctor_refuses_contradictory_authentication(self):
        self.assertEqual(self.invoke('setup', '--accept-eula').returncode, 0)
        config = self.root / '.state/compose.yaml'
        config.write_text(json.dumps({'services': {'server': {'environment': {'ONLINE_MODE': 'false'}}}}))
        result = self.invoke('doctor')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('authentication contradicts', result.stderr)

    def test_ambient_environment_cannot_redirect_project_or_pins(self):
        self.assertEqual(self.invoke('setup', '--accept-eula', '--profile', 'backup', '--profile', 'database', '--profile', 'web', '--network').returncode, 0)
        managed = dict(line.split('=', 1) for line in (self.root / '.state/settings.env').read_text().splitlines())
        managed.update(dict(line.split('=', 1) for line in (self.root / 'versions.env').read_text().splitlines() if line))
        environment = dict(os.environ, **{key: 'untrusted:latest' for key in managed})
        environment['COMPOSE_PROJECT_NAME'] = 'unrelated-production-proof'
        result = subprocess.run([str(self.cli), 'compose', 'config', '--format', 'json'], env=environment, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(result.stdout)
        self.assertEqual(config['name'], managed['COMPOSE_PROJECT_NAME'].strip("'"))
        self.assertNotIn('untrusted', str(config))
        self.assertEqual(config['services']['server']['environment']['VERSION'], managed['PAPER_VERSION'])
        (self.root / '.state/compose.yaml').write_text(json.dumps({'services': {'server': {'image': 'untrusted:latest'}}}))
        invalid = self.invoke('doctor')
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn('images contradict', invalid.stderr)

    def test_doctor_rejects_network_bypasses(self):
        self.assertEqual(self.invoke('setup', '--accept-eula', '--network', '--profile', 'database').returncode, 0)
        for service, mode in [('server', 'host'), ('database', 'host'), ('server', 'container:foreign')]:
            (self.root / '.state/compose.yaml').write_text(json.dumps({'services': {service: {'network_mode': mode}}}))
            result = self.invoke('doctor')
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('network', result.stderr.lower())
        for definition in [{'name': 'unrelated-bridge'}, {'external': True, 'name': 'unrelated-bridge'}, {'driver': 'macvlan'}]:
            (self.root / '.state/compose.yaml').write_text(json.dumps({'networks': {'default': definition}}))
            result = self.invoke('doctor')
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('network', result.stderr.lower())

    def test_literal_motd_survives_setup_and_compose(self):
        motd = "Unicode ☃ $HOME ${SERVER_IMAGE} backslash \\" + "' quote \\\\ tail"
        self.assertEqual(self.invoke('setup', '--accept-eula', '--network', '--motd', motd).returncode, 0)
        result = self.invoke('compose', 'config', '--format', 'json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['services']['server']['environment']['MOTD'].replace('$$', '$'), motd)
        import tomllib
        self.assertIn('Unicode ☃ $HOME ${SERVER_IMAGE}', tomllib.loads((self.root / '.state/velocity.toml').read_text())['motd'])

    def test_legacy_deployment_is_refused(self):
        (self.root / 'servers/main').mkdir(parents=True)
        self.assertNotEqual(self.invoke('setup', '--accept-eula').returncode, 0)
        self.assertFalse((self.root / '.state/settings.json').exists())

    def test_all_supported_modes_resolve_secure_compose(self):
        for options in [[], ['--distribution', 'vanilla'], ['--network', '--profile', 'backup',
                                                               '--profile', 'database', '--profile', 'web']]:
            with tempfile.TemporaryDirectory(prefix='minecraft config ') as temporary:
                target = Path(temporary)
                copy_template(target)
                cli = target / 'scripts/minecraft'
                setup = subprocess.run([str(cli), 'setup', '--accept-eula', *options], capture_output=True, text=True)
                self.assertEqual(setup.returncode, 0, setup.stderr)
                result = subprocess.run([str(cli), 'compose', 'config', '--format', 'json'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                config = json.loads(result.stdout)
                server = config['services']['server']
                self.assertEqual(server['environment']['ONLINE_MODE'], 'false' if '--network' in options else 'true')
                self.assertEqual(server['environment']['ENABLE_QUERY'], 'false')
                pins = dict(line.split('=', 1) for line in (target / 'versions.env').read_text().splitlines() if line)
                self.assertEqual(server['environment']['VERSION'], pins['VANILLA_VERSION' if 'vanilla' in options else 'PAPER_VERSION'])
                self.assertNotIn('/var/run/docker.sock', str(config))
                if '--network' in options:
                    self.assertFalse(server.get('ports'))
                    self.assertFalse(config['services']['database'].get('ports'))
                else:
                    self.assertEqual([port['target'] for port in server['ports']], [25565])
                secrets = [path.read_text().strip() for path in (target / '.state/secrets').iterdir()]
                ignored = subprocess.run(['git', 'check-ignore', '--no-index', '.state/secrets/rcon'], cwd=ROOT,
                                         capture_output=True, text=True)
                if (ROOT / '.git').exists():
                    self.assertEqual(ignored.returncode, 0)
                for secret in secrets:
                    self.assertNotIn(secret, setup.stdout + setup.stderr)


if __name__ == '__main__':
    unittest.main()
