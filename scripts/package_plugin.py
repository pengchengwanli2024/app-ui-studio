"""Build the contained portable plugin archive; no install or external writes."""
import argparse
import json
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / 'plugins' / 'app-ui-studio'
    output = Path(args.output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise SystemExit('Refusing to overwrite existing archive')
    if output.resolve().is_relative_to(source.resolve()):
        raise SystemExit('Archive must stay outside plugin source')
    if not output.parent.is_dir():
        raise SystemExit('Output parent must exist')
    manifest = json.loads((source / 'plugin.json').read_text())
    entries = sorted(source.rglob('*'))
    files = [p for p in entries if p.is_file() and '__pycache__' not in p.parts
             and not p.name.endswith('.pyc') and p.name != '.DS_Store']
    if any(p.is_symlink() for p in entries):
        raise SystemExit('Plugin source contains symlinks; inspect before packaging')
    with output.open('xb') as stream, zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, str(Path(manifest['name']) / path.relative_to(source)))
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(files):
            raise SystemExit('Archive validation failed')
    print(json.dumps({'archive': str(output), 'version': manifest['version'], 'files': len(files)}))


if __name__ == '__main__':
    main()
