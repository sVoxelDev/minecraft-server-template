import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


def copy_template(destination):
    files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True)
    for name in set(files.splitlines()):
        source = ROOT / name
        if source.is_file() and not name.startswith(('validation-output/', 'docs/proof/')):
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
                self.assertEqual(server['environment']['VERSION'], '26.3' if 'vanilla' in options else '26.2')
                self.assertNotIn('/var/run/docker.sock', str(config))
                if '--network' in options:
                    self.assertFalse(server.get('ports'))
                    self.assertFalse(config['services']['database'].get('ports'))
                else:
                    self.assertEqual([port['target'] for port in server['ports']], [25565])
                secrets = [path.read_text().strip() for path in (target / '.state/secrets').iterdir()]
                ignored = subprocess.run(['git', 'check-ignore', '--no-index', '.state/secrets/rcon'], cwd=ROOT,
                                         capture_output=True, text=True)
                self.assertEqual(ignored.returncode, 0)
                for secret in secrets:
                    self.assertNotIn(secret, setup.stdout + setup.stderr)


if __name__ == '__main__':
    unittest.main()
