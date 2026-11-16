"""Offline routing, provenance and execution-boundary checks."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'plugins/app-ui-studio/skills/app-ui-studio/scripts/studio.py'


def invoke(*arguments, expected=0):
    r = subprocess.run([sys.executable, '-B', str(SCRIPT), *arguments], capture_output=True, timeout=15)
    if r.returncode != expected:
        raise AssertionError(r.stdout.decode('utf-8', 'replace') + r.stderr.decode('utf-8', 'replace'))
    if b'Traceback' in r.stderr:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


class EcosystemTests(unittest.TestCase):
    def test_inventory_coverage_and_fork_boundaries(self):
        data = invoke('ecosystem', '--kind', 'projects')
        records = data['projects']
        self.assertEqual(len(records), data['coverage']['total'])
        self.assertEqual(len({p['name'] for p in records}), len(records))
        self.assertEqual(sum(p['fork'] for p in records), data['coverage']['forks'])
        self.assertTrue(all(p['disposition'] == 'fork-reference' for p in records if p['fork']))
        self.assertTrue(all(p['url'] == 'https://github.com/oil-oil/' + p['name'] for p in records))
        self.assertFalse(data['network_executed'])
        self.assertFalse(data['upstream_code_bundled'])

    def test_each_capability_is_reachable_and_sources_exist(self):
        caps = invoke('ecosystem')['capabilities']
        projects = {p['name']: p for p in invoke('ecosystem', '--kind', 'projects')['projects']}
        self.assertEqual(len({c['id'] for c in caps}), len(caps))
        for cap in caps:
            self.assertTrue(cap['sources'])
            for source in cap['sources']:
                self.assertIn(source, projects)
                self.assertIsNotNone(projects[source]['snapshot'])
                self.assertFalse(projects[source]['fork'])
            result = invoke('workflow', '--task', 'audit', '--focus', cap['id'], '--format', 'json')
            self.assertFalse(result['execution']['implementation'])
            self.assertFalse(result['execution']['project_writes'])
            self.assertFalse(result['generation_executed'])
            self.assertEqual(result['recommended_directions'], 0)
            self.assertEqual(result['specialty']['sources'], cap['sources'])

    def test_brief_is_plan_only_for_every_capability(self):
        for cap in invoke('ecosystem')['capabilities']:
            data = invoke('workflow', '--task', 'brief', '--focus', cap['id'], '--format', 'json')
            self.assertFalse(data['execution']['implementation'])
            self.assertFalse(data['execution']['project_writes'])
            self.assertEqual(data['deliverable'], 'brief')
            self.assertFalse(data['generation_executed'])

    def test_lookup_filters_and_invalid_ids(self):
        single = invoke('ecosystem', '--kind', 'projects', '--id', 'oil-icon')['projects']
        self.assertEqual([p['name'] for p in single], ['oil-icon'])
        data = invoke('ecosystem', '--kind', 'projects', '--disposition', 'adapted-method')
        self.assertTrue(data['projects'])
        self.assertTrue(all(p['disposition'] == 'adapted-method' for p in data['projects']))
        invoke('ecosystem', '--id', 'does-not-exist', expected=2)

    def test_read_only_and_brief_defaults_do_not_request_implementation(self):
        for focus, task in (('product-analysis', 'audit'), ('review-context', 'audit'), ('terminology', 'brief')):
            data = invoke('workflow', '--focus', focus, '--format', 'json')
            self.assertEqual(data['task'], task)
            self.assertFalse(data['execution']['project_writes'])
            self.assertFalse(data['execution']['implementation'])
            invoke('workflow', '--focus', focus, '--task', 'design', '--format', 'json', expected=2)
        analysis = invoke('workflow', '--focus', 'product-analysis', '--format', 'json')
        self.assertIn('基数', analysis['prompt'])
        review = invoke('workflow', '--focus', 'review-context', '--format', 'json')
        self.assertIn('文件/行', review['prompt'])

    def test_artifact_workflows_do_not_expand_into_application_builds(self):
        for focus in ('copy', 'icon-set', 'visual-explain', 'handoff', 'readme', 'product-demo', 'campaign'):
            data = invoke('workflow', '--focus', focus, '--format', 'json')
            self.assertNotIn('先实现代表页', data['prompt'])
            self.assertNotIn('## 页面领域', data['prompt'])
            self.assertFalse(data['generation_executed'])

    def test_mini_program_is_not_marked_native_or_verified(self):
        data = invoke('workflow', '--task', 'reconstruct', '--focus', 'mockup', '--platform', 'mini-program', '--format', 'json')
        self.assertEqual(data['platform'], 'mini-program')
        self.assertFalse(data['ui_quality_verified'])
        self.assertFalse(data['project_inspected'])
        self.assertEqual(data['suggested_viewports'], [])


if __name__ == '__main__':
    unittest.main()
