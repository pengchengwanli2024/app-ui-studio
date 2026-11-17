"""Local report contracts: honest missing data, comparison guards and safe output."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'plugins/app-ui-studio/skills/app-ui-studio/scripts/studio.py'


def report(mode='navigation'):
    return {'lighthouseVersion': '13.6.0', 'gatherMode': mode,
            'finalUrl': 'https://example.test/page?session=private-value',
            'environment': {'hostUserAgent': 'HeadlessChrome/test'},
            'configSettings': {'formFactor': 'mobile', 'screenEmulation': {'width': 412},
                               'throttlingMethod': 'simulate', 'throttling': {'cpuSlowdownMultiplier': 4},
                               'locale': 'en-US', 'disableStorageReset': False, 'emulatedUserAgent': 'mobile/test'},
            'categories': {'performance': {'score': .8, 'auditRefs': [{'id': 'largest-contentful-paint', 'weight': 1}]},
                           'accessibility': {'score': 0, 'auditRefs': [{'id': 'label', 'weight': 1}]}},
            'audits': {'largest-contentful-paint': {'score': .5, 'scoreDisplayMode': 'numeric',
                                                   'numericValue': 3000, 'numericUnit': 'millisecond'},
                       'cumulative-layout-shift': {'score': 1, 'scoreDisplayMode': 'numeric', 'numericValue': 0, 'numericUnit': 'unitless'},
                       'label': {'score': 0, 'scoreDisplayMode': 'binary'},
                       'manual': {'score': None, 'scoreDisplayMode': 'manual'}}}


class WebQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def invoke(self, path, *args, expected=0):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), 'web-report', str(path), *map(str, args)], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))
        self.assertNotIn(b'Traceback', result.stderr)
        return json.loads(result.stdout)

    def test_real_zero_missing_manual_and_execution_remain_distinct(self):
        path = self.write('report.json', report())
        before = path.read_bytes()
        data = self.invoke(path)
        self.assertEqual(data['categories']['accessibility']['score'], 0)
        self.assertEqual(data['metrics']['cumulative-layout-shift']['value'], 0)
        self.assertEqual(data['metrics']['interaction-to-next-paint']['status'], 'unavailable')
        self.assertIsNone(data['metrics']['interaction-to-next-paint']['value'])
        self.assertNotIn('manual', [item['audit_id'] for item in data['findings']])
        for key in ('lighthouse_executed', 'ui_quality_verified', 'field_core_web_vitals_verified'):
            self.assertFalse(data[key])
        self.assertNotIn('private-value', json.dumps(data))
        self.assertEqual(path.read_bytes(), before)

    def test_snapshot_and_timespan_do_not_invent_navigation_scores(self):
        for mode in ('snapshot', 'timespan'):
            sample = report(mode)
            sample['categories']['performance']['score'] = None
            sample['audits']['largest-contentful-paint'].update(score=None, numericValue=None, scoreDisplayMode='notApplicable')
            data = self.invoke(self.write(mode+'.json', sample))
            self.assertEqual(data['categories']['performance']['status'], 'unscored')
            self.assertEqual(data['metrics']['largest-contentful-paint']['status'], 'unavailable')

    def test_matching_reports_have_deltas_without_quality_verdict(self):
        old = self.write('old.json', report())
        current = report()
        current['categories']['performance']['score'] = .9
        current['audits']['largest-contentful-paint']['numericValue'] = 2000
        data = self.invoke(self.write('new.json', current), '--baseline', old)
        self.assertTrue(data['comparison']['conditions_match'])
        self.assertEqual(data['comparison']['score_deltas']['performance'], .1)
        self.assertEqual(data['comparison']['metric_deltas']['largest-contentful-paint']['value'], -1000)
        self.assertFalse(data['comparison']['same_user_state_verified'])

    def test_version_browser_scope_mode_and_state_mismatches_block_deltas(self):
        baseline = self.write('baseline.json', report())
        changes = [lambda d: d.update(lighthouseVersion='14.0.0'),
                   lambda d: d['environment'].update(hostUserAgent='different/browser'),
                   lambda d: d['configSettings'].update(formFactor='desktop'),
                   lambda d: d['configSettings'].update(onlyAudits=['label']),
                   lambda d: d['categories']['performance']['auditRefs'][0].update(weight=2),
                   lambda d: d.update(gatherMode='snapshot'),
                   lambda d: d.update(finalUrl='https://example.test/page?session=another-private-value'),
                   lambda d: d['configSettings'].pop('throttlingMethod')]
        for change in changes:
            sample = report()
            change(sample)
            data = self.invoke(self.write('changed.json', sample), '--baseline', baseline, expected=1)
            self.assertFalse(data['comparison']['conditions_match'])
            self.assertEqual(data['comparison']['score_deltas'], {})
            self.assertEqual(data['comparison']['metric_deltas'], {})

    def test_runtime_and_audit_errors_never_look_successful(self):
        for runtime in (True, False):
            sample = report()
            if runtime:
                sample['runtimeError'] = {'code': 'NO_FCP', 'message': 'private detail'}
            else:
                sample['audits']['label'].update(score=None, scoreDisplayMode='error')
            data = self.invoke(self.write('failed.json', sample), expected=1)
            self.assertTrue(data['runtime_error'] or data['audit_errors'])
            self.assertNotIn('private detail', json.dumps(data))

    def test_malformed_json_and_invalid_values_are_rejected(self):
        for change in (lambda d: d['categories']['performance'].update(score=True),
                       lambda d: d['categories']['performance'].update(score=1.5),
                       lambda d: d['audits']['label'].update(score=-1),
                       lambda d: d['audits']['largest-contentful-paint'].update(numericValue=True),
                       lambda d: d.update(finalUrl='file:///private/input'),
                       lambda d: d.update(finalUrl='https://user:password@example.test/'),
                       lambda d: d.update(audits=[]),
                       lambda d: d['categories']['performance']['auditRefs'][0].update(id='missing')):
            sample = report()
            change(sample)
            self.assertFalse(self.invoke(self.write('bad.json', sample), expected=2)['report_contract_valid'])
        for text in ('{"audits":{},"audits":{}}', '{"value":NaN}', '{}', '[]'):
            path = self.root/'malformed.json'
            path.write_text(text)
            self.assertFalse(self.invoke(path, expected=2)['report_contract_valid'])

    def test_output_is_exclusive_and_never_overwrites_input(self):
        source = self.write('input.json', report())
        before = source.read_bytes()
        self.invoke(source, '--output', source, expected=2)
        self.assertEqual(source.read_bytes(), before)
        target = self.root/'summary.json'
        self.invoke(source, '--output', target)
        first = target.read_bytes()
        self.invoke(source, '--output', target, expected=2)
        self.assertEqual(target.read_bytes(), first)


if __name__ == '__main__':
    unittest.main()
