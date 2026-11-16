"""Offline capability discovery. Never imports or executes upstream projects."""
import json
from functools import lru_cache
from pathlib import Path
import re

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
DISPOSITIONS = ('adapted-method', 'maintenance-reference', 'optional-tool', 'reference-only', 'fork-reference')


def load_asset(name):
    data = json.loads((ASSETS / name).read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('Unsupported ecosystem schema')
    return data


@lru_cache(maxsize=1)
def capability_profiles():
    records = load_asset('design-capabilities.json').get('capabilities')
    if not isinstance(records, list) or not records:
        raise ValueError('Capability profiles must be a nonempty list')
    ids = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Invalid capability profile')
        key = record.get('id')
        if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', key) or key in ids:
            raise ValueError('Capability IDs must be unique safe slugs')
        ids.add(key)
        if not isinstance(record.get('label'), str) or not record['label'].strip():
            raise ValueError('Capability needs a label')
        tasks = ('brief', 'design', 'polish', 'extend', 'reconstruct', 'audit')
        if record.get('default_task') not in tasks:
            raise ValueError('Capability needs a valid default task')
        allowed = record.get('allowed_tasks', list(tasks))
        if (not isinstance(allowed, list) or not allowed or any(t not in tasks for t in allowed)
                or record['default_task'] not in allowed):
            raise ValueError('Capability task policy is invalid')
        for field in ('sources', 'steps', 'checks'):
            if (not isinstance(record.get(field), list) or not record[field]
                    or any(not isinstance(v, str) or not v.strip() for v in record[field])):
                raise ValueError('Capability needs nonempty text lists: ' + field)
        if 'audit_steps' in record and (not isinstance(record['audit_steps'], list)
                or any(not isinstance(v, str) or not v.strip() for v in record['audit_steps'])):
            raise ValueError('Audit steps must be a text list')
        reference = record.get('reference')
        if (not isinstance(reference, str) or not re.fullmatch(r'references/[a-z0-9-]+\.md', reference)
                or not (ASSETS.parent / reference).is_file()):
            raise ValueError('Capability reference must resolve inside the skill')
    return tuple(records)


def project_index():
    data = load_asset('oil-projects.json')
    records = data.get('projects')
    if not isinstance(records, list) or not records:
        raise ValueError('Project index must be a nonempty list')
    names = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Invalid project record')
        name = record.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name in names:
            raise ValueError('Project names must be unique repository names')
        names.add(name)
        if record.get('url') != 'https://github.com/oil-oil/' + name or type(record.get('fork')) is not bool:
            raise ValueError('Project owner or fork classification is invalid')
        if record.get('disposition') not in DISPOSITIONS:
            raise ValueError('Unknown project disposition')
        if record['fork'] and record['disposition'] != 'fork-reference':
            raise ValueError('Forks cannot be presented as adopted original sources')
        snapshot = record.get('snapshot')
        if snapshot is not None and (not isinstance(snapshot, dict) or not re.fullmatch(r'[0-9a-f]{40}', snapshot.get('commit', ''))):
            raise ValueError('Reviewed source requires an exact commit')
    actual = {'total': len(records), 'non_forks': sum(not p['fork'] for p in records),
              'forks': sum(p['fork'] for p in records),
              'reviewed_snapshots': sum(p.get('snapshot') is not None for p in records)}
    if data.get('coverage') != actual:
        raise ValueError('Project coverage does not match the inventory')
    return data


def run(args, emit):
    data = project_index()
    if args.kind == 'capabilities':
        if args.disposition:
            raise ValueError('--disposition applies only to projects')
        records = list(capability_profiles())
        if args.id:
            records = [p for p in records if p['id'] == args.id]
        else:
            records = [{k: p[k] for k in ('id', 'label', 'sources', 'reference', 'default_task')} for p in records]
    else:
        records = [p for p in data['projects'] if (not args.id or p['name'] == args.id)
                   and (not args.disposition or p['disposition'] == args.disposition)]
    if not records:
        raise ValueError('No matching ecosystem record')
    emit({'schema_version': 1, 'observed_at': data['observed_at'], 'coverage': data['coverage'],
          args.kind: records, 'network_executed': False, 'upstream_code_bundled': False,
          'upstream_execution_verified': False,
          'limits': ['Pinned discovery and independent workflow adaptations, not an upstream installer or executor.',
                     'Metadata review, source review and actual tool execution are separate.']})
    return 0


def register(commands, emit):
    parser = commands.add_parser('ecosystem', help='Discover reviewed Oil capabilities and project dispositions offline')
    parser.add_argument('--kind', choices=('capabilities', 'projects'), default='capabilities')
    parser.add_argument('--id')
    parser.add_argument('--disposition', choices=DISPOSITIONS)
    parser.set_defaults(run=lambda args: run(args, emit))
