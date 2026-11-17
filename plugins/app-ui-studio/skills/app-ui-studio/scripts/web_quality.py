"""Summarize local Lighthouse results without launching a browser or certifying UX."""
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


METRICS = ('first-contentful-paint', 'largest-contentful-paint', 'cumulative-layout-shift',
           'total-blocking-time', 'speed-index', 'interaction-to-next-paint')
CONDITIONS = ('formFactor', 'screenEmulation', 'throttlingMethod', 'throttling',
              'locale', 'disableStorageReset', 'emulatedUserAgent')


def number(value, label, maximum=None):
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (maximum is not None and value > maximum):
        raise ValueError('Invalid ' + label)
    return value


def load_report(path, strict_json):
    source = Path(path).expanduser()
    if source.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('Lighthouse JSON exceeds 32 MiB; export a single LHR without large assets')
    raw = source.read_bytes()
    data = strict_json(raw)
    if not isinstance(data, dict) or not isinstance(data.get('audits'), dict) or not data['audits']:
        raise ValueError('Expected one Lighthouse result (LHR), not a flow container or a Studio summary')
    if not isinstance(data.get('lighthouseVersion'), str) or not data['lighthouseVersion'].strip():
        raise ValueError('Missing Lighthouse version')
    if not isinstance(data.get('categories'), dict) or not isinstance(data.get('configSettings'), dict):
        raise ValueError('Missing Lighthouse categories or configuration')
    url = data.get('finalDisplayedUrl') or data.get('finalUrl') or data.get('requestedUrl')
    if not isinstance(url, str):
        raise ValueError('Missing audited URL')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Expected an HTTP(S) audited URL without embedded credentials')
    # Query/fragment values and report DOM details are deliberately not exported.
    public_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
    categories, membership = {}, {}
    for key, category in data['categories'].items():
        if not isinstance(category, dict):
            raise ValueError('Invalid Lighthouse category')
        score = number(category.get('score'), 'category score', 1)
        categories[key] = {'score': score, 'status': 'unscored' if score is None else 'scored'}
        refs = category.get('auditRefs', [])
        if not isinstance(refs, list):
            raise ValueError('Invalid category audit references')
        for ref in refs:
            if not isinstance(ref, dict) or ref.get('id') not in data['audits']:
                raise ValueError('Category references an unavailable audit')
            membership.setdefault(ref['id'], []).append(key)
    findings, metrics, audit_errors = [], {}, []
    for key, audit in data['audits'].items():
        if not isinstance(audit, dict):
            raise ValueError('Invalid Lighthouse audit')
        score = number(audit.get('score'), 'audit score', 1)
        mode = audit.get('scoreDisplayMode', 'unknown')
        if not isinstance(mode, str):
            raise ValueError('Invalid audit score display mode')
        if mode == 'error':
            audit_errors.append(key)
        if key in METRICS:
            value = number(audit.get('numericValue'), 'metric value')
            metrics[key] = {'value': value, 'unit': audit.get('numericUnit'),
                            'status': 'unavailable' if value is None else 'reported'}
        if score is not None and score < 1 and mode not in ('manual', 'informative', 'notApplicable', 'error'):
            findings.append({'audit_id': key, 'title': audit.get('title', key), 'score': score,
                             'mode': mode, 'categories': membership.get(key, []),
                             'display_value': audit.get('displayValue')})
    for key in METRICS:
        metrics.setdefault(key, {'value': None, 'unit': None, 'status': 'unavailable'})
    runtime = data.get('runtimeError')
    if runtime is not None and not isinstance(runtime, dict):
        raise ValueError('Invalid Lighthouse runtime error')
    settings = data['configSettings']
    warnings = data.get('runWarnings') or []
    if not isinstance(warnings, list):
        raise ValueError('Invalid Lighthouse warnings')
    environment = data.get('environment') or {}
    if not isinstance(environment, dict):
        raise ValueError('Invalid Lighthouse environment')
    context = {key: settings.get(key) for key in CONDITIONS}
    context.update(url=public_url, lighthouse_version=data['lighthouseVersion'],
                   gather_mode=data.get('gatherMode', 'unknown'),
                   host_user_agent=environment.get('hostUserAgent'),
                   categories=sorted(categories),
                   audit_scope={'only': settings.get('onlyAudits'), 'skip': settings.get('skipAudits')},
                   audit_weights_sha256=hashlib.sha256(json.dumps({key: value.get('auditRefs', []) for key, value in data['categories'].items()}, sort_keys=True).encode()).hexdigest())
    # The full URL participates privately in comparison: stripping query values
    # from the public summary must not make different application states match.
    identity = {**context, 'url': url}
    result = {'schema_version': 1, 'report_contract_valid': True,
              'source_sha256': hashlib.sha256(raw).hexdigest(),
              'context': context, 'fetch_time': data.get('fetchTime'),
              'runtime_error': None if runtime is None else {'code': runtime.get('code', 'UNKNOWN')},
              'audit_errors': audit_errors, 'warning_count': len(warnings),
              'categories': categories, 'metrics': metrics, 'findings': findings,
              'lighthouse_executed': False, 'ui_quality_verified': False,
              'field_core_web_vitals_verified': False,
              'limits': ['Imported local report data, not proof that this command ran Lighthouse.',
                         'A lab score is not field INP, visual quality, a complete user flow or WCAG certification.',
                         'Unscored, manual, unavailable and zero remain distinct. Raw report details stay in the source file.']}
    return result, identity


