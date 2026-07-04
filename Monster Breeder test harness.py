# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile


def FindHtmlPath():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    candidates = [
        Path('monster_breeder_fixes_20260703_2315.html'),
        Path('monster_breeder_round_season_pathfinding_20260703.html'),
        Path('index.html'),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def ExtractScripts(html):
    workerMatch = re.search(r'<script\s+id="simulationWorkerSource"[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    if not workerMatch:
        raise SystemExit('Could not find simulationWorkerSource script block')
    scripts = re.findall(r'<script([^>]*)>(.*?)</script>', html, flags=re.S | re.I)
    normalScripts = [content for attrs, content in scripts if 'simulationWorkerSource' not in attrs]
    if not normalScripts:
        raise SystemExit('Could not find main browser script block')
    return workerMatch.group(1), normalScripts[-1]


def RunNodeCheck(path):
    result = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True, timeout=15)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def RunWorkerRegression(workerPath):
    nodeSource = r'''
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync(process.argv[2], 'utf8');
const messages = [];
const context = { console, setInterval, clearInterval, Date, Math, Object, Array, Number, String, Boolean, JSON };
context.self = { postMessage: (message) => messages.push(message) };
context.globalThis = context;
vm.createContext(context);
vm.runInContext(code, context, { filename: 'simulationWorkerSource.js' });
messages.length = 0;
context.self.onmessage({ data: { protocolVersion: 1, messageId: 'regression', type: 'RUN_HEADLESS_TESTS', payload: { count: 3, seed: 100000, maxTicks: 700 } } });
const result = messages.find((message) => message.type === 'HEADLESS_TEST_RESULTS');
if (!result) {
    console.error(JSON.stringify(messages, null, 2));
    process.exit(2);
}
console.log(JSON.stringify({ regressionTests: result.payload.regressionTests, endedCount: result.payload.endedCount, timedOutCount: result.payload.timedOutCount }, null, 2));
if (!result.payload.regressionTests || !result.payload.regressionTests.passed) {
    process.exit(3);
}
'''
    runner = Path('monster_breeder_node_regression_runner_20260703_2327.js')
    runner.write_text(nodeSource, encoding='utf-8')
    result = subprocess.run(['node', str(runner), str(workerPath)], capture_output=True, text=True, timeout=60)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def StaticDomChecks(html):
    required = [
        'id="resumeGameMenuButton"',
        'function DrawTreasurePile',
        "kind:'droppedTreasure'",
        'function RunRegressionTests()',
        'class MicrofaunaEmitter',
        'getTreasureBreakdown(extraLooseTreasure)',
    ]
    missing = [text for text in required if text not in html]
    if missing:
        raise SystemExit('Static checks failed; missing: ' + ', '.join(missing))


def main():
    htmlPath = FindHtmlPath()
    html = htmlPath.read_text(encoding='utf-8')
    StaticDomChecks(html)
    workerSource, mainSource = ExtractScripts(html)
    workerPath = Path('monster_breeder_extracted_worker_regression_20260703_2327.js')
    mainPath = Path('monster_breeder_extracted_main_regression_20260703_2327.js')
    workerPath.write_text(workerSource, encoding='utf-8')
    mainPath.write_text(mainSource, encoding='utf-8')
    RunNodeCheck(workerPath)
    RunNodeCheck(mainPath)
    RunWorkerRegression(workerPath)
    print('All syntax and regression checks passed:', htmlPath)


if __name__ == '__main__':
    main()
