"""Portable site build and position-driven narrative invariants."""
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('src', 'href') and value:
                self.references.append(value)
            elif name == 'srcset' and value:
                self.references.extend(part.strip().split()[0] for part in value.split(','))


class SiteTests(unittest.TestCase):
    def test_build_is_portable_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'site'
            def run():
                return subprocess.run([sys.executable, str(ROOT / 'scripts/build_site.py'), '--output', str(output)], capture_output=True, timeout=30)
            result = run()
            self.assertEqual(result.returncode, 0, result.stdout.decode('utf-8', 'replace'))
            self.assertFalse(json.loads(result.stdout)['external_deployment'])
            page = (output / 'index.html').read_text(encoding='utf-8')
            self.assertNotIn('../plugins/', page)
            for path in ('assets/studio-paper.png', 'assets/review-workspace.jpg', 'assets/review-annotation.jpg', 'assets/review-annotation-mobile.jpg',
                         'assets/studio-ui.css', 'site.js', 'review/board.json', 'review/index.html'):
                self.assertTrue((output / path).is_file(), path)
            for html in output.rglob('*.html'):
                parser = LocalReferences()
                parser.feed(html.read_text(encoding='utf-8'))
                for reference in parser.references:
                    url = urlsplit(reference)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    target = (html.parent / unquote(url.path)).resolve()
                    self.assertTrue(target.is_relative_to(output.resolve()), reference)
                    self.assertTrue(target.is_file(), reference)
            marker = output / 'preserve'
            marker.write_text('existing user output')
            self.assertEqual(run().returncode, 2)
            self.assertEqual(marker.read_text(), 'existing user output')

    def test_story_position_is_reversible_and_clamped(self):
        code = r'''
const assert = require('node:assert/strict');
const {phaseAt} = require(process.argv[1]);
const steps = [{top: 0, bottom: 600}, {top: 600, bottom: 1200}, {top: 1200, bottom: 1800}];
const at = offset => phaseAt(steps.map(s => ({top:s.top-offset,bottom:s.bottom-offset})), 900);
assert.equal(at(0).index, 0);
assert.equal(at(700).index, 1);
assert.equal(at(1400).index, 2);
assert.equal(at(700).index, 1);
assert.equal(at(0).index, 0);
assert.equal(at(-1000).progress, 0);
assert.equal(at(4000).progress, 1);
assert.throws(() => phaseAt([], 900));
assert.throws(() => phaseAt(steps, 0));
'''
        result = subprocess.run(['node', '-e', code, str(ROOT / 'site/site.js')], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', 'replace'))


if __name__ == '__main__':
    unittest.main()
