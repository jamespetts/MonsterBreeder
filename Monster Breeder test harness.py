# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import re, subprocess, sys
html = Path('monster_breeder_objectified_architecture_20260702_snapshot_split.html').read_text(encoding='utf-8')
match = re.search(r'<script\s+id="simulationWorkerSource"[^>]*>(.*?)</script>', html, flags=re.S | re.I)
if not match:
    raise SystemExit('Could not find simulationWorkerSource script block.')
worker_path = Path('monster_breeder_extracted_worker_for_check.js')
worker_path.write_text(match.group(1), encoding='utf-8')
try:
    result = subprocess.run(['node', '--check', str(worker_path)], capture_output=True, text=True, timeout=10)
except FileNotFoundError:
    print('Node.js unavailable; extracted worker only.')
    sys.exit(0)
print(result.stdout)
print(result.stderr)
if result.returncode != 0:
    raise SystemExit(result.returncode)
print('Worker syntax check passed:', worker_path)
