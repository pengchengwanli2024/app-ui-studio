"""Feedback must remain attached to exact screenshots across UI and CLI handoff."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fixtures import png

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'plugins/app-ui-studio/skills/app-ui-studio'
SCRIPT = SKILL / 'scripts/studio.py'


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'screen.png').write_bytes(png(2, 1))
        manifest = {'schema_version': 1, 'title': 'Review', 'context': {'state': 'initial'}, 'candidates': [
            {'id': key, 'label': key, 'screens': [{'id': 'mobile', 'artifact': 'screen.png',
                                                 'viewport': {'width': 2, 'height': 1}}]} for key in ('a', 'b')]}
        (self.root / 'input.json').write_text(json.dumps(manifest))
        self.invoke('board', str(self.root / 'input.json'), '--output', str(self.root / 'board'))
        self.board = json.loads((self.root / 'board/board.json').read_text())

    def invoke(self, *args, expected=0):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), *args], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))
        self.assertNotIn(b'Traceback', result.stderr)
        return json.loads(result.stdout)

    def feedback(self):
        screen = self.board['candidates'][0]['screens'][0]
        source = {'candidate_id': 'a', 'screen_id': 'mobile', 'artifact': screen['artifact'],
                  'sha256': screen['sha256'], 'viewport': copy.deepcopy(screen['viewport'])}
        return {'schema_version': 1, 'board_id': self.board['board_id'], 'selected_candidate': 'b',
                'selected_viewport': 'mobile', 'notes': [{**source, 'text': 'Keep the layout'}],
                'annotations': [{**source, 'id': 'note-1', 'point': {'x': .25, 'y': .75}, 'text': 'Check this heading'}]}

    def verify(self, feedback, expected=0):
        path = self.root / 'feedback.json'
        path.write_text(json.dumps(feedback))
        return self.invoke('board-feedback', str(self.root / 'board/board.json'), str(path), expected=expected)

    def test_feedback_can_review_a_different_candidate_from_selection(self):
        result = self.verify(self.feedback())
        self.assertTrue(result['feedback_contract_valid'])
        self.assertEqual(result['annotation_count'], 1)
        self.assertFalse(result['selection_applied'])
        self.assertFalse(result['visual_quality_verified'])

    def test_feedback_inputs_do_not_alias_board(self):
        data = self.feedback()
        data['annotations'][0]['viewport']['height'] = True
        self.assertIs(type(self.board['candidates'][0]['screens'][0]['viewport']['height']), int)

    def test_wrong_source_or_geometry_is_rejected(self):
        for mutate in (lambda d: d.update(board_id='0' * 64),
                       lambda d: d['annotations'][0].update(candidate_id='missing'),
                       lambda d: d['annotations'][0].update(sha256='0' * 64),
                       lambda d: d['annotations'][0]['viewport'].update(height=True),
                       lambda d: d['notes'][0].update(artifact='../screen.png'),
                       lambda d: d['annotations'][0]['point'].update(x=-.1),
                       lambda d: d['annotations'][0]['point'].update(y=True),
                       lambda d: d['annotations'].append(copy.deepcopy(d['annotations'][0]))):
            data = self.feedback()
            mutate(data)
            self.verify(data, expected=2)

    def test_changed_screenshot_invalidates_handoff(self):
        feedback = self.feedback()
        artifact = self.root / 'board' / feedback['annotations'][0]['artifact']
        artifact.write_bytes(png(3, 1))
        self.verify(feedback, expected=2)

    def test_real_qike_review_export_can_be_reproduced(self):
        output = self.root / 'qike-review'
        self.invoke('board', str(ROOT / 'examples/review-board.json'), '--output', str(output))
        result = self.invoke('board-feedback', str(output / 'board.json'), str(ROOT / 'evidence/v2.5.0/board-feedback.json'))
        self.assertEqual(result['annotation_count'], 2)
        self.assertEqual(result['screen_note_count'], 2)

    def test_browser_model_keeps_notes_scoped_and_restores_valid_drafts(self):
        model = SKILL / 'scripts/board_feedback.js'
        code = r'''
const assert = require('node:assert/strict');
const api = require(process.argv[1]);
const board = JSON.parse(process.argv[2]);
const a = api.sourceFor(board, 'a', 'mobile');
const b = api.sourceFor(board, 'b', 'mobile');
const state = api.createState(board);
api.writeNote(state, a, 'A only');
assert.equal(api.readNote(state, b), '');
api.writeNote(state, b, 'B only');
api.addAnnotation(state, a, {x: .2, y: .8}, 'Heading');
api.addAnnotation(state, a, {x: .8, y: .2}, 'Button');
state.selected_candidate = 'b';
const restored = api.restoreState(board, JSON.parse(JSON.stringify(api.exportFeedback(state))));
assert.equal(api.readNote(restored, a), 'A only');
assert.equal(api.readNote(restored, b), 'B only');
assert.equal(restored.annotations.length, 2);
assert.equal(restored.annotations[0].candidate_id, 'a');
assert.equal(api.exportFeedback(restored).selected_candidate, 'b');
const stale = api.exportFeedback(restored); stale.annotations[0].sha256 = '0'.repeat(64);
assert.throws(() => api.restoreState(board, stale));
assert.throws(() => api.addAnnotation(state, a, {x: NaN, y: .2}, 'Invalid'));
assert.throws(() => api.addAnnotation(state, a, {x: .2, y: .2}, '  '));
console.log('PASS scoped feedback and draft restore');
'''
        result = subprocess.run(['node', '-e', code, str(model), json.dumps(self.board)], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))


if __name__ == '__main__':
    unittest.main()
