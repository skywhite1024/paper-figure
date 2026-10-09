"""Package the checked paper-scoped output layout; never regenerate a flat release.

Archives are optional local delivery files, ignored by Git. No ZIP is uploaded
by this script. Existing output files are the canonical package input.
"""
import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from paper_figure.outputs import refresh_output
from paper_figure.model import require, ValidationError


def create_packages(repository, output, destination):
    repository, output, destination = map(lambda p: Path(p).resolve(), (repository, output, destination))
    require(not destination.is_relative_to(output), 'Archive destination cannot be inside output/')
    refresh_output(repository, output)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = sorted(p for p in output.rglob('*') if p.is_file())
    # Use Git's tracked source list rather than accidentally including secrets or
    # temporary directories from an unrestricted filesystem walk.
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=repository).decode().split('\0')
    sources = []
    for name in filter(None, tracked):
        relative = Path(name)
        path = repository / relative
        if relative.parts[0] == 'output' or path.is_relative_to(destination):
            continue
        if any(part in {'build', '.git', '__pycache__', 'node_modules', '.venv', 'dist'}
               or part.endswith('.egg-info') for part in relative.parts):
            continue
        if path.suffix.lower() in {'.zip', '.bundle', '.pdf', '.deb', '.rpm'}:
            continue
        if path.is_file():
            sources.append(path)
    result = []
    for kind in ['samples', 'source', 'complete']:
        target = destination / f'paper-figure-v0.2-{kind}.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            if kind != 'source':
                for path in outputs:
                    relative = path.relative_to(output)
                    archive.write(path, (Path('output') / relative) if kind == 'complete' else relative)
            if kind != 'samples':
                for path in sources:
                    relative = path.relative_to(repository)
                    archive.write(path, relative if kind == 'complete' else Path('source') / relative)
        result.append((str(target), target.stat().st_size, hashlib.sha256(target.read_bytes()).hexdigest()))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'output')
    parser.add_argument('--out', type=Path, default=ROOT / 'build/releases')
    args = parser.parse_args()
    try:
        for path, size, digest in create_packages(ROOT, args.input, args.out):
            print(path, size, digest)
    except (OSError, ValidationError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f'error: {exc}\n')

if __name__ == '__main__':
    main()
