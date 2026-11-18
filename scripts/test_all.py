"""Run the same complete test entrypoints locally and in CI, including script suites."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITES = ('test_contracts.py', 'test_merge_compatibility.py', 'test_workflow.py',
          'test_board.py', 'test_board_feedback.py', 'test_ecosystem.py',
          'test_site.py', 'test_web_quality.py', 'test_dsh_bundle.py')


def main():
    for name in SUITES:
        print('Running tests/' + name, flush=True)
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tests' / name)], cwd=ROOT)
        if result.returncode:
            return result.returncode
    print('PASS all 9 test entrypoints, including standalone contract suites')
    return 0


if __name__ == '__main__':
    sys.exit(main())
