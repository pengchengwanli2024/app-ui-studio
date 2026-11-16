"""Build the local product site and its real review workspace into a new directory."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def build(destination):
    root = Path(__file__).resolve().parents[1]
    source = root / 'site'
    skill = root / 'plugins/app-ui-studio/skills/app-ui-studio'
    output = Path(destination).expanduser().absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError('Output must be a new directory with an existing parent')
    if output.resolve().is_relative_to(source.resolve()):
        raise ValueError('Output must stay outside site source')
    files = [p for p in source.rglob('*') if p.is_file()]
    if any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('Inspect source symlinks before building')
    output.mkdir()
    try:
        for path in files:
            relative = path.relative_to(source)
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative.as_posix() == 'index.html':
                text = path.read_text(encoding='utf-8').replace('../plugins/app-ui-studio/skills/app-ui-studio/assets/studio-ui.css', 'assets/studio-ui.css').replace('../plugins/app-ui-studio/assets/icon.svg', 'assets/icon.svg')
                target.write_text(text, encoding='utf-8')
            else:
                shutil.copyfile(path, target)
        shutil.copyfile(skill / 'assets/studio-ui.css', output / 'assets/studio-ui.css')
        shutil.copyfile(root / 'plugins/app-ui-studio/assets/icon.svg', output / 'assets/icon.svg')
        result = subprocess.run([sys.executable, '-B', str(skill / 'scripts/studio.py'), 'board',
                                 str(root / 'examples/review-board.json'), '--output', str(output / 'review')],
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        if result.returncode:
            raise ValueError('Review workspace build failed: ' + result.stdout.strip())
        return {'output': str(output), 'review_workspace': True, 'external_deployment': False,
                'media_generation_executed': False, 'note': 'Existing material and real screenshot inputs were packaged; no quality verdict.'}
    except Exception:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output), ensure_ascii=True))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    sys.exit(main())
