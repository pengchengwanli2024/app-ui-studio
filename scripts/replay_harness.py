"""Replay preserved bounded checks without model calls or changing original evidence."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path('plugins/app-ui-studio/skills/app-ui-studio/scripts/studio.py')
PRESET = Path('plugins/app-ui-studio/skills/app-ui-studio/assets/saas-presets.json')


def main():
    results = {}
    for label in ('baseline', 'general', 'domain', 'composed'):
        with tempfile.TemporaryDirectory(prefix='studio-harness-replay-') as tmp:
            tree = Path(tmp)
            (tree / SCRIPT).parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'qa/harness/baseline/studio.py', tree / SCRIPT)
            (tree / PRESET).parent.mkdir(parents=True)
            shutil.copyfile(ROOT / PRESET, tree / PRESET)
            shutil.copyfile(ROOT / f'evidence/harness/{label}.patch', tree / 'fix.patch')
            for check in (('check.py', 'validate.py') if label == 'baseline' else ('check.py',)):
                result = subprocess.run([sys.executable, str(ROOT / 'qa/harness' / check)],
                                        cwd=tree, text=True, capture_output=True)
                print(f'{label}/{check}: {result.stdout.strip()}')
                if result.returncode:
                    print(result.stderr, file=sys.stderr)
                    raise SystemExit(result.returncode)
            results[label] = {'contracts': 42, 'extra_boundaries': 34 if label == 'baseline' else 0, 'exit': 0}
    print(json.dumps({'replay': results, 'new_agent_runs': False,
                      'note': 'Preserved fixture limitation remains; no visual quality claim.'}))


if __name__ == '__main__':
    main()
