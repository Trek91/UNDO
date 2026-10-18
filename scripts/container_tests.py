"""Run packaged tests with declared pure-Python tools; production pins remain in-image."""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
parser = argparse.ArgumentParser()
parser.add_argument('--image', required=True)
parser.add_argument('--platform', required=True, choices=['linux/amd64', 'linux/s390x'])
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
if not list((root/'.runtime/test-wheels').glob('*.whl')):
    raise SystemExit('Prepare .runtime/test-wheels as documented in docs/UNDO_V3_HANDOFF.md')
command = ['docker', 'run', '--rm', '--platform', args.platform, '--network', 'none', '--read-only', '--tmpfs', '/tmp',
    '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
    '--mount', f'type=bind,source={root / "backend/tests"},target=/app/backend/tests,readonly',
    '--mount', f'type=bind,source={root / "backend/pyproject.toml"},target=/app/backend/pyproject.toml,readonly',
    '--mount', f'type=bind,source={root / ".runtime/test-wheels"},target=/test-wheels,readonly',
    '-e', 'PYTHONPATH=/tmp/testdeps:/app/backend', '-e', 'PYTEST_ADDOPTS=-p no:cacheprovider',
    args.image, 'sh', '-c', 'python -m pip install --no-index --no-deps --find-links /test-wheels --target /tmp/testdeps '
    'pytest==9.1.1 httpx==0.28.1 httpcore==1.0.9 certifi==2026.7.22 pluggy==1.7.0 '
    'iniconfig==2.3.1 packaging==26.3 pygments==2.21.0 && python -m pytest -q']
raise SystemExit(subprocess.run(command).returncode)
