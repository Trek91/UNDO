"""Build/verify a deterministic curated archive from current files, never Git HEAD."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'submission-manifest.json'
INDEX = 'SUBMISSION_CONTENTS.json'
FORBIDDEN = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.ruff_cache', '.mypy_cache',
             '.runtime', 'dist', 'data', 'test-results', 'playwright-report'}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_name(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or any(part in FORBIDDEN for part in path.parts):
        raise ValueError(f'Unsafe/excluded manifest path: {name}')
    if path.name == '.env' or '.db' in path.suffixes or path.suffix in {'.pyc', '.zip'}:
        raise ValueError(f'Local or generated artifact excluded: {name}')


def sources(root: Path) -> dict[str, bytes]:
    manifest = json.loads((root/MANIFEST).read_text(encoding='utf-8'))
    names = [row['path'] for row in manifest['files']]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate manifest entry')
    result = {}
    for name in sorted(names):
        validate_name(name)
        file = root/name
        if file.is_symlink() or not file.is_file() or root not in file.resolve().parents:
            raise ValueError(f'Missing or unsafe required file: {name}')
        data = file.read_bytes()
        if re.search(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}', data):
            raise ValueError(f'Potential credential in {name}; inspect before redistribution')
        result[name] = data
    for folder in ['backend/app', 'backend/tests', 'frontend/src', 'frontend/tests', 'frontend/e2e', 'frontend/public', 'deploy']:
        for file in (root/folder).rglob('*'):
            name = file.relative_to(root).as_posix()
            if file.is_file() and not any(part in FORBIDDEN for part in file.relative_to(root).parts) and name not in result:
                raise ValueError(f'Project file omitted from explicit manifest: {name}')
    return result


def verify(archive: Path) -> dict:
    with zipfile.ZipFile(archive) as zip_file:
        if zip_file.testzip() is not None:
            raise ValueError('Archive CRC failure')
        names = zip_file.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive entries')
        for name in names:
            validate_name(name)
        index = json.loads(zip_file.read(INDEX))
        manifest = json.loads(zip_file.read(MANIFEST))
        expected = {row['path'] for row in manifest['files']}
        if set(names) != expected | {INDEX} or set(index) != expected:
            raise ValueError('Archive, manifest and content index disagree')
        for name, record in index.items():
            data = zip_file.read(name)
            if len(data) != record['bytes'] or digest(data) != record['sha256']:
                raise ValueError(f'Content hash mismatch: {name}')
        return dict(status='PASS', archive=archive.name, sha256=digest(archive.read_bytes()), files=len(names),
                    content_hashes_verified=len(index), crc='PASS', exclusions='PASS')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'dist/UNDO-V3-SUBMISSION.zip')
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify), indent=2))
        return
    files = sources(ROOT)
    index = {name: dict(bytes=len(data), sha256=digest(data)) for name, data in files.items()}
    files[INDEX] = (json.dumps(index, indent=2)+'\n').encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 17, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    report = verify(args.output)
    args.output.with_suffix('.zip.sha256').write_text(report['sha256']+'  '+args.output.name+'\n', encoding='utf-8')
    args.output.with_suffix('.contents.txt').write_text('\n'.join(f'{name}\t{len(data)}\t{digest(data)}' for name, data in sorted(files.items()))+'\n', encoding='utf-8')
    args.output.with_suffix('.integrity.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