def compare(current, baseline, current_identity, baseline_identity):
    differences = []
    if current_identity['gather_mode'] == 'unknown' or baseline_identity['gather_mode'] == 'unknown':
        differences.append('unknown gather mode')
    for key in current_identity:
        if current_identity[key] is None or baseline_identity.get(key) is None:
            differences.append('unknown condition: ' + key)
        elif current_identity[key] != baseline_identity[key]:
            differences.append('changed condition: ' + key)
    if current['runtime_error'] or baseline['runtime_error'] or current['audit_errors'] or baseline['audit_errors']:
        differences.append('runtime or audit error')
    result = {'conditions_match': not differences, 'differences': differences,
              'baseline_sha256': baseline['source_sha256'], 'same_user_state_verified': False,
              'score_deltas': {}, 'metric_deltas': {},
              'note': 'Deltas describe these reports only; verify matching fixtures/states and repeat serial runs before attributing improvement.'}
    if not differences:
        for key, category in current['categories'].items():
            left, right = baseline['categories'][key]['score'], category['score']
            if left is not None and right is not None:
                result['score_deltas'][key] = round(right - left, 6)
        for key, metric in current['metrics'].items():
            old = baseline['metrics'][key]
            if metric['value'] is not None and old['value'] is not None and metric['unit'] == old['unit']:
                result['metric_deltas'][key] = {'value': round(metric['value'] - old['value'], 6), 'unit': metric['unit']}
    return result


def run(args, emit, strict_json):
    try:
        result, identity = load_report(args.report, strict_json)
        if args.baseline:
            baseline, old_identity = load_report(args.baseline, strict_json)
            result['comparison'] = compare(result, baseline, identity, old_identity)
        if args.output:
            import json
            destination = Path(args.output).expanduser()
            if destination.is_symlink():
                raise ValueError('Refusing an output symlink')
            with destination.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        emit(result)
        return 1 if result['runtime_error'] or result['audit_errors'] or not result.get('comparison', {}).get('conditions_match', True) else 0
    except (OSError, ValueError, TypeError, RecursionError) as error:
        emit({'report_contract_valid': False, 'lighthouse_executed': False,
              'ui_quality_verified': False, 'errors': [str(error)]})
        return 2


def register(commands, emit, strict_json):
    parser = commands.add_parser('web-report', help='Read local Lighthouse JSON; no browser, network or project edits')
    parser.add_argument('report')
    parser.add_argument('--baseline')
    parser.add_argument('--output', help='Exclusively create a new summary; parent must exist')
    parser.set_defaults(run=lambda args: run(args, emit, strict_json))
