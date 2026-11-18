"""DeepSeek Harness bundle contract for plugins/app-ui-studio."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins' / 'app-ui-studio'
NODE = shutil.which('node')


def node_major():
    if NODE is None:
        return 0
    match = re.match(r'v(\d+)', subprocess.run([NODE, '--version'], capture_output=True, text=True).stdout)
    return int(match.group(1)) if match else 0


def run_node(script):
    done = subprocess.run([NODE, '--input-type=module', '-e', script], cwd=PLUGIN,
                          capture_output=True, timeout=60)
    if done.returncode:
        raise AssertionError(done.stderr.decode(errors='replace'))
    return json.loads(done.stdout.decode('utf-8'))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((PLUGIN / 'package.json').read_text(encoding='utf-8'))

    def test_versions_agree_across_hosts(self):
        others = {json.loads((PLUGIN / name).read_text(encoding='utf-8'))['version']
                  for name in ('plugin.json', '.codex-plugin/plugin.json')}
        self.assertEqual(others, {self.manifest['version']})

    def test_package_stays_commonjs_for_existing_scripts(self):
        # board_feedback.js is CommonJS; a module-typed package would break require() of it.
        self.assertNotEqual(self.manifest.get('type'), 'module')
        self.assertTrue(self.manifest['exports']['.'].endswith('.mjs'))

    def test_exports_files_and_patch(self):
        for key, target in self.manifest['exports'].items():
            matches = list(PLUGIN.glob(target[2:])) if '*' in target else [PLUGIN / target]
            self.assertTrue(matches and all(path.is_file() for path in matches), key)
        for entry in self.manifest['files']:
            self.assertTrue(list(PLUGIN.glob(entry)), entry)
        patch = (PLUGIN / self.manifest['dsh']['bundle']['patch']).read_text(encoding='utf-8')
        self.assertIn('name: ' + self.manifest['name'] + '\n', patch)
        self.assertNotIn('dependencies', self.manifest)
        self.assertNotIn('scripts', self.manifest)

    def test_locales(self):
        for locale in ('en', 'zh'):
            meta = json.loads((PLUGIN / 'locale' / (locale + '.json')).read_text(encoding='utf-8'))['meta']
            self.assertTrue(meta['title'])
            self.assertGreater(len(meta['description']), 40)


@unittest.skipUnless(node_major() >= 22, 'Node.js 22+ is required for the provider tests')
class ProviderTests(unittest.TestCase):
    def test_skill_is_listed_and_body_is_preserved(self):
        result = run_node(
            "import { createProvider } from './dsh/index.mjs';"
            "const p = await createProvider(); const list = await p.list();"
            "console.log(JSON.stringify({ list, skill: await p.get(list[0]) }))")
        self.assertEqual([item['name'] for item in result['list']], ['app-ui-studio'])
        self.assertEqual(result['list'][0]['provider'], 'app-ui-studio')
        source = (PLUGIN / 'skills' / 'app-ui-studio' / 'SKILL.md').read_text(encoding='utf-8')
        body = source.split('---\n', 2)[2]
        content = result['skill']['content']
        self.assertTrue(content.endswith(body))
        self.assertIn('studio.py', content[:-len(body)])
        self.assertNotIn('{{', content[:-len(body)])


if __name__ == '__main__':
    unittest.main()
