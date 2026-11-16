"""Validate feedback against a generated board and the actual screenshot bytes."""
import hashlib
import math
from pathlib import Path
import re

from comparison_board import board_identity, identifier


def validate(board_path, feedback_path, strict_json, evidence_bytes, image_dimensions):
    path = Path(board_path).expanduser().resolve(strict=True)
    board = strict_json(path.read_bytes())
    feedback = strict_json(Path(feedback_path).expanduser().read_bytes())
    if (not isinstance(board, dict) or not isinstance(board.get('context'), dict)
            or not isinstance(board.get('candidates'), list) or not board['candidates']
            or board.get('board_id') != board_identity(board)):
        raise ValueError('Board identity is missing or changed; regenerate the board')
    sources, candidates, screen_ids = {}, set(), None
    for candidate in board['candidates']:
        if not isinstance(candidate, dict) or not isinstance(candidate.get('screens'), list):
            raise ValueError('Invalid board candidate')
        key = identifier(candidate.get('id'), 'candidate id')
        if key in candidates:
            raise ValueError('Duplicate board candidate')
        candidates.add(key)
        current_screens = set()
        for screen in candidate['screens']:
            if not isinstance(screen, dict):
                raise ValueError('Invalid board screenshot')
            screen_id = identifier(screen.get('id'), 'screen id')
            size = screen.get('viewport')
            if (not isinstance(size, dict) or any(type(size.get(axis)) is not int or size[axis] <= 0 for axis in ('width', 'height'))
                    or screen_id in current_screens):
                raise ValueError('Invalid board viewport')
            raw = evidence_bytes(path.parent, screen.get('artifact'))
            if hashlib.sha256(raw).hexdigest() != screen.get('sha256') or image_dimensions(raw) != (size['width'], size['height']):
                raise ValueError('Screenshot bytes no longer match the board')
            sources[key, screen_id] = {'candidate_id': key, 'screen_id': screen_id, 'artifact': screen['artifact'],
                                       'sha256': screen['sha256'], 'viewport': size}
            current_screens.add(screen_id)
        if not current_screens or (screen_ids is not None and screen_ids != current_screens):
            raise ValueError('Inconsistent board screen IDs')
        screen_ids = current_screens
    if (not isinstance(feedback, dict) or type(feedback.get('schema_version')) is not int or feedback['schema_version'] != 1
            or feedback.get('board_id') != board['board_id']):
        raise ValueError('Feedback belongs to a different board or schema')
    if feedback.get('selected_candidate') is not None and feedback['selected_candidate'] not in candidates:
        raise ValueError('Unknown selected candidate')
    if feedback.get('selected_viewport') not in screen_ids:
        raise ValueError('Unknown selected viewport')
    ids, note_sources = set(), set()
    for kind in ('notes', 'annotations'):
        entries = feedback.get(kind)
        if not isinstance(entries, list) or len(entries) > 1000:
            raise ValueError('Feedback entries must be a bounded list')
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError('Invalid feedback entry')
            source_key = (entry.get('candidate_id'), entry.get('screen_id'))
            if any(not isinstance(value, str) for value in source_key):
                raise ValueError('Invalid feedback source')
            size = entry.get('viewport')
            if not isinstance(size, dict) or any(type(size.get(axis)) is not int for axis in ('width', 'height')):
                raise ValueError('Feedback viewport must contain integer dimensions')
            expected = sources.get(source_key)
            if expected is None or any(entry.get(key) != value for key, value in expected.items()):
                raise ValueError('Feedback screenshot identity does not match')
            text = entry.get('text')
            if not isinstance(text, str) or not text.strip() or len(text) > 8000:
                raise ValueError('Feedback text must be nonblank and at most 8000 characters')
            if kind == 'notes':
                if source_key in note_sources:
                    raise ValueError('Duplicate screen note')
                note_sources.add(source_key)
            else:
                key, point = entry.get('id'), entry.get('point')
                if (not isinstance(key, str) or not re.fullmatch(r'note-[1-9][0-9]{0,15}', key) or key in ids
                        or int(key[5:]) >= 2**53 - 1):
                    raise ValueError('Annotation IDs must be unique')
                ids.add(key)
                if not isinstance(point, dict) or any(type(point.get(axis)) not in (int, float)
                        or not math.isfinite(point[axis]) or not 0 <= point[axis] <= 1 for axis in ('x', 'y')):
                    raise ValueError('Annotation position must be finite and normalized to 0..1')
    return {'schema_version': 1, 'board_id': board['board_id'], 'feedback_contract_valid': True,
            'annotation_count': len(feedback['annotations']), 'screen_note_count': len(feedback['notes']),
            'selection_applied': False, 'visual_quality_verified': False,
            'limits': ['Validated screenshot identity and feedback structure only; no project edits or quality verdict.']}


def register(commands, emit, strict_json, evidence_bytes, image_dimensions):
    parser = commands.add_parser('board-feedback', help='Validate exported feedback against exact screenshot bytes; read-only')
    parser.add_argument('board')
    parser.add_argument('feedback')
    def run(args):
        emit(validate(args.board, args.feedback, strict_json, evidence_bytes, image_dimensions))
        return 0
    parser.set_defaults(run=run)
