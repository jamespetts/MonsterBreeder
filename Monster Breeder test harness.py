# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import re
import subprocess
import sys

# Default to the generated review build when present, otherwise fall back to index.html.
# A specific HTML file may also be supplied as the first command-line argument.
def FindHtmlPath():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    candidates = [
        Path('monster_breeder_round_season_pathfinding_20260703.html'),
        Path('index.html'),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]

html_path = FindHtmlPath()
html = html_path.read_text(encoding='utf-8')
match = re.search(r'<script\s+id="simulationWorkerSource"[^>]*>(.*?)</script>', html, flags=re.S | re.I)
if not match:
    raise SystemExit('Could not find simulationWorkerSource script block in ' + str(html_path))
worker_path = Path('monster_breeder_extracted_worker_for_check.js')
worker_path.write_text(match.group(1), encoding='utf-8')
try:
    result = subprocess.run(['node', '--check', str(worker_path)], capture_output=True, text=True, timeout=10)
except FileNotFoundError:
    print('Node.js unavailable; extracted worker only:', worker_path)
    sys.exit(0)
print(result.stdout)
print(result.stderr)
if result.returncode != 0:
    raise SystemExit(result.returncode)
print('Worker syntax check passed:', worker_path)
